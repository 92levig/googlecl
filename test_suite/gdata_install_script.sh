#!/bin/bash

# This program takes unpacked tarballs and installs
# them into the designated directories (creating them
# if necessary). 

cd "$(dirname $0)"
base_directory="$(pwd)"
tarball_directory=$base_directory/gdata_tarballs/unpacked
install_directory=$base_directory/gdata_installs

if [[ -d $tarball_directory ]] ; then  
  echo
else 
  mkdir -p $tarball_directory
fi

if [[ -d $install_directory ]] ; then  
  echo
else 
  mkdir -p $install_directory
fi  


cd $tarball_directory

for i in {1..17}
do
  echo $i
  cd $tarball_directory/gdata-2.0.$i
  pwd
  target=$install_directory/gdata-2.0.$i
  if [[ -d $target ]] ; then
    continue  
  fi
  mkdir -p $target
  echo $target
   
  export PYTHONPATH=$target
  echo $PYTHONPATH    

  python setup.py install --home=$target
done    
