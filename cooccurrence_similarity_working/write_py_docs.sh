#!/bin/bash
for file in $(ls *.py) 
do
    pydoc -w ./$file
    mv ${file%.py}.html pydoc_dir/
done
