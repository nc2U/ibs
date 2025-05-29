from django.db import models

from work.models.project import IssueProject


class Repository(models.Model):
    project = models.ForeignKey(IssueProject, on_delete=models.CASCADE, verbose_name='프로젝트')
    is_default = models.BooleanField('주저장소', default=False)
    slug = models.CharField('식별자', max_length=255, unique=True,
                            help_text='1 에서 255 글자 소문자(a-z),숫자,대쉬(-)와 밑줄(_)만 가능합니다. 식별자는 저장후에는 수정할 수 없습니다.')
    local_path = models.CharField('저장소 경로', max_length=255, help_text='로컬의 bare 저장소 (예: /app/repos/repo.git)')
    is_report = models.BooleanField('파일이나 폴더의 마지막 커밋을 보고', default=False)

    def __str__(self):
        return f'{self.slug}'

    class Meta:
        ordering = ('id',)
        verbose_name = '15. 저장소'
        verbose_name_plural = '15. 저장소'


class Commit(models.Model):
    repo = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name='commits')
    commit_hash = models.CharField(max_length=40, unique=True)
    message = models.TextField(default='')
    author = models.CharField(max_length=100, default='Unknown')
    date = models.DateTimeField(db_index=True)
    issues = models.ManyToManyField('Issue', blank=True)

    class Meta:
        ordering = ('-id',)
        verbose_name = '16. 커미트'
        verbose_name_plural = '16. 커미트'
