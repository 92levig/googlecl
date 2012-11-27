#! /bin/bash

# This test program tries to upload a txt file and a pdf file to Google Docs via 
# googlecl with python gdata2.0.1 through gdata2.0.5. It's a good idea to run
# a googlecl docs upload with --force-auth before running this script.

# Just because the versions 10-17 supports uploading files:
# http://code.google.com/p/googlecl/wiki/UploadingGoogleDocs
#
#The following versions of python-gdata do not support uploading anything to Google Docs.
#
#2.0.5
#2.0.6
#2.0.7
#2.0.8
#2.0.9
#2.0.11

echo ""
echo "GOOGLE DOCS DON'T WORK FOR THE FOLLOWING GDATA VERSIONS:"
echo "   2.0.5"
echo "   2.0.6"
echo "   2.0.7"
echo "   2.0.8"
echo "   2.0.9"
echo "   2.0.11"
echo ""

exit;

