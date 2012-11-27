#! /bin/bash

. utils.sh

# This test program manages contacts.

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

contact_title="example bob"
contact_email="examplebob@example"
contact_group="test group"


touch $output_file

cd $gdata_directory

auth_executed=0

# $1 - number of expected contacts
function check_contacts_number {

    should_be \
        "./google contacts list name,email --title \"$contact_title\"" \
        $1 \
        0 \
        "contact" \
        "google contacts delete --title \"$contact_title\""
        
}

# $1 - number of expected contact groups
function check_contact_groups_number {

    should_be \
        "./google contacts list-groups --title \"$contact_group\"" \
        $1 \
        0 \
        "contact group" \
        "google contacts delete-groups --title \"$contact_group\""
        
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
    ./google contacts list name,email --title "$contact_title" --force-auth -u $auth_username
  fi

  check_contacts_number 0

  # Creating new contact
  ./google contacts add "$contact_title, $contact_email"
  
  check_contacts_number 1
  
  # Deleting the task
  ./google contacts delete --title "$contact_title"

  check_contacts_number 0
  
  # Create a contact-group
  check_contact_groups_number 0
  
  ./google contacts add-groups --title "$contact_group"
  
  check_contact_groups_number 1
  
  ./google contacts delete-groups --title "$contact_group"

  check_contact_groups_number 0  

done #>> $output_file
