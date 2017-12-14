# coding: utf-8

from setuptools import setup

setup(
    name="geohashlite",
    version="0.1",
    author="Xuzhou Qin",
    author_email="me@qinxuzhou.com",
    packages=["geohashlite"],
    license="LICENSE",
    description="A python library for interacting with geohash",
    long_description=open('README.md').read(),
    install_requires=[
        'shapely',
    ],
)