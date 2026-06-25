#!/bin/bash

python ../../manage.py dumpdata \
    docs.doctype docs.category ledger.bankcode \
    ledger.companyaccount ledger.projectaccount contract.documenttype \
    ibs.accountsort ibs.accountsubd1 ibs.accountsubd2 ibs.accountsubd3 \
    ibs.projectaccountd2 ibs.projectaccountd3 ibs.wisesaying \
    work.role work.permission work.tracker work.issuestatus work.codeissuepriority  \
    --indent 2 --output seeds-data.json
