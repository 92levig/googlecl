#! /bin/bash

. utils.sh

# This test program manages calendar tasks.

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

# $1 - number of expected tasks
function check_tasks_number {

    should_be \
        "python google.py calendar list --date $task_search_date -u $auth_username" \
        $1 \
        2 \
        "calendar entry" \
        "export PYTHONPATH=\"$gdata_directory/gdata-2.0.1/lib/python\" && python ../src/google.py calendar delete --date $task_search_date --title \".*\" -u $auth_username"
        
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
    python google.py calendar list --date $task_search_date --force-auth -u $auth_username
  fi

  # Creating new task
  python google.py calendar add "$task_title" --date $task_date -u $auth_username 
  
  # Checking if the task exists
  check_tasks_number 1
    
  # Deleting the task
  python google.py calendar delete --date $task_search_date --title "$task_title" -u $auth_username

  check_tasks_number 0
  
done
