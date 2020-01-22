#!/usr/bin/env python

from setuptools import setup
from indi_admin import __version__


requirements = open('requirements.txt').read().split()


setup(
    name='indi-admin',
    version=__version__,
    description='Another web application to manage an INDI server',
    author='Juan Menendez',
    author_email='juanmb@gmail.com',
    url='http://www.github.com/juanmb/indi-admin/',
    packages=['indi_admin'],
    include_package_data=True,
    install_requires=requirements,
    license="LGPL",
    zip_safe=False,
    entry_points={
        "console_scripts": ["indi-admin=indi_admin.main:main"]
    },
    classifiers=[
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Operating System :: OS Independent',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Astronomy',
    ],
)
