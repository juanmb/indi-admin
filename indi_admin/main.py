import os
from flask import Flask, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib import sqla

from indiweb.driver import DriverCollection, INDI_DATA_DIR
from indiweb.indi_server import IndiServer, INDI_PORT, INDI_FIFO, INDI_CONFIG_DIR


INDI_CONFIG_DIR = os.path.join(os.environ['HOME'], '.indi')

db_path = "sqlite:///{:s}/indiadmin.db".format(INDI_CONFIG_DIR)

if not os.path.exists(INDI_CONFIG_DIR):
    os.mkdir(INDI_CONFIG_DIR)

# Create application
app = Flask(__name__)

# Create dummy secrey key so we can use sessions
app.config['SECRET_KEY'] = '123456790'

app.config['SQLALCHEMY_DATABASE_URI'] = db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False

db = SQLAlchemy(app)


# Flask views
@app.route('/')
def index():
    return redirect('/admin/')


class LocalDrivers(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50))
    label = db.Column(db.String(50))
    group = db.Column(db.String(50))
    version = db.Column(db.String(8))
    binary = db.Column(db.String(64), unique=True)
    skeleton = db.Column(db.String(50))

    def __str__(self):
        return self.name


class Profiles(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    port = db.Column(db.Integer, default=INDI_PORT)
    active = db.Column(db.Boolean)
    local_drivers = db.relationship('LocalDrivers', secondary="profiles_local_drivers",
                                    backref=db.backref('profiles', lazy='dynamic'))

    def __str__(self):
        return self.name

class Hosts(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), unique=True)
    address = db.Column(db.String(50))
    port = db.Column(db.Integer, default=INDI_PORT)
    remote_drivers = db.relationship('RemoteDrivers', cascade='delete')

    def __str__(self):
        return self.name


class RemoteDrivers(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50))

    host_id = db.Column(db.Integer, db.ForeignKey('hosts.id'), nullable=False)
    #host = db.relationship('Hosts', foreign_keys=host_id, backref='remote_drivers')
    host = db.relationship('Hosts', foreign_keys=host_id)

    # TODO: unique constraint: name, host_id

    def __str__(self):
        return self.name


class ProfilesLocalDrivers(db.Model):
    __tablename__="profiles_local_drivers"
    id = db.Column(db.Integer(), primary_key=True)
    profile_id = db.Column(db.Integer(), db.ForeignKey('profiles.id', ondelete='CASCADE'))
    local_driver_id = db.Column(db.Integer(), db.ForeignKey('local_drivers.id', ondelete='CASCADE'))


class LocalDriversView(sqla.ModelView):
    # TODO: add "scan" button
    default_sort = 'name'
    column_searchable_list = ['name']
    form_columns = ['name', 'label', 'group', 'version', 'binary']
    column_exclude_list = ['label', 'skeleton']
    can_view_details = True
    can_delete = False
    can_create = False
    can_edit = False


class ProfilesView(sqla.ModelView):
    default_sort = 'name'
    form_columns = ['name', 'port', 'active', 'local_drivers']


class RemoteDriversView(sqla.ModelView):
    pass


class HostsView(sqla.ModelView):
    form_columns = ['name', 'address', 'port']


def main():
    # Create admin
    admin = Admin(app, name='INDI Web Admin',
                        template_mode='bootstrap3')
    admin.add_view(ProfilesView(Profiles, db.session))
    admin.add_view(LocalDriversView(LocalDrivers, db.session))
    admin.add_view(RemoteDriversView(RemoteDrivers, db.session))
    admin.add_view(HostsView(Hosts, db.session))

    # Create DB
    db.create_all()

    collection = DriverCollection(INDI_DATA_DIR)
    #collection = DriverCollection('drivers')
    #indi_server = IndiServer(args.fifo, args.conf)
    for drv in collection.drivers:
        query = db.session.query(LocalDrivers).filter_by(binary=drv.binary)

        # insert or update
        if query.count():
            query.update(
                {'name': drv.name, 'label': drv.label, 'group': drv.family,
                 'version': drv.version, 'skeleton': drv.skeleton})
        else:
            row = LocalDrivers(name=drv.name, label=drv.label,
                               group=drv.family, binary=drv.binary,
                               version=drv.version, skeleton=drv.skeleton)
            db.session.add(row)

    db.session.commit()

    # Start app
    app.run(debug=True)


if __name__ == '__main__':
    main()
