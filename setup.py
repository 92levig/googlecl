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
      install_requires=['gdata'],
      long_description="""The Google Data APIs allow programmatic access to
various Google services.  This package wraps a subset of those APIs into a
command-line tool that makes it easy to do things like posting to a Blogger
blog, uploading files to Picasa, or editing a Google Docs file.""",
      classifiers=[
          'Topic :: Internet :: WWW/HTTP',
          'Environment :: Console',
          'Development Status :: 4 - Beta',
          'Operating System :: POSIX',
          'Intended Audience :: Developers',
          'Intended Audience :: End Users/Desktop'
      ]     
     ) 
