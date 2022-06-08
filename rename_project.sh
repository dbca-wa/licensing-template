#!/bin/bash

set -e
if [[ $# -lt 1 ]]; then
    echo "Missing script parameter:  you must supply the system name to replace 'licensing_template'"
    echo "$0 1"
    exit 1
fi

# rename dirs
mv ./licensing_template/ ./$1/ &&
DIR_LIST=$(find . -type d -name "*licensing_template*")
for f in $DIR_LIST
do 
    mv $f $(echo $f | sed "s/licensing_template/$1/g")
done &&

# rename files 
FILE_LIST=$(find . -type f -name "*licensing_template*")
for f in $FILE_LIST
do 
    mv $f $(echo $f | sed "s/licensing_template/$1/g")
done &&

# replace all occurrences of "licensing_system" with new system name
#find . -type f -exec sed -i "s/licensing_template/$1/g" {} \;
find . -path ./.git -prune -o -print | xargs sed -i "s/licensing_template/$1/g"
