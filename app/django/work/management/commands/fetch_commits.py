import re
import time
from datetime import datetime

import requests
from django.core.management.base import BaseCommand
from django.db import transaction, connection, IntegrityError

from work.models import Repository, Commit, Issue


class Command(BaseCommand):
    help = "Fetch commits from GitHub repositories"

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=None, help='Limit the number of commits to fetch')

    def handle(self, *args, **kwargs):
        limit = kwargs.get('limit')  # 명령줄에서 --limit으로 전달된 값
        api_url = "https://api.github.com/repos"

        for repo in Repository.objects.all():
            api_url = f'{api_url}/{repo.owner}/{repo.slug}'
            commits_data = self.fetch_commits(api_url=f"{api_url}/commits",
                                              token=repo.github_token,
                                              limit=limit)
            if not commits_data:
                self.stdout.write(self.style.WARNING(f"No commits retrieved from {api_url}"))
                continue

            commit_hashes = []
            commits_to_create = []

            # DB에서 기존 해시들을 가져와서 set 으로 저장
            existing_hashes = set(Commit.objects.filter(repo=repo).values_list('commit_hash', flat=True))

            for item in commits_data:
                try:
                    commit_hash = item['sha']
                    commit_data = item.get('commit', {})
                    author = commit_data.get('author', {}).get('name', 'Unknown')
                    date_str = commit_data.get('author', {}).get('date')
                    message = commit_data.get('message', '')

                    if not all([commit_hash, author, date_str]):  # 필수 항목 누락 검사
                        self.stderr.write(self.style.WARNING(f"Skipping invalid commit data: {item}"))
                        continue

                    if commit_hash in existing_hashes:  # 중복 커밋 해시 검사
                        self.stderr.write(self.style.WARNING(f"Skipping existing commit {commit_hash}"))
                        continue

                    date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))  # 커밋 객체 생성
                    commits_to_create.append(Commit(
                        repo=repo,
                        commit_hash=commit_hash,
                        author=author,
                        date=date,
                        message=message))
                    commit_hashes.append((commit_hash, message))

                except (KeyError, ValueError) as e:
                    self.stderr.write(self.style.WARNING(f"Invalid commit data: {e}"))
                    continue

            if commits_to_create:
                with transaction.atomic():
                    try:
                        Commit.objects.bulk_create(commits_to_create, ignore_conflicts=True)
                        self.stdout.write(self.style.SUCCESS(f"Created {len(commits_to_create)} commits"))
                        # 이슈 연결을 위해 저장된 커밋 확인
                        saved_hashes = set(Commit.objects.filter(
                            repo=repo,
                            commit_hash__in=[c.commit_hash for c in commits_to_create]
                        ).values_list('commit_hash', flat=True))
                        for commit_hash, message in commit_hashes:
                            if commit_hash not in saved_hashes:
                                self.stderr.write(self.style.WARNING(f"Commit {commit_hash} was not saved"))
                                continue
                            issue_numbers = re.findall(r'#(\d+)', message)
                            if issue_numbers:
                                try:
                                    valid_issues = Issue.objects.filter(project=repo.project, pk__in=issue_numbers)
                                    if valid_issues:
                                        commit = Commit.objects.get(commit_hash=commit_hash)
                                        commit.issues.add(*valid_issues)  # 벌크로 이슈 추가
                                        self.stdout.write(self.style.WARNING(
                                            f"Linked {len(valid_issues)} issues to commit {commit_hash}"))
                                except AttributeError:
                                    self.stderr.write(
                                        self.style.WARNING(f"No project linked to repository {api_url}"))
                                    continue
                    except IntegrityError as e:
                        self.stderr.write(self.style.ERROR(f"Bulk create failed: {e}"))
                        raise
            else:
                self.stdout.write(self.style.WARNING(f"No new commits to create for {api_url}"))

            self.stdout.write(
                self.style.SUCCESS(
                    f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                    f"Fetched {len(commits_to_create)} new commits from {api_url}"))

    def fetch_commits(self, api_url, token=None, limit=None):
        commits_data = []
        page = 1
        headers = {'Authorization': f'token {token}'}
        # limit이 None이 아니면 per_page를 limit과 100 중 작은 값으로 설정
        per_page = min(limit, 100) if limit is not None else 100

        while True:
            try:
                response = requests.get(api_url, headers=headers, params={'page': page, 'per_page': per_page})
                response.raise_for_status()
                page_data = response.json()
                if not page_data:
                    break
                commits_data.extend(page_data)
                # limit이 설정된 경우, 필요한 만큼만 유지하고 종료
                if limit is not None and len(commits_data) >= limit:
                    commits_data = commits_data[:limit]
                    break
                page += 1
                remaining = response.headers.get('X-RateLimit-Remaining')
                if remaining and int(remaining) < 100:
                    reset = datetime.fromtimestamp(int(response.headers.get('X-RateLimit-Reset', 0)))
                    self.stdout.write(self.style.WARNING(f"Rate limit low: {remaining} remaining, resets at {reset}"))
            except requests.HTTPError as e:
                if e.response.status_code == 403 and 'rate limit exceeded' in str(e):
                    reset_time = int(e.response.headers.get('X-RateLimit-Reset', 0))
                    wait_seconds = max(reset_time - int(time.time()), 0) + 5
                    self.stdout.write(self.style.WARNING(f"Rate limit exceeded, waiting {wait_seconds} seconds"))
                    time.sleep(wait_seconds)
                    continue
                self.stderr.write(self.style.ERROR(f"GitHub API page {page} request failed for {api_url}: {e}"))
                return commits_data
            except requests.RequestException as e:
                self.stderr.write(self.style.ERROR(f"GitHub API page {page} request failed for {api_url}: {e}"))
                return commits_data

        commits_data = sorted(commits_data, key=lambda x: x['commit']['committer']['date'])  # 오래된 순서로 정렬
        self.stdout.write(self.style.WARNING(f"Retrieved {len(commits_data)} commits from {api_url}"))
        return commits_data
