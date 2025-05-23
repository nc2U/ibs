import json
import os.path

from django.db import transaction, IntegrityError
from django.db.models import Sum, Q
from django.utils import timezone
from rest_framework import serializers

from accounts.models import User
from apiV1.serializers.accounts import SimpleUserSerializer
from work.models.project import IssueProject, Role, Permission, Member, Module, Version
from work.models.github import Repository, Commit
from work.models.logging import ActivityLogEntry, IssueLogEntry
from work.models.inform import CodeDocsCategory, News, Search
from work.models.issue import (IssueCategory, Tracker, IssueStatus, Workflow,
                               CodeActivity, CodeIssuePriority, Issue, IssueRelation,
                               IssueFile, IssueComment, TimeEntry)


class SearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Search
        fields = '__all__'
