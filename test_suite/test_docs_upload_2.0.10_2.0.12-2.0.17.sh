#! /bin/bash

. utils.sh

if [[ $1 == "" ]]; then
    echo "You have to provide username as the first parameter"
    exit
fi

# This test program tries to upload a txt file and a pdf file to Google Docs via 
# googlecl with python gdata2.0.6 through gdata2.0.17. It's a good idea to run
# a googlecl docs upload with --force-auth before running this script.
#
# Just because the versions 10-17 supports uploading files:
# http://code.google.com/p/googlecl/wiki/UploadingGoogleDocs
#
#The following versions of python-gdata fully support uploading arbitrary file types to Google Docs via googlecl. In order to get the version of GoogleCL that fully supports docs uploads, check it out from svn.
#
#2.0.10
#2.0.12
#2.0.13
#2.0.14
#2.0.15
#2.0.16

auth_username=$1

cd "$(dirname $0)"
base_directory="$(pwd)"
googlecl_directory="$base_directory/../src"
gdata_directory="$base_directory/gdata_installs"
txt_file="$base_directory/foo.txt"
pdf_file="$base_directory/foo.pdf"
test_file_name="foo"
output_file="$base_directory/output.txt"

touch $output_file

cd $gdata_directory

auth_executed=0

# This tests uploading files, listing and deleting them

# $1 - number of expected documents
function check_docs_number {

    should_be \
        "./google docs list title,url-direct --title "$test_file_name"" \
        $1 \
        0 \
        "document" \
        "google docs delete --title \"$test_file_name\""
        
}

auth_executed=0

for i in gdata-2.0.{10..17} 
do
  if [[ $i == "gdata-2.0.11" ]]; then continue; fi

  echo -e '\n\n'
  echo "-----------------------------------------------------------------------" 
  echo "$i" 

  cd $gdata_directory/$i
  pwd
  
  export PYTHONPATH="$gdata_directory/$i/lib/python"
  echo "$PYTHONPATH" 

  cd $googlecl_directory
  pwd 

  if [[ $auth_executed == "0" ]]; then
    auth_executed=1 
    ./google docs list title,url-direct --force-auth -u $auth_username
  fi
  
  check_docs_number 0

  # Test uploading text file
  ./google docs upload $txt_file
  
  # Check the file exists
  check_docs_number 1
  
  # Delete the uploaded file
  ./google docs delete --title "$test_file_name"
  
  check_docs_number 0
  

done #>> $output_file
