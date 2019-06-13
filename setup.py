#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name = "sardana2xls",
      version = "1.0.0",
      description = ("Tool to generate a xls representation of an existing Tango Sardana environment"),
      author = "KITS - Controls",
      author_mail = "kits@maxiv.lu.se",
      license = "GPLv3",
      url = "http://www.maxlab.lu.se",
      packages = find_packages(),
      include_package_data=True,
      package_data={'': ['*.xls']},
      entry_points={
          "console_scripts": ["sardana2xls = sardana2xls.sardana2xls:main"]},
      install_requires=["setuptools", "pytango", "xlrd"],
      )
