from rest_framework import serializers

from ibs.models import (AccountSort, AccountSubD1, AccountSubD2, AccountSubD3,
                        ProjectAccountD2, ProjectAccountD3, CalendarSchedule, WiseSaying)


# Ibs --------------------------------------------------------------------------
class AccountSortSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountSort
        fields = ('pk', 'name')


class AccountSubD1Serializer(serializers.ModelSerializer):
    class Meta:
        model = AccountSubD1
        fields = ('pk', 'sorts', 'code', 'name', 'description')


class AccountSubD2Serializer(serializers.ModelSerializer):
    class Meta:
        model = AccountSubD2
        fields = ('pk', 'd1', 'code', 'name', 'description')


class AccountSubD3Serializer(serializers.ModelSerializer):
    class Meta:
        model = AccountSubD3
        fields = ('pk', 'd2', 'code', 'name', 'description', 'is_hide', 'is_special')


class ProjectAccountD2Serializer(serializers.ModelSerializer):
    d1 = serializers.SlugRelatedField(queryset=AccountSubD1.objects.all(), slug_field='name')

    class Meta:
        model = ProjectAccountD2
        fields = ('pk', 'd1', 'code', 'name', 'description')


class ProjectAccountD3Serializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectAccountD3
        fields = ('pk', 'd2', 'code', 'is_related_contract', 'name', 'description')


class CalendarScheduleSerializer(serializers.ModelSerializer):
    from apiV1.serializers.accounts import SimpleUserSerializer
    creator = SimpleUserSerializer(read_only=True)

    class Meta:
        model = CalendarSchedule
        fields = ('pk', 'title', 'all_day', 'start_date', 'end_date', 'start_time',
                  'end_time', 'creator', 'created', 'updated')


class WiseSaySerializer(serializers.ModelSerializer):
    class Meta:
        model = WiseSaying
        fields = ('pk', 'saying_ko', 'saying_en', 'spoked_by')
