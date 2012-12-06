#! /bin/bash

. utils.sh

# This test program manages tasks.

auth_username=$1

if [[ $1 == "" ]]; then
    echo "You have to provide username as the first parameter"
    exit
fi

cd "$(dirname $0)"
base_directory="$(pwd)"
googlecl_directory="$base_directory/../src"
gdata_directory="$base_directory/gdata_installs"

output_file="$base_directory/output.txt"

album_title="test_album"
tags="a b"
image="$base_directory/image.png"


touch $output_file

cd $gdata_directory

auth_executed=0

# $1 - number of expected albums
function check_albums_number {

    should_be \
        "./google picasa list-albums --title \"$album_title\"" \
        $1 \
        0 \
        "picasa album" \
        "google picasa delete --title \"$album_title\""
        
}

for i in gdata-2.0.{1..17}
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
    ./google picasa list --title $album_title --force-auth -u $auth_username
  fi
  
  check_albums_number 0
  
  # Creating new album
  ./google picasa create --title $album_title --tags "$tags"  
  
  check_albums_number 1
  
  # posting image
  ./google picasa post --title "$album_title" $image

  check_albums_number 1
  
  # Deleting the album
  ./google picasa delete --title $album_title
  
  check_albums_number 0

done #>> $output_file
