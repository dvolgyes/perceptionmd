#!/usr/bin/env python
from distutils.core import setup
from distutils.command.install import INSTALL_SCHEMES
import platform
import sys

conda = sys.version.find("conda")>-1
for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']

system = platform.system()

reqs = ['cachetools','pydicom','textx','matplotlib','pycontracts','docutils','pygame','numpy','wget','six']

print("Conda is detected" if conda else "Conda is not detected")

if not conda:
    reqs += ["kivy"]
    if system != 'Linux':
        pass
        #reqs=['kivy.deps.angle','kivy.deps.gstreamer','kivy.deps.sdl2','kivy.deps.glew'] + reqs

setup(
  include_data_files = True,
  name = 'perceptionmd',
  version = '0.1.6',
  description = 'Human observer tests for radiology',
  author = 'David Volgyes',
  author_email = 'david.volgyes@ieee.org',
  url = 'https://github.com/dvolgyes/perceptionmd',
  packages = ['perceptionmd','perceptionmd/utils','perceptionmd/volumes'],
  scripts=['PerceptionMD.py','PerceptionMD.bat'],
  data_files = [('perceptionmd', ['LICENSE.txt','README.txt']),
                ('perceptionmd/lang', ['perceptionmd/lang/perception.tx']),
                ('perceptionmd/widgets', ['perceptionmd/widgets/infoscreen.kv']),
                ('perceptionmd/unittests',['perceptionmd/unittests/travis-example.pmd'])],
  keywords = ['testing', 'example'],
  classifiers = [],
  license = 'AGPL3',
  install_requires=reqs,
#  download_url = 'https://github.com/dvolgyes/perceptionmd/archive/latest.tar.gz',
)

