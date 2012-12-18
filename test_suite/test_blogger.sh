#! /bin/bash

. utils.sh

print_warning \
    "BLOGGER" \
    "THERE SHOULD ALREADY EXIST THE BLOG GIVEN AS THE SECOND PARAMETER" \
    "USAGE: ./test_blogger.sh <username> <blogname>"
    
# This script tests managing blogger posts by the googlecl application.

auth_username=$1

if [[ $1 == "" ]]; then
    echo "You have to provide username as the first parameter"
    exit
fi

blogname=$2

if [[ $2 == "" ]]; then
    echo "You have to provide an existing blog name as the second parameter"
    exit
fi

cd "$(dirname $0)"
base_directory="$(pwd)"
googlecl_directory="$base_directory/../src"
gdata_directory="$base_directory/gdata_installs"

output_file="$base_directory/output.txt"


post_title="example post title" 
post_body="example post body"
post_tags="a,b"

touch $output_file

cd $gdata_directory

auth_executed=0

# $1 - number of expected blog posts
function check_posts_number {

    should_be \
        "python google.py blogger list --title \"$post_title\" --blog $blogname -u $auth_username" \
        $1 \
        0 \
        "blog post" \
        "export PYTHONPATH=\"$gdata_directory/gdata-2.0.1/lib/python\" && python ../src/google.py blogger delete --title \"$post_title\" --blog $blogname -u $auth_username --yes"
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
    python google.py blogger list --blog $blogname --force-auth -u $auth_username
  fi

  check_posts_number 0

  # Creating new blog post.
  python google.py blogger post --title "$post_title" --blog $blogname -u $auth_username "adlasdasd" 
  
  check_posts_number 1
  
  # Tagging the blog post, unfortunately there is no way to check if it worked.
  python google.py blogger tag --blog $blogname --title "$post_title" -u $auth_username --tags "$post_tags"
  
  # Deleting the blog post.
  python google.py blogger delete --blog $blogname --title "$post_title" -u $auth_username --yes

  check_posts_number 0
  

done 
