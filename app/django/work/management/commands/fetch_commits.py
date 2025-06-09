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

    def sync_branches(self, git_repo, repo, repo_path):
        """로컬 브랜치와 원격 브랜치를 동기화"""
        try:
            # 원격 브랜치 목록
            remote_refs = git_repo.remotes.origin.refs
            self.stdout.write(f"Remote refs: {[ref.name for ref in remote_refs]}")
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
                        subprocess.run(['git', '-C', repo_path, 'branch', '-D', branch], check=True)
                        self.stdout.write(self.style.SUCCESS(f"Deleted local branch: {branch}"))
                    except subprocess.CalledProcessError as e:
                        self.stderr.write(self.style.ERROR(f"Failed to delete branch {branch}: {e}"))

            # DB 동기화
            existing_branches = set(repo.branches.values_list('name', flat=True))
            new_branch_names = [b for b in remote_branches if b not in existing_branches]
            if new_branch_names:
                Branch.objects.bulk_create([Branch(repo=repo, name=name) for name in new_branch_names])
                self.stdout.write(self.style.SUCCESS(f"Added {len(new_branch_names)} branches: {new_branch_names}"))
            deleted_branch_names = [b for b in existing_branches if b not in remote_branches]
            if deleted_branch_names:
                try:
                    Branch.objects.filter(repo=repo, name__in=deleted_branch_names).delete()
                    self.stdout.write(
                        self.style.SUCCESS(f"Deleted {len(deleted_branch_names)} branches: {deleted_branch_names}"))
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"Failed to delete DB branches: {e}"))

            # Bare 저장소의 HEAD 설정
            default_branch = next((ref for ref in remote_refs if ref.name in ['origin/main', 'origin/master']), None)
            if default_branch:
                default_branch_name = default_branch.name.replace('origin/', '')
                subprocess.run(['git', '-C', repo_path, 'symbolic-ref', 'HEAD', f'refs/heads/{default_branch_name}'],
                               check=True)
                self.stdout.write(self.style.SUCCESS(f"Set HEAD to refs/heads/{default_branch_name}"))
            else:
                self.stderr.write(self.style.WARNING("No default branch (main/master) found"))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Branch sync failed: {e}"))
            raise

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

            try:
                # 안전 디렉토리 설정
                subprocess.run(['git', 'config', '--global', '--add', 'safe.directory', repo_path], check=True)
                self.stdout.write(self.style.SUCCESS("Safe directory 설정 완료"))
            except subprocess.CalledProcessError as e:
                self.stderr.write(self.style.ERROR(f"Safe directory 설정 실패: {e}"))

            try:
                for attempt in range(3):
                    try:
                        subprocess.run(['git', '-C', repo_path, 'fetch', '--all', '--prune', '--force'], check=True)
                        subprocess.run(['git', '-C', repo_path, 'remote', 'set-head', 'origin', '--auto'], check=True)
                        self.stdout.write(self.style.SUCCESS(f"Synced with origin for {repo.slug}"))
                        break
                    except subprocess.CalledProcessError as e:
                        if attempt == 2:
                            self.stderr.write(self.style.ERROR(f"Git sync failed for {repo.slug}: {e}"))
                            continue
                        time.sleep(2)

                self.sync_branches(git_repo, repo, repo_path)
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Git operations failed: {e}"))
                continue

            # 브랜치-커밋 매핑
            commit_branch_map = {}
            try:
                # git for-each-ref로 브랜치별 HEAD 커밋 조회
                cmd = ['git', '-C', repo_path, 'for-each-ref', '--format=%(refname:short) %(objectname)', 'refs/heads']
                output = subprocess.check_output(cmd, text=True).strip()
                for line in output.split('\n'):
                    if line:
                        branch_name, commit_hash = line.split()
                        if commit_hash not in commit_branch_map:
                            commit_branch_map[commit_hash] = []
                        commit_branch_map[commit_hash].append(branch_name)
                # 히스토리 탐색으로 추가 커밋 매핑
                for branch in repo.branches.all():
                    branch_name = branch.name
                    cmd = ['git', '-C', repo_path, 'log', f'refs/heads/{branch_name}', '--format=%H']
                    if limit is not None:
                        cmd.append(f'--max-count={limit}')
                    try:
                        output = subprocess.check_output(cmd, text=True).strip()
                        if output:
                            commit_hashes = output.split('\n')
                            for commit_hash in commit_hashes:
                                if commit_hash not in commit_branch_map:
                                    commit_branch_map[commit_hash] = []
                                if branch_name not in commit_branch_map[commit_hash]:
                                    commit_branch_map[commit_hash].append(branch_name)
                    except subprocess.CalledProcessError as e:
                        self.stderr.write(self.style.ERROR(f"Failed to get commits for branch {branch_name}: {e}"))
            except subprocess.CalledProcessError as e:
                self.stderr.write(self.style.ERROR(f"Failed to map branches: {e}"))

            # 커밋 및 부모 데이터 준비
            existing_hashes = set(Commit.objects.filter(repo=repo).values_list('commit_hash', flat=True))
            commits_to_create = []
            commit_hashes = []
            commit_parent_map = {}
            commit_obj_map = {}

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

            for commit in reversed(list(commits_iter)):  # 오래된 순으로
                self.ensure_commit_exists(repo, commit, commit_obj_map, existing_hashes, commits_to_create)
                commit_hashes.append((commit.hexsha, commit.message))
                commit_parent_map[commit.hexsha] = [p.hexsha for p in commit.parents]

            if commits_to_create:
                with transaction.atomic():
                    try:
                        # 1차: Commit 저장
                        Commit.bulk_create_with_revision_ids(commits_to_create, ignore_conflicts=True)
                        self.stdout.write(self.style.SUCCESS(f"Created {len(commits_to_create)} commits"))

                        # 저장된 커밋 조회
                        saved_commits = Commit.objects.filter(
                            repo=repo,
                            commit_hash__in=[c.commit_hash for c in commits_to_create]
                        )
                        commit_obj_map = {c.commit_hash: c for c in saved_commits}

                        # 2차: parents 관계 연결
                        with connection.cursor() as cursor:
                            for child_hash, parent_hashes in commit_parent_map.items():
                                child = commit_obj_map.get(child_hash)
                                if not child:
                                    continue
                                for p_hash in parent_hashes:
                                    parent = commit_obj_map.get(p_hash)
                                    if parent and parent != child:  # 순환 방지
                                        cursor.execute(
                                            "INSERT INTO work_commit_parents (from_commit_id, to_commit_id) "
                                            "VALUES (%s, %s) ON CONFLICT DO NOTHING",
                                            [child.id, parent.id]
                                        )
                        self.stdout.write(self.style.SUCCESS("Linked parent relationships"))

                        # 3차: 브랜치 연결
                        branch_map = {b.name: b for b in repo.branches.all()}
                        for commit_hash, commit_obj in commit_obj_map.items():
                            branch_names = commit_branch_map.get(commit_hash, [])
                            branch_objs = [branch_map.get(name) for name in branch_names if name in branch_map]
                            branch_objs = [b for b in branch_objs if b]
                            if branch_objs:
                                commit_obj.branches.add(*branch_objs)
                                self.stdout.write(self.style.SUCCESS(
                                    f"Linked {len(branch_objs)} branches to commit {commit_hash}: {branch_names}"))

                        # 4차: 이슈 연결
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

                    except IntegrityError as e:
                        self.stderr.write(self.style.ERROR(f"Bulk create failed: {e}"))
                        raise
            else:
                self.stdout.write(self.style.WARNING(f"No new commits to create for {repo.slug}"))

            self.stdout.write(
                self.style.SUCCESS(
                    f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                    f"Processed {repo.slug} ({len(commits_to_create)} new commits)"))
