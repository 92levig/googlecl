#! /bin/bash

# I've occasionally seen delayed results, where a video didn't appear
# immediately.  So I've added sleep 3 in check_videos.  Occasionally this
# may not be enough, and the error might appear transiently.

. utils.sh

print_warning \
    "YOUTUBE" \
    "" \
    "USAGE: ./test_youtube <username>"

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

touch $output_file

cd $gdata_directory

auth_executed=0

video_title="foo"
video="$base_directory/foo.ogv"

# $1 - number of expected videos
function check_videos {
    sleep 3
    should_be \
        "python google.py youtube list -u $auth_username" \
        $1 \
        0 \
        "video" \
        "export PYTHONPATH=\"$gdata_directory/gdata-2.0.1/lib/python\" && python ../src/google.py youtube delete --title \"$video_title\" -u $auth_username --yes"
        
}

for i in gdata-2.0.{1..10} gdata-2.0.{12..17}
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
    python google.py youtube list --force-auth -u $auth_username
  fi

  check_videos 0

  python google.py youtube post $video --title "$video_title" \
      -u $auth_username --category=Education
    
  check_videos 1
  
  python google.py youtube delete --title "$video_title" -u $auth_username --yes

  check_videos 0
done
