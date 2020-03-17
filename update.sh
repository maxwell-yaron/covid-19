#!/usr/bin/env bash

./update_dataset.py

./generate.py

change=$(git diff)

if [[ $change -ne 0 ]]
then
  google-chrome docs/index.html
  while true; do
    read -p "Do you wish push this update [y/n]? " yn
    case $yn in
        [Yy]* )
        git add -A
        git commit -m "Automatic Update"
        git push
        break;;
        [Nn]* ) exit;;
        * ) echo "Please answer yes or no.";;
    esac
  done
else
  echo "No changes"
fi

