from django.db import models
from django.conf import settings

# class AccountSort(models.Model):
#     name = models.CharField(max_length=2)
#
#     def __str__(self):
#         return self.name
#
#     class Meta:
#         ordering = ['id']
#         verbose_name = "01. (공통) - 입출금 구분"
#         verbose_name_plural = "01. (공통) - 입출금 구분"
#
#
# class AccountSubD1(models.Model):
#     sorts = models.ManyToManyField('rebs.AccountSort')
#     code = models.CharField(max_length=3)
#     name = models.CharField(max_length=10)
#     description = models.CharField(max_length=20)
#
#     def __str__(self):
#         return f'[{self.code}] {self.name} 계정'
#
#     class Meta:
#         ordering = ['id']
#         verbose_name = "02. (공통) - 회계계정 과목"
#         verbose_name_plural = "02. (공통) - 회계계정 과목"
#
#
# class AccountSubD2(models.Model):
#     d1 = models.ForeignKey(AccountSubD1, on_delete=models.CASCADE, related_name='acc_d2s')
#     code = models.CharField(max_length=3)
#     name = models.CharField(max_length=20)
#     description = models.CharField(max_length=50)
#
#     def __str__(self):
#         return f'[{self.code}] {self.name}'
#
#     class Meta:
#         ordering = ['id']
#         verbose_name = "03. 본사 계정"
#         verbose_name_plural = "03. 본사 계정"
#
#
# class AccountSubD3(models.Model):
#     sort = models.ForeignKey(AccountSort, on_delete=models.CASCADE)
#     d2 = models.ForeignKey(AccountSubD2, on_delete=models.CASCADE, related_name='acc_d3s')
#     code = models.CharField(max_length=3)
#     name = models.CharField(max_length=20)
#     is_hide = models.BooleanField(default=False)
#     is_special = models.BooleanField(default=False)
#     description = models.CharField(max_length=50)
#
#     def __str__(self):
#         return f'[{self.code}] {self.name}'
#
#     class Meta:
#         ordering = ['id']
#         verbose_name = "04. 본사 세부계정"
#         verbose_name_plural = "04. 본사 세부계정"
#
#
# class ProjectAccountD2(models.Model):
#     d1 = models.ForeignKey(AccountSubD1, on_delete=models.CASCADE, related_name='pro_d2s')
#     code = models.CharField(max_length=3)
#     name = models.CharField(max_length=20)
#     description = models.CharField(max_length=50, blank=True)
#
#     def __str__(self):
#         return self.name
#
#     class Meta:
#         ordering = ('id',)
#         verbose_name = "05. 프로젝트 계정"
#         verbose_name_plural = "05. 프로젝트 계정"
#
#
# class ProjectAccountD3(models.Model):
#     sort = models.ForeignKey(AccountSort, on_delete=models.CASCADE)
#     d2 = models.ForeignKey(ProjectAccountD2, on_delete=models.CASCADE, related_name='pro_d3s')
#     code = models.CharField(max_length=3)
#     is_related_contract = models.BooleanField(default=False)
#     name = models.CharField(max_length=20)
#     description = models.CharField(max_length=50, blank=True)
#
#     def __str__(self):
#         return self.name
#
#     class Meta:
#         ordering = ('id',)
#         verbose_name = "06. 프로젝트 세부계정"
#         verbose_name_plural = "06. 프로젝트 세부계정"
#
#
# class CalendarSchedule(models.Model):
#     title = models.CharField('일정 제목', max_length=100)
#     all_day = models.BooleanField(default=True)
#     start_date = models.DateField('시작 일자', null=True, blank=True)
#     end_date = models.DateField('종료 일자', null=True, blank=True)
#     start_time = models.DateTimeField('시작 시간', null=True, blank=True)
#     end_time = models.DateTimeField('종료 시간', null=True, blank=True)
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='등록자')
#     created_at = models.DateTimeField('등록일', auto_now_add=True)
#     updated_at = models.DateTimeField('수정일', auto_now=True)
#
#
# class WiseSaying(models.Model):
#     saying_ko = models.CharField(max_length=300)
#     saying_en = models.CharField(max_length=300)
#     spoked_by = models.CharField(max_length=50, blank=True)
#
#     def __str__(self):
#         return f'{self.saying_ko} - {self.spoked_by}'
#
#     class Meta:
#         verbose_name = "오늘의 한마디"
#         verbose_name_plural = "오늘의 한마디"
