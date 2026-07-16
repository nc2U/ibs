#!/bin/bash

# 1. work.CustomQuery를 제외한 다른 모델들을 seeds-data.json으로 덤프
python ../../manage.py dumpdata \
    docs.category ledger.bankcode \
    ledger.companyaccount ledger.projectaccount contract.documenttype \
    ibs.accountsort ibs.accountsubd1 ibs.accountsubd2 ibs.accountsubd3 \
    ibs.projectaccountd2 ibs.projectaccountd3 ibs.wisesaying \
    work.role work.permission work.tracker work.issuestatus work.codeissuepriority \
    --indent 2 --output seeds-data.json

# 2. work.CustomQuery 모델의 pk 1, 2번 데이터만 임시 파일로 덤프
python ../../manage.py dumpdata work.CustomQuery --pks 1,2 --indent 2 --output seeds-customquery-temp.json

# 3. Python 스크립트를 사용하여 두 json 파일을 병합하고 임시 파일 삭제
python -c "
import json
import os

try:
    with open('seeds-data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
except Exception:
    data = []

try:
    with open('seeds-customquery-temp.json', 'r', encoding='utf-8') as f:
        cq_data = json.load(f)
except Exception:
    cq_data = []

# 두 데이터를 병합하여 저장
with open('seeds-data.json', 'w', encoding='utf-8') as f:
    json.dump(data + cq_data, f, ensure_ascii=False, indent=2)

if os.path.exists('seeds-customquery-temp.json'):
    os.remove('seeds-customquery-temp.json')
"
