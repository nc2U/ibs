import os
import re
import subprocess
from datetime import datetime

from zoneinfo import ZoneInfo
from django.core.management.base import BaseCommand
from django.db import transaction, IntegrityError
from git import Repo, GitCommandError, InvalidGitRepositoryError

from work.models import Repository, Commit, Issue, Branch


class Command(BaseCommand):
    help = "Fetch commits from local bare Git repositories"

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=None, help='Limit the number of commits to fetch')

    def handle(self, *args, **kwargs):
        limit = kwargs.get('limit')
        base_repo_path = "/app/repos"

        for repo in Repository.objects.all():
            repo_path = repo.local_path or os.path.join(base_repo_path, f"{repo.slug}.git")

            if not os.path.isdir(repo_path):
                self.stderr.write(self.style.ERROR(f"Path not found: {repo_path}"))
                continue

            try:
                try:
                    git_repo = Repo(repo_path)
                except InvalidGitRepositoryError:
                    self.stderr.write(self.style.ERROR(f"Invalid Git repository: {repo_path}"))
                    continue

                try:
                    subprocess.run(
                        ['git', 'config', '--global', '--add', 'safe.directory', repo_path],
                        check=True
                    )
                    self.stdout.write(self.style.SUCCESS("Safe directory 설정 완료!!!"))
                except subprocess.CalledProcessError as e:
                    self.stdout.write(self.style.ERROR(f"Safe directory 설정 실패: {e}"))

                try:  # ensure fetch ref spec exists
                    fetch_specs = git_repo.remote('origin').config_reader.get_value("fetch", None)
                except Exception:
                    fetch_specs = None

                if not fetch_specs:
                    git_repo.git.config('--add', 'remote.origin.fetch', '+refs/heads/*:refs/remotes/origin/*')

                git_repo.remote('origin').fetch()
                self.stdout.write(self.style.SUCCESS(f"Fetched from origin for {repo.slug}!!!"))
            except GitCommandError as e:
                self.stderr.write(self.style.ERROR(f"Git fetch failed: {e}"))
                continue

            # Branch 등록
            local_branches = [head.name for head in git_repo.heads if head.name != 'HEAD']
            # DB에 이미 등록된 브랜치 이름 목록
            existing_branches = set(repo.branches.values_list('name', flat=True))
            # 등록되지 않은 브랜치 필터링
            new_branch_names = [b for b in local_branches if b not in existing_branches]

            # 새 브랜치들 저장
            if new_branch_names:
                Branch.objects.bulk_create([
                    Branch(repo=repo, name=branch_name) for branch_name in new_branch_names
                ])
                print(f"✅ [{repo.slug}] 새 브랜치 {len(new_branch_names)}개 추가됨: {new_branch_names}")

            for ref in git_repo.references:  # 로컬 브랜치(refs/heads/*)를 원격 브랜치(refs/remotes/origin/*)로 업데이트
                if ref.name.startswith('origin/'):
                    remote_branch = ref.name  # 예: origin/master
                    branch_name = remote_branch.replace('origin/', '')  # 예: master
                    local_ref = f"refs/heads/{branch_name}"
                    remote_ref = f"refs/remotes/{remote_branch}"
                    try:
                        git_repo.git.update_ref(local_ref, remote_ref)
                        self.stdout.write(self.style.SUCCESS(f"Updated local ref {local_ref} -> {remote_ref}"))
                    except GitCommandError as e:
                        self.stderr.write(self.style.ERROR(f"Failed to update {local_ref}: {e}"))

            try:
                remote_refs = git_repo.remotes.origin.refs
                branch_candidates = ['origin/main', 'origin/master']

                default_branch = None
                for name in branch_candidates:
                    for ref in remote_refs:
                        if ref.name == name:
                            default_branch = ref.name
                            break
                    if default_branch:
                        break

                if not default_branch:
                    heads = git_repo.heads
                    if heads:
                        default_branch = heads[0].name
                    else:
                        self.stderr.write(self.style.ERROR(f"No default branch found in {repo.slug}"))
                        continue

                commits_iter = git_repo.iter_commits(default_branch, max_count=limit)
            except GitCommandError as e:
                self.stderr.write(self.style.ERROR(f"Failed to get commits: {e}"))
                continue

            existing_hashes = set(Commit.objects.filter(repo=repo).values_list('commit_hash', flat=True))
            commits_to_create = []
            commit_hashes = []
            commit_parent_map = {}  # <== 추가: 부모 해시를 저장할 딕셔너리

            for commit in reversed(list(commits_iter)):  # 오래된 순으로
                if commit.hexsha in existing_hashes:
                    self.stderr.write(self.style.WARNING(f"Skipping existing commit {commit.hexsha}"))
                    continue

                author = commit.author.name or "Unknown"
                seoul_tz = ZoneInfo("Asia/Seoul")
                date = datetime.fromtimestamp(commit.committed_date, tz=ZoneInfo("UTC")).astimezone(seoul_tz)
                message = commit.message.strip()

                # Commit 인스턴스를 준비
                commit_instance = Commit(
                    repo=repo,
                    commit_hash=commit.hexsha,
                    author=author,
                    date=date,
                    message=message,
                )
                commits_to_create.append(commit_instance)
                commit_hashes.append((commit.hexsha, message))

                # 부모 해시를 저장해 둠 (추후 parents 연결용)
                commit_parent_map[commit.hexsha] = [p.hexsha for p in commit.parents]

            if commits_to_create:
                with (transaction.atomic()):
                    try:
                        # 1차 저장
                        Commit.bulk_create_with_revision_ids(commits_to_create, ignore_conflicts=True)
                        self.stdout.write(self.style.SUCCESS(f"Created {len(commits_to_create)} commits"))

                        # 저장된 커밋들을 다시 조회하여 hash → 객체 매핑 생성
                        saved_commits = Commit.objects.filter(
                            repo=repo,
                            commit_hash__in=[c.commit_hash for c in commits_to_create])
                        commit_obj_map = {c.commit_hash: c for c in saved_commits}

                        # 2차: parents 관계 연결
                        for child_hash, parent_hashes in commit_parent_map.items():
                            child = commit_obj_map.get(child_hash)
                            if not child:
                                continue
                            parent_objs = [
                                commit_obj_map.get(p_hash)
                                for p_hash in parent_hashes if p_hash in commit_obj_map
                            ]
                            parent_objs = [p for p in parent_objs if p is not None]
                            if parent_objs:
                                child.parents.set(parent_objs)

                        # 이슈 연결
                        for commit_hash, message in commit_hashes:
                            if commit_hash not in commit_obj_map:
                                continue
                            issue_numbers = re.findall(r'#(\d+)', message)
                            if issue_numbers:
                                valid_issues = Issue.objects.filter(project=repo.project, pk__in=issue_numbers)
                                if valid_issues.exists():
                                    commit_obj_map[commit_hash].issues.add(*valid_issues)
                                    self.stdout.write(
                                        self.style.SUCCESS(
                                            f"Linked {len(valid_issues)} issues to commit {commit_hash}"
                                        )
                                    )
                    except IntegrityError as e:
                        self.stderr.write(self.style.ERROR(f"Bulk create failed: {e}"))
                        raise
            else:
                self.stdout.write(self.style.WARNING(f"No new commits to create for {repo.slug}"))

            self.stdout.write(
                self.style.SUCCESS(
                    f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                    f"Processed {repo.slug} ({len(commits_to_create)} new commits)"
                )
            )
