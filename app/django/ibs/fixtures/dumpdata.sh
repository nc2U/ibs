#!/bin/bash

python ../../manage.py dumpdata \
    board.group board.board docs.doctype docs.category \
    cash.bankcode ibs.accountsort ibs.accountsubd1 ibs.accountsubd2 \
    ibs.accountsubd3 ibs.projectaccountd2 ibs.projectaccountd3 \
    work.role work.tracker work.issuestatus work.codeactivity \
    work.codeissuepriority work.codedocscategory ibs.wisesaying \
    --indent 2 > seeds-data.json
