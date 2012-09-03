#! /bin/bash

# This program downloads all versions of python-gdata and unpacks them.
cd "$(dirname $0)"
base_directory="$(pwd)"
compressed_tarball_directory="$base_directory/gdata_tarballs/compressed"
unpacked_tarball_directory="$base_directory/gdata_tarballs/unpacked"

if [[ -d $compressed_tarball_directory ]] ; then  
  echo
else 
  mkdir -p $compressed_tarball_directory
fi

if [[ -d $unpacked_tarball_directory ]] ; then  
  echo
else 
  mkdir -p $unpacked_tarball_directory
fi  

for i in {1..17}
do
  cd $compressed_tarball_directory
  if [[ ! -f  $compressed_tarball_directory/gdata-2.0.$i.tar.gz ]] ; then
    #Because gdata-2.0.11 is different. . . 
    if [[ $i == 11 ]]  ; then
      wget "http://gdata-python-client.googlecode.com/files/gdata-2.0.$i.final.tar.gz" 
      mv gdata-2.0.$i.final.tar.gz gdata-2.0.$i.tar.gz
    else
      wget "http://gdata-python-client.googlecode.com/files/gdata-2.0.$i.tar.gz" 
    fi
    cd $unpacked_tarball_directory
    tar -xvf $compressed_tarball_directory/gdata-2.0.$i.tar.gz
  fi
done
