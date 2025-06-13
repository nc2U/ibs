import os
import re
import subprocess
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand
from django.db import transaction, IntegrityError, connection
from git import Repo, GitCommandError, InvalidGitRepositoryError

from work.models import Repository, Commit, Issue, Branch


class Command(BaseCommand):
    help = "Fetch commits from local bare Git repositories and sync branches"

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=None, help='Limit the number of commits to fetch')

    @staticmethod
    def get_default_branch(git_repo, repo_path):
        """리모트 저장소의 기본 브랜치 반환"""
        try:
            head_ref = subprocess.check_output(['git', '-C', repo_path, 'ls-remote', '--symref', 'origin', 'HEAD'],
                                               text=True)
            for line in head_ref.splitlines():
                if line.startswith('ref:'):
                    return line.split('refs/heads/')[1].split()[0]
        except subprocess.CalledProcessError:
            pass
        try:
            refs = subprocess.check_output(['git', '-C', repo_path, 'ls-remote', '--heads', 'origin'],
                                           text=True).splitlines()
            branches = [line.split('refs/heads/')[1] for line in refs if 'refs/heads/' in line]
            return branches[0] if branches else None
        except subprocess.CalledProcessError:
            return None

    @staticmethod
    def _is_safe_directory(repo_path):
        try:
            result = subprocess.run(['git', 'config', '--global', '--get-all', 'safe.directory'],
                                    capture_output=True, text=True)
            return repo_path in result.stdout.strip().splitlines()
        except subprocess.CalledProcessError:
            return False

    def check_repo(self, repo, git_repo, repo_path):
        if not git_repo.heads and not git_repo.remotes.origin.refs:  # 빈 저장소 확인
            self.stderr.write(self.style.WARNING(f"⚠️ Empty repository: {repo.slug}"))
            return False

        if not self._is_safe_directory(repo_path):  # safe.directory 확인 및 추가
            try:
                subprocess.run(['git', 'config', '--global', '--add', 'safe.directory', repo_path], check=True)
                self.stdout.write(self.style.SUCCESS(f"✅ safe.directory 등록됨: {repo_path}"))
            except subprocess.CalledProcessError as e:
                self.stderr.write(self.style.ERROR(f"❌ safe.directory 설정 실패: {e}"))
                return False

        try:
            remote_url = subprocess.check_output(['git', '-C', repo_path, 'config', '--get', 'remote.origin.url'],
                                                 text=True).strip()
            if remote_url != repo.remote_url:
                subprocess.run(['git', '-C', repo_path, 'remote', 'set-url', 'origin', repo.remote_url], check=True)
                self.stdout.write(f"Updated remote.origin.url to {repo.remote_url}")
        except subprocess.CalledProcessError:
            try:
                subprocess.run(['git', '-C', repo_path, 'remote', 'add', 'origin', repo.remote_url], check=True)
                self.stdout.write(f"Added remote.origin.url: {repo.remote_url}")
            except subprocess.CalledProcessError as e:
                self.stderr.write(self.style.ERROR(f"❌ Failed to set remote.origin: {e}"))
                return False

        try:  # remote.origin.fetch 확인 및 추가
            result = subprocess.run(['git', '-C', repo_path, 'config', '--get-all', 'remote.origin.fetch'],
                                    capture_output=True, text=True)
            fetch_rules = result.stdout.strip().splitlines()
            target_ref_spec = '+refs/heads/*:refs/remotes/origin/*'
            if target_ref_spec not in fetch_rules:
                subprocess.run(
                    ['git', '-C', repo_path, 'config', '--add', 'remote.origin.fetch', target_ref_spec], check=True)
                self.stdout.write(self.style.SUCCESS(f"✅ remote.origin.fetch 추가됨: {target_ref_spec}"))
            return True
        except subprocess.CalledProcessError as e:
            self.stderr.write(self.style.ERROR(f"❌ remote.origin.fetch 확인 실패: {e}"))
            return False

    def fetch_repo(self, repo_path):
        """Git 저장소 페치"""
        try:
            remote_url = subprocess.check_output(['git', '-C', repo_path, 'config', '--get', 'remote.origin.url'],
                                                 text=True).strip()
            self.stdout.write(f"Remote URL: {remote_url}")
        except subprocess.CalledProcessError:
            self.stderr.write(self.style.ERROR("No remote.origin.url configured"))
            return False
        for attempt in range(3):
            try:
                subprocess.run(['git', '-C', repo_path, 'fetch', '--all', '--prune', '--force'],
                               check=True, capture_output=True, text=True)
                subprocess.check_output(['git', '-C', repo_path, 'show-ref'], text=True).strip()
                return True
            except subprocess.CalledProcessError as e:
                self.stderr.write(f"Fetch attempt {attempt + 1} failed: {e.stderr}")
                if attempt == 2:
                    return False
                time.sleep(2)
        return False

    def sync_branches(self, git_repo, repo, repo_path):
        """로컬 브랜치와 원격 브랜치를 동기화"""
        try:
            default_branch = self.get_default_branch(git_repo, repo_path)
            if not default_branch:
                self.stderr.write(self.style.WARNING(f"No default branch found for {repo.slug}"))
                return

            # 원격 브랜치 목록
            remote_refs = git_repo.remotes.origin.refs if git_repo.remotes.origin.refs else []
            remote_branches = [ref.name.replace('origin/', '') for ref in remote_refs if ref.name != 'origin/HEAD']
            self.stdout.write(self.style.SUCCESS(f"Remote branches: {remote_branches}"))

            # 로컬 브랜치 업데이트
            for branch in remote_branches:
                try:
                    subprocess.run(
                        ['git', '-C', repo_path, 'update-ref', f'refs/heads/{branch}', f'refs/remotes/origin/{branch}'],
                        check=True)
                    self.stdout.write(self.style.SUCCESS(f"Updated local branch: {branch}"))
                except subprocess.CalledProcessError as e:
                    self.stderr.write(self.style.ERROR(f"Failed to update branch {branch}: {e}"))

            # 삭제된 로컬 브랜치 정리
            local_branches = [head.name for head in git_repo.heads if head.name != 'HEAD']
            for branch in local_branches:
                if branch not in remote_branches:
                    try:
                        cmd = ['git', '-C', repo_path, 'rev-list', branch, '--max-count=1']
                        last_commit = subprocess.check_output(cmd, text=True).strip()
                        if last_commit:
                            self.stdout.write(f"Branch {branch} has commits, preserving in DB")
                            continue
                    except subprocess.CalledProcessError:
                        pass
                    try:
                        subprocess.run(['git', '-C', repo_path, 'branch', '-D', branch], check=True)
                        self.stdout.write(self.style.SUCCESS(f"Deleted local branch: {branch}"))
                    except subprocess.CalledProcessError as e:
                        self.stderr.write(self.style.ERROR(f"Failed to delete branch {branch}: {e}"))

            # DB 동기화
            with transaction.atomic():
                existing_branches = set(repo.branches.values_list('name', flat=True))
                new_branch_names = [b for b in remote_branches if b not in existing_branches]
                if new_branch_names:
                    Branch.objects.bulk_create([Branch(repo=repo, name=name) for name in new_branch_names])
                    self.stdout.write(self.style.SUCCESS(f"Added {len(new_branch_names)} branches: {new_branch_names}"))
                deleted_branch_names = [b for b in existing_branches if b not in remote_branches]
                if deleted_branch_names:
                    branches_with_commits = set(
                        Commit.objects.filter(repo=repo, branches__name__in=deleted_branch_names)
                        .values_list('branches__name', flat=True))
                    deleted_branch_names = [b for b in deleted_branch_names if b not in branches_with_commits]
                    if deleted_branch_names:
                        Branch.objects.filter(repo=repo, name__in=deleted_branch_names).delete()
                        self.stdout.write(
                            self.style.SUCCESS(f"Deleted {len(deleted_branch_names)} branches: {deleted_branch_names}"))

            # Bare 저장소의 HEAD 및 origin/HEAD 설정
            try:
                if subprocess.check_output(['git', '-C', repo_path, 'show-ref',
                                            f'refs/heads/{default_branch}'], text=True).strip():
                    subprocess.run(['git', '-C', repo_path, 'symbolic-ref', 'HEAD',
                                    f'refs/heads/{default_branch}'], check=True)
                    self.stdout.write(self.style.SUCCESS(f"Set HEAD to refs/heads/{default_branch}"))
                else:
                    self.stderr.write(self.style.WARNING(f"Branch {default_branch} does not exist, skipping HEAD set"))
            except subprocess.CalledProcessError as e:
                self.stderr.write(self.style.ERROR(f"Failed to set HEAD: {e}"))

            try:
                subprocess.run(
                    ['git', '-C', repo_path, 'symbolic-ref', 'refs/remotes/origin/HEAD',
                     f'refs/remotes/origin/{default_branch}'], check=True)
                self.stdout.write(self.style.SUCCESS(f"Set origin/HEAD to {default_branch}"))
            except subprocess.CalledProcessError as e:
                self.stderr.write(self.style.ERROR(f"Failed to set origin/HEAD: {e}"))

        except (subprocess.CalledProcessError, GitCommandError, ValueError) as e:
            self.stderr.write(self.style.ERROR(f"Branch sync failed: {e}"))
            raise

    def ensure_commit_exists(self, repo, commit, commit_obj_map, existing_hashes, commits_to_create):
        """재귀적으로 커밋과 부모 커밋을 저장 준비"""
        if commit.hexsha in existing_hashes or commit.hexsha in commit_obj_map:
            return
        author = commit.author.name or "Unknown"
        seoul_tz = ZoneInfo("Asia/Seoul")
        date = datetime.fromtimestamp(commit.committed_date, tz=ZoneInfo("UTC")).astimezone(seoul_tz)
        commit_instance = Commit(
            repo=repo,
            commit_hash=commit.hexsha,
            author=author,
            date=date,
            message=commit.message.strip()
        )
        commits_to_create.append(commit_instance)
        commit_obj_map[commit.hexsha] = commit_instance
        for parent in commit.parents:
            self.ensure_commit_exists(repo, parent, commit_obj_map, existing_hashes, commits_to_create)

    def handle(self, *args, **kwargs):
        limit = kwargs.get('limit')
        base_repo_path = "/app/repos"

        for repo in Repository.objects.all():
            repo_path = repo.local_path or os.path.join(base_repo_path, f"{repo.slug}.git")

            if not os.path.isdir(repo_path):
                self.stderr.write(self.style.ERROR(f"Path not found: {repo_path}"))
                continue

            try:
                git_repo = Repo(repo_path)
            except InvalidGitRepositoryError:
                self.stderr.write(self.style.ERROR(f"Invalid Git repository: {repo_path}"))
                continue

            # 레파지토리 상태 확인 및 기본 설정
            if not self.check_repo(repo, git_repo, repo_path):
                continue

            # Git 페치
            if not self.fetch_repo(repo_path):
                self.stderr.write(self.style.ERROR(f"Git fetch failed for {repo.slug}"))
                continue

            with transaction.atomic():
                try:
                    self.sync_branches(git_repo, repo, repo_path)

                    # 브랜치-커밋 매핑
                    commit_branch_map = {}
                    try:
                        cmd = ['git', '-C', repo_path, 'for-each-ref', '--format=%(refname:short)', 'refs/heads']
                        branches = subprocess.check_output(cmd, text=True).strip().split('\n')
                        self.stdout.write(f"Found branches: {branches}")
                        for branch in branches:
                            if branch:
                                try:
                                    cmd = ['git', '-C', repo_path, 'rev-list', branch, '--']
                                    output = subprocess.check_output(cmd, text=True).strip()
                                    commit_hashes = output.split('\n')
                                    self.stdout.write(f"Branch {branch} has {len(commit_hashes)} commits")
                                    for commit_hash in commit_hashes:
                                        if commit_hash:
                                            commit_branch_map.setdefault(commit_hash, []).append(branch)
                                except subprocess.CalledProcessError as e:
                                    self.stderr.write(
                                        self.style.ERROR(f"Failed to get commits for branch {branch}: {e}"))
                        existing_branches = set(repo.branches.values_list('name', flat=True))
                        for branch_name in existing_branches:
                            if branch_name not in branches:
                                commit_hashes = Commit.objects.filter(repo=repo,
                                                                      branches__name=branch_name).values_list(
                                    'commit_hash', flat=True)
                                for commit_hash in commit_hashes:
                                    commit_branch_map.setdefault(commit_hash, []).append(branch_name)
                    except subprocess.CalledProcessError as e:
                        self.stderr.write(self.style.ERROR(f"Failed to map branches: {e}"))

                    # 커밋 및 부모 데이터 준비
                    existing_hashes = set(Commit.objects.filter(repo=repo).values_list('commit_hash', flat=True))
                    commits_to_create = []
                    commit_hashes = []
                    commit_parent_map = {}
                    commit_obj_map = {}

                    try:
                        commits_iter = git_repo.iter_commits('--all', max_count=limit)
                    except GitCommandError as e:
                        self.stderr.write(self.style.ERROR(f"Failed to get commits: {e}"))
                        continue

                    for commit in reversed(list(commits_iter)):  # 오래된 순으로
                        self.ensure_commit_exists(repo, commit, commit_obj_map, existing_hashes, commits_to_create)
                        commit_hashes.append((commit.hexsha, commit.message))
                        commit_parent_map[commit.hexsha] = [p.hexsha for p in commit.parents]

                    if commits_to_create:
                        try:
                            # Commit 저장
                            Commit.bulk_create_with_revision_ids(commits_to_create, ignore_conflicts=False)
                            self.stdout.write(self.style.SUCCESS(f"Created {len(commits_to_create)} commits"))
                        except IntegrityError as e:
                            self.stderr.write(self.style.WARNING(f"IntegrityError, retrying without duplicates: {e}"))
                            existing_hashes = set(
                                Commit.objects.filter(repo=repo).values_list('commit_hash', flat=True))
                            commits_to_create = [c for c in commits_to_create if c.commit_hash not in existing_hashes]
                            Commit.bulk_create_with_revision_ids(commits_to_create, ignore_conflicts=True)

                        # 저장된 커밋 조회
                        saved_commits = Commit.objects.filter(
                            repo=repo, commit_hash__in=[c.commit_hash for c in commits_to_create])
                        commit_obj_map = {c.commit_hash: c for c in saved_commits}

                        # 부모 관계 연결
                        parent_relations = []
                        for child_hash, parent_hashes in commit_parent_map.items():
                            child = commit_obj_map.get(child_hash)
                            if not child:
                                continue
                            for p_hash in parent_hashes:
                                parent = commit_obj_map.get(p_hash)
                                if parent and parent != child:
                                    parent_relations.append(
                                        Commit.parents.through(from_commit_id=child.id, to_commit_id=parent.id))
                        Commit.parents.through.objects.bulk_create(parent_relations, ignore_conflicts=True)
                        self.stdout.write(self.style.SUCCESS("Linked parent relationships"))

                        # 브랜치 연결
                        branch_map = {b.name: b for b in repo.branches.all().select_related('repo')}
                        for commit_hash, commit_obj in commit_obj_map.items():
                            branch_names = commit_branch_map.get(commit_hash, [])
                            branch_objs = [branch_map.get(name) for name in branch_names if name in branch_map]
                            branch_objs = [b for b in branch_objs if b]
                            if branch_objs:
                                commit_obj.branches.add(*branch_objs)
                                self.stdout.write(self.style.SUCCESS(
                                    f"Linked {len(branch_objs)} branches to commit {commit_hash}: {branch_names}"))

                        # 이슈 연결
                        for commit_hash, message in commit_hashes:
                            if commit_hash not in commit_obj_map:
                                continue
                            issue_numbers = re.findall(r'#(\d+)\b', message)
                            if issue_numbers:
                                valid_issues = Issue.objects.filter(pk__in=issue_numbers)
                                if valid_issues.exists():
                                    commit_obj_map[commit_hash].issues.add(*valid_issues)
                                    self.stdout.write(self.style.SUCCESS(
                                        f"Linked {len(valid_issues)} issues to commit {commit_hash}"))

                        # 시퀀스 조정
                        with connection.cursor() as cursor:
                            cursor.execute(
                                "SELECT setval('work_commit_id_seq', (SELECT COALESCE(MAX(id), 0) + 1 FROM work_commit))")
                            self.stdout.write(self.style.SUCCESS("Sequence adjusted for work_commit_id_seq"))

                    else:
                        self.stdout.write(self.style.WARNING(f"No new commits to create for {repo.slug}"))

                    self.stdout.write(self.style.SUCCESS(
                        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                        f"Processed {repo.slug} ({len(commits_to_create)} new commits)"))

                except (subprocess.CalledProcessError, GitCommandError, ValueError) as e:
                    self.stderr.write(self.style.ERROR(f"Repository sync failed: {e}"))
                    continue
