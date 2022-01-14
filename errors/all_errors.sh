#!/bin/bash
for FILE in *.imp; do
	FN="${FILE%%.*}"
    in_file="${FN}_in.txt"
    error_file="error.txt"
    expected_file="${FN}_out.txt"
    rm -f out.mr
	python3 ../kompilator.py "$FN.imp" "out.mr" 2> $error_file

    diff_res=$(diff $error_file $expected_file)

    if [ "$diff_res" ] ; then
        echo -e "\033[0;31m$FN: FAILED\033[0m"
        echo $diff_res
    else
        echo -e "\033[0;32m$FN: PASSED\033[0m"
    fi
done