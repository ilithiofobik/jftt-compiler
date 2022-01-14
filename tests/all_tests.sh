#!/bin/bash
for FILE in *.imp; do
	FN="${FILE%%.*}"
    in_file="${FN}_in.txt"
    out_file="out.txt"
    expected_file="${FN}_out.txt"
    rm -f out.mr
	python3 ../kompilator.py "$FN.imp" "out.mr" 
    ../test_vm/maszyna-wirtualna-cln "out.mr" < $in_file > "out.txt" 2> "error.txt"
    diff_res=$(diff $out_file $expected_file)

    if [ -s "error.txt" ] || [ "$diff_res" ] ; then
        echo -e "\033[0;31m$FN: FAILED\033[0m"
        if [ -s "error.txt" ] ; then
            cat < error.txt
        else
            echo $diff_res
        fi
    else
        echo -e "\033[0;32m$FN: PASSED\033[0m"
    fi
done