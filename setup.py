#!/usr/bin/env python


try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

f = open('README.rst')
long_description = f.read().strip()
f.close()

setup(
    name='twabulous',
    version='9000.4a',
    description="Twitter + Fabulous = Twabulous",
    long_description=long_description,
    author='Ralph Bean & Remy DeCausemaker',
    author_email='ralph.bean@gmail.com',
    url='http://github.com/ralphbean/twabulous/',
    license='AGPLv3',
    install_requires=[
        "fabulous",
        "simplejson",
        "pycurl",
        "PIL",
    ],
    packages=['twabulous'],
    include_package_data=True,
    zip_safe=False,
    entry_points="""
    [console_scripts]
    twabulous = twabulous.twabulous:main
    """
)
