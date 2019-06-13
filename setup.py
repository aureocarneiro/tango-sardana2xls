#!/usr/bin/env python

from setuptools import setup

setup(name = "sardana2xls",
      version = "1.0.0",
      description = ("Tool to generate a xls representation of an existing Tango Sardana environment"),
      author = "KITS Group",
      author_mail = "kits@maxiv.lu.se",
      license = "GPLv3",
      url = "http://www.maxlab.lu.se",
      packages =["sardana2xls"],
      entry_points={
          "console_scripts": ["sardana2xls = sardana2xls.sardana2xls:main"]},
      install_requires=["setuptools", "pytango", "xlrd"],
      )
