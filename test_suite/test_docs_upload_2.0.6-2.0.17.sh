#! /bin/bash

# This test program tries to upload a txt file and a pdf file to Google Docs via 
# googlecl with python gdata2.0.6 through gdata2.0.17. It's a good idea to run
# a googlecl docs upload with --force-auth before running this script.

cd "$(dirname $0)"
base_directory="$(pwd)"
googlecl_directory="$base_directory/../src"
gdata_directory="$base_directory/gdata_installs"
txt_file="$base_directory/foo.txt"
pdf_file="$base_directory/foo.pdf"
output_file="$base_directory/output.txt"

touch $gdata_directory $txt_file $pdf_file $output_file

cd $gdata_directory

for i in gdata-2.0.{6..17}
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

  ./google docs upload $txt_file  
  ./google docs upload $pdf_file   
done #>> $output_file
