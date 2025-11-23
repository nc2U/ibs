#!/bin/bash

python ../../manage.py dumpdata \
    docs.doctype docs.category cash.bankcode ledger.bankcode contract.documenttype \
    ibs.accountsort ibs.accountsubd1 ibs.accountsubd2 ibs.accountsubd3 \
    ibs.projectaccountd2 ibs.projectaccountd3 ibs.wisesaying \
    work.role work.permission work.tracker work.issuestatus \
    work.codeactivity work.codeissuepriority work.codedocscategory  \
    --indent 2 > seeds-data.json
