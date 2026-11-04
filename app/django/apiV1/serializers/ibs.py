from rest_framework import serializers

from apiV1.serializers.accounts import SimpleUserSerializer
from ibs.models import (AccountSort, AccountSubD1, AccountSubD2, AccountSubD3,
                        ProjectAccountD2, ProjectAccountD3, UserWidgetConfig,
                        CalendarSchedule, WiseSaying)


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
        fields = ('pk', 'sort', 'd2', 'code', 'name', 'description', 'is_hide', 'is_special')


class ProjectAccountD2Serializer(serializers.ModelSerializer):
    d1 = serializers.SlugRelatedField(queryset=AccountSubD1.objects.all(), slug_field='name')

    class Meta:
        model = ProjectAccountD2
        fields = ('pk', 'd1', 'code', 'name', 'description')


class ProjectAccountD3Serializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectAccountD3
        fields = ('pk', 'sort', 'd2', 'code', 'is_payment', 'is_related_contract', 'name', 'description')


class UserWidgetConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserWidgetConfig
        fields = ('pk', 'layouts', 'visible_widgets', 'version')


class CalendarScheduleSerializer(serializers.ModelSerializer):
    creator = SimpleUserSerializer(read_only=True)

    class Meta:
        model = CalendarSchedule
        fields = ('pk', 'title', 'all_day', 'start_date', 'end_date', 'start_time',
                  'end_time', 'creator', 'created', 'updated')

    def validate(self, attrs):
        all_day = attrs.get('all_day', getattr(self.instance, 'all_day', True))
        start_date = attrs.get('start_date', getattr(self.instance, 'start_date', None))
        end_date = attrs.get('end_date', getattr(self.instance, 'end_date', None))
        start_time = attrs.get('start_time', getattr(self.instance, 'start_time', None))
        end_time = attrs.get('end_time', getattr(self.instance, 'end_time', None))

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({'end_date': '종료 일자는 시작 일자 이후여야 합니다.'})

        if not all_day and start_time and end_time and start_time > end_time:
            raise serializers.ValidationError({'end_time': '종료 시간은 시작 시간 이후여야 합니다.'})

        return attrs



class WiseSaySerializer(serializers.ModelSerializer):
    class Meta:
        model = WiseSaying
        fields = ('pk', 'saying_ko', 'saying_en', 'spoked_by')
