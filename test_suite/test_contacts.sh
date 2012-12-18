#! /bin/bash

. utils.sh

print_warning \
    "CALENDAR" \
    "" \
    "USAGE: ./test_contacts.sh <username>"

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

    sleep 5
   
    should_be \
        "python google.py contacts list name,email --title \"$contact_title\" -u $auth_username" \
        $1 \
        0 \
        "contact" \
        "export PYTHONPATH=\"$gdata_directory/gdata-2.0.1/lib/python\" && python ../src/google.py contacts delete --title \"$contact_title\" -u $auth_username --yes"
        
}

# $1 - number of expected contact groups
function check_contact_groups_number {

    sleep 5

    should_be \
        "python google.py contacts list-groups --title \"$contact_group\" -u $auth_username" \
        $1 \
        0 \
        "contact group" \
        "export PYTHONPATH=\"$gdata_directory/gdata-2.0.1/lib/python\" && python ../src/google.py contacts delete-groups --title \"$contact_group\" -u $auth_username --yes"
        
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
    python google.py contacts list name,email --title "$contact_title" --force-auth -u $auth_username
  fi

  check_contacts_number 0

  # Creating new contact
  python google.py contacts add "$contact_title, $contact_email" -u $auth_username
    
  check_contacts_number 1
  
  # Deleting the task
  python google.py contacts delete --title "$contact_title" -u $auth_username --yes

  check_contacts_number 0
  
  # Create a contact-group
  check_contact_groups_number 0
  
  python google.py contacts add-groups --title "$contact_group" -u $auth_username
  
  check_contact_groups_number 1
  
  python google.py contacts delete-groups --title "$contact_group" -u $auth_username --yes

  check_contact_groups_number 0  

done
