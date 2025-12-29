#!/bin/bash

# python manage.py makemigrations accounts board book cash company contract docs ibs items ledger notice payment project work
python manage.py migrate --database=default