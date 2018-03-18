# coding: utf-8

"""
Setup.py of geohashlite
"""

from setuptools import setup, Extension

# requiring C++ here for Windows support.
c1 = Extension('_geohash',
               sources=['src/geohash.cpp', ],
               define_macros=[('PYTHON_MODULE', 1), ])

setup(
    name="geohashlite",
    version="0.3.1",
    author="Xuzhou Qin",
    author_email="me@qinxuzhou.com",
    packages=["geohashlite"],
    license="LICENSE",
    description="A python library for interacting with geohash",
    long_description=open('README.md').read(),
    install_requires=[
        'shapely',
    ],
    ext_modules=[c1],
)
