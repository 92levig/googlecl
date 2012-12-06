#! /bin/bash

. utils.sh

if [[ $1 == "" ]]; then
    echo "You have to provide username as the first parameter"
    exit
fi

if [[ $2 == "" ]]; then
    echo "You have to provide folder name as the second parameter"
    exit
fi

# This test program lists all the documents from given folder.

auth_username=$1
folder_name=$2

cd "$(dirname $0)"
base_directory="$(pwd)"
googlecl_directory="$base_directory/../src"
gdata_directory="$base_directory/gdata_installs"
output_file="$base_directory/output.txt"

touch $output_file

cd $gdata_directory

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
  
  ./google docs --folder "$folder_name" list

done
