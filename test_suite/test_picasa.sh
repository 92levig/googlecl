#! /bin/bash

. utils.sh

print_warning \
    "PICASA" \
    "" \
    "USAGE: ./test_picasa.sh <username>"
    

# This test program manages picasa albums and pictures.

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
        "python google.py picasa list-albums --title \"$album_title\" -u $auth_username" \
        $1 \
        0 \
        "picasa album" \
        "export PYTHONPATH=\"$gdata_directory/gdata-2.0.1/lib/python\" && python ../src/google.py picasa delete --title \"$album_title\" -u $auth_username --yes"
        
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
    python google.py picasa list --title $album_title --force-auth -u $auth_username
  fi
  
  check_albums_number 0
  
  # Creating new album
  python google.py picasa create --title $album_title --tags "$tags" -u $auth_username 
  
  check_albums_number 1
  
  # posting image
  python google.py picasa post --title "$album_title" $image -u $auth_username

  check_albums_number 1
  
  # Deleting the album
  python google.py picasa delete --title $album_title -u $auth_username --yes
  
  check_albums_number 0

done #>> $output_file
