#!/usr/bin/env python
from distutils.core import setup
from distutils.command.install import INSTALL_SCHEMES
import platform

for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']

system = platform.system()

reqs = ['cachetools','pydicom','textx','cython','matplotlib','kivy','pycontracts','docutils','pygame']

if system != 'Linux':
    reqs = ['cachetools','pydicom','textx','cython','matplotlib','kivy','pycontracts','docutils','pygame',
    'kivy.deps.angle','kivy.deps.gstreamer','kivy.deps.sdl2','kivy.deps.glew']

setup(
  include_data_files = True,
  name = 'perceptionmd',
  version = '0.1.2',
  description = 'Human observer tests for radiology',
  author = 'David Volgyes',
  author_email = 'david.volgyes@ieee.org',
  url = 'https://github.com/dvolgyes/perceptionmd',
  packages = ['perceptionmd','perceptionmd/CTTools'], 
  scripts=['PerceptionMD.py',],
  data_files = [('perceptionmd', ['LICENSE.txt','perceptionmd/perception.tx']), 
                ('perceptionmd/widgets', ['perceptionmd/widgets/infoscreen.kv']), 
                ('perceptionmd/unittests/',['perceptionmd/unittests/travis-example.md'])],
  keywords = ['testing', 'example'],
  classifiers = [],
  license = 'AGPL3',
  install_requires=reqs,
#  download_url = 'https://github.com/dvolgyes/perceptionmd/archive/latest.tar.gz',
)

