#! /bin/bash

. utils.sh

print_warning \
    "DOCUMENTS" \
    "" \
    "USAGE: ./test_docs_upload_2.0.1_2.0.4.sh <username>"

if [[ $1 == "" ]]; then
    echo "You have to provide username as the first parameter"
    exit
fi

# This test program tries to upload a txt file and a pdf file to Google Docs via 
# googlecl with python gdata2.0.1 through gdata2.0.5. It's a good idea to run
# a googlecl docs upload with --force-auth before running this script.

# Just because the versions 10-17 supports uploading files:
# http://code.google.com/p/googlecl/wiki/UploadingGoogleDocs
#
#The following versions of python-gdata support uploading some file types, like text files, but do not support uploading arbitrary file types (like PDFs).
#
#2.0.0
#2.0.1
#2.0.2
#2.0.3
#2.0.4

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

auth_executed=0

# $1 - number of expected documents
function check_docs_number {
    
    should_be \
        "python google.py docs list title,url-direct --title "$test_file_name" -u $auth_username" \
        $1 \
        0 \
        "document" \
        "export PYTHONPATH=\"$gdata_directory/gdata-2.0.1/lib/python\" && python ../src/google.py docs delete --title \"$test_file_name\" -u $auth_username"
        
}

for i in gdata-2.0.{1..4}
do
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
    python google.py docs list title,url-direct --force-auth -u $auth_username
  fi
  
  check_docs_number 0

  # Test uploading text file
  python google.py docs upload $txt_file -u $auth_username
  
  check_docs_number 1  
  
  # Delete the uploaded file
  python google.py docs delete --title "$test_file_name" -u $auth_username
      
  check_docs_number 0
  
done
