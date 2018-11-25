#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='cophub',
      version='0.0.1',
      description=('Copernicus Australasia Data Hub coverage '
                   'maps and reporting.'),
      packages=find_packages(),
      install_requires=[
          'pathlib',
          'matplotlib',
          'click',
          'fiona',
          'geopandas',
          'shapely'
      ],
      dependency_links=[
          'hg+https://bitbucket.org/chchrsc/auscophub/get/auscophub-1.1.7.tar.gz#egg=auscophub-1.1.7'
      ],
      scripts=['bin/cophub_maps', 'bin/cophub_info', 'bin/cophub_overlaps']
      )
