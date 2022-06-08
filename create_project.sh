#!/bin/bash

set -e
#if [[ $# -lt 1 ]]; then
#    echo "Missing script parameter:  you must supply the system name to replace 'licensing_template'"
#    echo "$0 1"
#    exit 1
#fi

# Gather required user input
read -p 'Github username: ' gituser
read -p 'Github repo name: ' gitrepo

gituser=${gituser,,}
gitdir=${gitrepo/"-"/"_"}

# clone gitrepo
{
    cd ../
    git clone git@github.com:$gituser/$gitrepo.git $gitrepo
} ||
{
    echo "Error: $gitrepo repo/fork does not exist on your Github account $gituser"
    echo "$0 1"
    exit 1
}

# return to licensing-template folder
cd licensing-template &&

# rename dirs
mv ./licensing_template/ ./$gitdir/ &&
DIR_LIST=$(find . -type d -name "*licensing_template*")
for f in $DIR_LIST
do 
    mv $f $(echo $f | sed "s/licensing_template/$gitdir/g")
done &&

# rename files 
FILE_LIST=$(find . -type f -name "*licensing_template*")
for f in $FILE_LIST
do 
    mv $f $(echo $f | sed "s/licensing_template/$gitdir/g")
done &&

# replace all occurrences of "licensing_system" with new system name
find . -type f -exec sed -i "s/licensing_template/$gitdir/g" {} \;

# clean licensing-template, copy files to new project then delete licensing-template
rm -rf .git && rm rename_project.sh &&
cd ../ && cp -r licensing-template/ $gitrepo/ &&

echo "Files have been copied to your new repo" &&
rm -rf licensing-template/
echo "Licensing template has been removed"

