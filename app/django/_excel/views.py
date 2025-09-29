##############################################################################
#
# A Django view class to write an Excel file using the XlsxWriter
# module.
#
# Copyright 2013-2020, John McNamara, jmcnamara@cpan.org
#
import datetime
import io
import json

import xlsxwriter
import xlwt
from django.core import serializers
from django.db.models import Q, F, Sum, When, Case, PositiveBigIntegerField
from django.http import HttpResponse
from django.views.generic import View

from cash.models import CashBook, ProjectCashBook
from company.models import Company, Staff, Department, JobGrade, Position, DutyTitle
from contract.models import Contract
from docs.models import LawsuitCase
from project.models import Project, ProjectOutBudget, Site, SiteOwner, SiteContract

TODAY = datetime.date.today().strftime('%Y-%m-%d')
