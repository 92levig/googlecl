Welcome to GoogleCL's brand new test suite!

So far, we've got the downloader and installers committed. 
(Tip: download first, then install.) 

We're working to provide test suites that allow you to test against any or all
python-gdata libraries from 2.0.1 through 2.0.17.

Currently, there is a test for Google Docs Uploads. The test will run against 
all python-gdata libraries downloaded into this folder and will test uploads of 
.txt and .pdf files.

Since there are two kinds of authorization for Google Docs, we recommend running 
GoogleCL from a terminal to upload a document first. 

Be sure to set your PYTHONPATH to a gdata library in this folder
either from 2.0.1 to 2.0.5 or from 2.0.6 through 2.0.17 
and use the optional argument: --force-auth 

This will get the authentification correct before you test the other gdata 
libraries with the appropriately named shell script. 
