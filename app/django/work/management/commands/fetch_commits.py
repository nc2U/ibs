import gc
import os
import re
import subprocess
import time
from collections import deque
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
    def get_default_branch(repo_path):
        """리모트 저장소의 기본 브랜치 반환"""
        try:
            head_ref = subprocess.check_output(
                ['git', '-C', repo_path, 'ls-remote', '--symref', 'origin', 'HEAD'], text=True)
            for line in head_ref.splitlines():
                if line.startswith('ref:'):
                    return line.split('refs/heads/')[1].split()[0]
        except subprocess.CalledProcessError as e:
            print(f"CalledProcessError : {e}")
        try:
            refs = subprocess.check_output(
                ['git', '-C', repo_path, 'ls-remote', '--heads', 'origin'], text=True).splitlines()
            branches = [line.split('refs/heads/')[1] for line in refs if 'refs/heads/' in line]
            return branches[0] if branches else None
        except subprocess.CalledProcessError:
            return None

    def check_repo(self, repo, git_repo, repo_path):
        if not git_repo.heads and not git_repo.remotes.origin.refs:  # 빈 저장소 확인
            self.stderr.write(self.style.WARNING(f"⚠️ Empty repository: {repo.slug}"))
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

        lock_file = f"{repo_path}/.git/lock"
        for attempt in range(3):
            if not os.path.exists(lock_file):
                try:
                    process = subprocess.Popen(
                        ['git', '-C', repo_path, 'fetch', '--all', '--prune', '--force'],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    stdout, stderr = process.communicate(timeout=300)  # 5분 타임아웃

                    if process.returncode != 0:
                        raise subprocess.CalledProcessError(process.returncode, process.args, stderr=stderr)

                    subprocess.check_output(['git', '-C', repo_path, 'show-ref'], text=True).strip()
                    # 추가: 저장소 새로고침 확인
                    subprocess.run(['git', '-C', repo_path, 'fetch', '--all'], check=True, text=True)
                    return True
                except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
                    self.stderr.write(self.style.ERROR(f"Fetch attempt {attempt + 1} failed: {str(e)}"))
                    if attempt == 2:
                        return False
                    time.sleep(2)
        return False

    def sync_branches(self, git_repo, repo, repo_path):
        """로컬 브랜치와 원격 브랜치를 동기화"""
        try:
            default_branch = self.get_default_branch(repo_path)
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

    def collect_commits_bfs(self, repo, git_repo, root_commits, existing_hashes, repo_path):
        """큐 기반(BFS)으로 커밋과 부모 커밋을 저장 준비"""
        commit_obj_map = {}
        commits_to_create = []
        commit_parent_map = {}
        visited = set()
        queue = deque(root_commits)
        max_queue_size = 100000
        start_time = time.time()
        max_runtime = 600  # 10분

        while queue:
            if len(queue) > max_queue_size:
                self.stderr.write(self.style.ERROR(f"Queue size exceeded: {len(queue)}"))
                break
            if time.time() - start_time > max_runtime:
                self.stderr.write(self.style.ERROR(f"Processing timeout"))
                break
            if len(visited) % 1000 == 0:
                gc.collect()
                self.stdout.write(f"Processed {len(visited)} commits, Queue size: {len(queue)}")

            commit = queue.popleft()
            if commit.hexsha in visited or commit.hexsha in existing_hashes:
                continue
            visited.add(commit.hexsha)

            try:
                output = subprocess.check_output(['git', '-C', repo_path, 'cat-file', '-p', commit.hexsha], text=True)
                author = "Unknown"
                date = None
                message = ""
                parent_hashes = []
                for line in output.splitlines():
                    if line.startswith("author"):
                        author = line.split(" ", 1)[1].rsplit('<')[0].strip()
                    elif line.startswith("committer"):
                        timestamp = int(line.rsplit(" ", 2)[1])
                        seoul_tz = ZoneInfo("Asia/Seoul")
                        date = datetime.fromtimestamp(timestamp, tz=ZoneInfo("UTC")).astimezone(seoul_tz)
                    elif line.startswith("parent"):
                        parent_hashes.append(line.split()[1])
                    elif not line.startswith("tree"):
                        message += line + "\n"
                commit_instance = Commit(
                    repo=repo,
                    commit_hash=commit.hexsha,
                    author=author,
                    date=date,
                    message=message.strip()
                )
                commits_to_create.append(commit_instance)
                commit_obj_map[commit.hexsha] = commit_instance
                commit_parent_map[commit.hexsha] = parent_hashes
                for parent_hash in parent_hashes:
                    if parent_hash not in visited and parent_hash not in existing_hashes:
                        parent_commit = git_repo.commit(parent_hash)
                        queue.append(parent_commit)
            except subprocess.CalledProcessError as e:
                self.stderr.write(self.style.ERROR(f"Failed to process commit {commit.hexsha}: {e}"))
                continue

        commits_to_create = sorted(commits_to_create, key=lambda c: c.date)
        return commits_to_create, commit_obj_map, commit_parent_map

    def handle(self, *args, **kwargs):
        with connection.cursor() as cursor:
            cursor.execute('''SELECT pg_advisory_lock(12345)''')  # 고유 락 ID

            try:
                limit = kwargs.get('limit')
                base_repo_path = "/app/repos"

                for repo in Repository.objects.all():
                    with transaction.atomic():
                        repo_path = repo.local_path or os.path.join(base_repo_path, f"{repo.slug}.git")

                        if not os.path.isdir(repo_path):  # 저장소 경로 등록 확인
                            self.stderr.write(self.style.ERROR(f"Path not found: {repo_path}"))
                            continue

                        try:  # git 저장소 확인
                            git_repo = Repo(repo_path)
                        except InvalidGitRepositoryError:
                            self.stderr.write(self.style.ERROR(f"Invalid Git repository: {repo_path}"))
                            continue

                        # 레파지토리 상태 확인 및 기본 설정
                        if not self.check_repo(repo, git_repo, repo_path):
                            self.stderr.write(self.style.ERROR(f"Check repository failed for {repo.slug}"))
                            continue

                        # Git 페치
                        if not self.fetch_repo(repo_path):
                            self.stderr.write(self.style.ERROR(f"Git fetch failed for {repo.slug}"))
                            continue

                        try:
                            # default branch & origin branches -> local branches sync!
                            self.sync_branches(git_repo, repo, repo_path)

                            # 브랜치-커밋 매핑
                            commit_branch_map = {}
                            try:
                                cmd = ['git', '-C', repo_path, 'for-each-ref', '--format=%(refname:short)',
                                       'refs/heads']
                                branches = subprocess.check_output(cmd, text=True, timeout=300).strip().split('\n')
                                branches = [b for b in branches if b]
                                self.stdout.write(f"Found branches: {branches}")

                                if not branches:
                                    self.stderr.write(self.style.WARNING(f"No branches found for {repo.slug}"))
                                    continue

                                for branch in branches:
                                    try:
                                        cmd = ['git', '-C', repo_path, 'rev-list', branch]
                                        output = subprocess.check_output(cmd, text=True, timeout=300).strip()
                                        commit_hashes = output.split('\n')
                                        self.stdout.write(f"Branch {branch} has {len(commit_hashes)} commits")

                                        for commit_hash in commit_hashes:
                                            commit_branch_map.setdefault(commit_hash, []).append(branch)
                                    except subprocess.CalledProcessError as e:
                                        self.stderr.write(
                                            self.style.ERROR(f"Failed to get commits for branch {branch}: {e}"))

                                existing_branches = set(repo.branches.values_list('name', flat=True))
                                for branch_name in existing_branches:
                                    if branch_name not in branches:
                                        commit_hashes = Commit.objects.filter(
                                            repo=repo, branches__name=branch_name).values_list('commit_hash', flat=True)
                                        for commit_hash in commit_hashes:
                                            commit_branch_map.setdefault(commit_hash, []).append(branch_name)

                            except subprocess.CalledProcessError as e:
                                self.stderr.write(self.style.ERROR(f"Failed to map branches: {e}"))

                            # 커밋 및 부모 데이터 준비
                            existing_hashes = set(
                                Commit.objects.filter(repo=repo).values_list('commit_hash', flat=True))

                            try:
                                root_commits = [ref.commit for ref in git_repo.remotes.origin.refs if
                                                ref.name != 'origin/HEAD']
                                commits_to_create, commit_obj_map, commit_parent_map = \
                                    self.collect_commits_bfs(repo, git_repo, root_commits, existing_hashes, repo_path)
                                commits_iter = git_repo.iter_commits('--all', max_count=limit)
                                commit_hashes = [(commit.hexsha, commit.message) for commit in commits_iter]
                            except GitCommandError as e:
                                self.stderr.write(self.style.ERROR(f"Failed to get commits: {e}"))
                                continue

                            self.stdout.write(
                                self.style.SUCCESS(f"커밋(create) 수 : {len(commits_to_create)} -> commits_to_create!!"))
                            self.stdout.write(
                                self.style.SUCCESS(f"커밋(obj) 수 : {len(commit_obj_map)} -> commit_obj_map!!"))
                            self.stdout.write(self.style.SUCCESS(f"커밋 부모 맵 수 : {len(commit_parent_map)}"))
                            self.stdout.write(self.style.SUCCESS(f"커밋 브랜치 맵 수 : {len(commit_branch_map)}"))
                            branch_map = {b.name: b for b in repo.branches.all()}
                            self.stdout.write(self.style.SUCCESS(f"브랜치 맵 수 : {len(branch_map)}"))

                            if commits_to_create:
                                try:  # Commit 저장
                                    Commit.objects.bulk_create(commits_to_create, ignore_conflicts=False)
                                    self.stdout.write(self.style.SUCCESS(f"Created {len(commits_to_create)} commits"))
                                except IntegrityError as e:
                                    self.stderr.write(
                                        self.style.WARNING(f"IntegrityError, retrying without duplicates: {e}"))
                                    existing_hashes = set(
                                        Commit.objects.filter(repo=repo).values_list('commit_hash', flat=True))
                                    commits_to_create = [c for c in commits_to_create if
                                                         c.commit_hash not in existing_hashes]
                                    Commit.objects.bulk_create(commits_to_create, ignore_conflicts=True)

                                # parent 관계에 필요한 모든 커밋을 대상으로 조회 (child + parent)
                                hashes = set(commit_parent_map.keys()) | {h for hs in commit_parent_map.values() for h
                                                                          in hs}
                                saved_commits = Commit.objects.filter(repo=repo, commit_hash__in=hashes)
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
                                self.stdout.write(
                                    self.style.SUCCESS(f"Linked {len(commit_parent_map)} parent relationships"))

                                # 브랜치 연결
                                for commit_hash, commit_obj in commit_obj_map.items():
                                    branch_names = commit_branch_map.get(commit_hash, [])
                                    branch_objs = [branch_map.get(name) for name in branch_names if name in branch_map]
                                    branch_objs = [b for b in branch_objs if b]
                                    if branch_objs:
                                        commit_obj.branches.add(*branch_objs)
                                        if len(commit_obj_map) < 100:
                                            self.stdout.write(self.style.SUCCESS(
                                                f"Linked {len(branch_objs)} branches to commit {commit_hash}: {branch_names}"))

                                self.stdout.write(
                                    self.style.SUCCESS(f"Linked branches to {len(commit_obj_map)} commits Complete!"))

                                # 이슈 연결
                                for commit_hash, message in commit_hashes:
                                    if commit_hash not in commit_obj_map:
                                        continue
                                    issue_numbers = re.findall(r'#(\d+)\b', message)
                                    if issue_numbers:
                                        valid_issues = Issue.objects.filter(pk__in=issue_numbers)
                                        if valid_issues.exists():
                                            commit_obj_map[commit_hash].issues.add(*valid_issues)
                                            if len(commit_hashes) < 100:
                                                self.stdout.write(self.style.SUCCESS(
                                                    f"Linked {len(valid_issues)} issues to commit {commit_hash}"))

                                self.stdout.write(self.style.SUCCESS(
                                    f"Linked issues to {len(commit_hashes)} commits Complete!"))
                            else:
                                self.stdout.write(self.style.WARNING(f"No new commits to create for {repo.slug}"))

                            self.stdout.write(self.style.SUCCESS(
                                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Processed {repo.slug} ({len(commits_to_create)} new commits)"))
                        except (subprocess.CalledProcessError, GitCommandError, ValueError) as e:
                            self.stderr.write(self.style.ERROR(f"Repository sync failed: {e}"))
                            continue
                # 시퀀스 조정
                cursor.execute(
                    "SELECT setval('work_commit_id_seq', (SELECT COALESCE(MAX(id), 0) + 1 FROM work_commit))")
                self.stdout.write(self.style.SUCCESS("Sequence adjusted for work_commit_id_seq"))
            finally:
                cursor.execute('''SELECT pg_advisory_unlock(12345)''')
