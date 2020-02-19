# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
packages = find_packages()
desc ="""Commissioning tools for accelerators

This tool consists of a library which provides:
    * :mod:`ophyd`: device drivers for BESSY II
    * :mod:`bluesky`:

See https://github.com/XXX
"""

setup(
    full_name = "Berlin accelerator commissioning tools",
    name = "bact2",
    version = "0.0.0",
    author = "Pierre Schnizer, Tom Mertens, Andreas Schälicke",
    author_email= "pierre.schnizer@helmholtz-berlin.de tom.mertens@helmholtz-berlin.de markus.ries@helmholz-berlin.de andreas.schaelicke@helmholtz-berlin.de",
    description = desc,
    license = "GPL",
    keywords = ",EPICS",
    url="https://github.com/TMsangohan/bact2/",
    packages = packages,
    classifiers = [
        "Development Status :: 2 - Pre - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Physics",
    ]
)
