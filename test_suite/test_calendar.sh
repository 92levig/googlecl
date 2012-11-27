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

task_title="exampletask"
task_search_date="2012-11-09"
task_date="2012-11-10"

touch $output_file

cd $gdata_directory

auth_executed=0

# $1 - number of expected contacts
function check_contacts_number {

    should_be \
        "./google calendar list --date $task_search_date" \
        $1 \
        2 \
        "calendar entry" \
        "google calendar delete --date $task_search_date --title \".*\""
        
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
    ./google calendar list --date $task_search_date --force-auth -u $auth_username
  fi

  # Creating new task
  ./google calendar add "$task_title" --date $task_date 
  
  # Checking if the task exists
  check_contacts_number 1
    
  # Deleting the task
  ./google calendar delete --date $task_search_date --title "$task_title"

  check_contacts_number 0
  
done #>> $output_file
