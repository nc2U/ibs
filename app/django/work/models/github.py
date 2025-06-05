from django.db import models, transaction
from django.db.models.aggregates import Max

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
    revision_id = models.PositiveIntegerField(null=True, blank=True)
    repo = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name='commits')
    parents = models.ManyToManyField('self', symmetrical=False, related_name='children', blank=True)
    commit_hash = models.CharField(max_length=40, unique=True)
    message = models.TextField(default='')
    author = models.CharField(max_length=100, default='Unknown')
    date = models.DateTimeField(db_index=True)
    issues = models.ManyToManyField('Issue', blank=True)

    def __str__(self):
        return f"{self.repo.slug}: {self.commit_hash[:7]} (Rev {self.revision_id})"

    class Meta:
        ordering = ('-id',)
        verbose_name = '16. 커미트'
        verbose_name_plural = '16. 커미트'
        unique_together = ('repo', 'revision_id')

    def save(self, *args, **kwargs):
        if self.revision_id is None:
            with transaction.atomic():
                max_revision = Commit.objects.filter(repo=self.repo) \
                    .select_for_update().aggregate(Max('revision_id')) \
                    ['revision_id__max']
                self.revision_id = (max_revision or 0) + 1
        super().save(*args, **kwargs)

    @classmethod
    def bulk_create_with_revision_ids(cls, commits, ignore_conflicts=False):
        """
        Commit 객체 리스트를 bulk_create하며, Repository별 revision_id를 설정.
        Args: commits: Commit 객체 리스트
        ignore_conflicts: 중복 레코드 무시 여부 (default: False)
        Returns: 생성된 Commit 객체 리스트
        """
        if not commits:
            return []
        repo_commits = {}  # Repository별로 커밋 그룹화
        for commit in commits:
            if commit.repo_id not in repo_commits:
                repo_commits[commit.repo_id] = []
            repo_commits[commit.repo_id].append(commit)
        with transaction.atomic():
            for repo_id in repo_commits:  # 각 Repository의 최대 revision_id 조회
                max_revision = (
                        cls.objects.filter(repo_id=repo_id)
                        .select_for_update()
                        .aggregate(Max('revision_id'))['revision_id__max'] or 0
                )
                for index, commit in enumerate(repo_commits[repo_id], start=1):  # 커밋들에 순차적 revision_id 부여
                    commit.revision_id = max_revision + index
            return cls.objects.bulk_create(commits, ignore_conflicts=ignore_conflicts)  # bulk_create 실행
