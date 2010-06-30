# Copyright (C) 2010 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

try:
  from setuptools import setup
except ImportError:
  from distutils.core import setup
packages =['googlecl',
           'googlecl.blogger',
           'googlecl.calendar',
           'googlecl.contacts',
           'googlecl.docs',
           'googlecl.picasa',
           'googlecl.youtube']
 
long_desc = """The Google Data APIs allow programmatic access to
various Google services.  This package wraps a subset of those APIs into a
command-line tool that makes it easy to do things like posting to a Blogger
blog, uploading files to Picasa, or editing a Google Docs file."""


setup(name="googlecl",
      version="0.9.7",
      description="Use (some) Google services from the command line",
      author="Tom H. Miller",
      author_email="tom.h.miller@gmail.com",
      url="http://code.google.com/p/googlecl",
      license="Apache Software License",
      packages=packages,
      package_dir={'googlecl':'src/googlecl'},
      scripts=["src/google"],
      install_requires=['gdata >=1.2.4'],
      long_description=long_desc,
      classifiers=[
          'Topic :: Internet :: WWW/HTTP',
          'Environment :: Console',
          'Development Status :: 4 - Beta',
          'Operating System :: POSIX',
          'Intended Audience :: Developers',
          'Intended Audience :: End Users/Desktop'
      ]     
     ) 
