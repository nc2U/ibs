import re
import time
from datetime import datetime

import requests
from django.core.management.base import BaseCommand
from django.db import transaction

from work.models import Repository, Commit, Issue


class Command(BaseCommand):
    help = "Fetch commits from GitHub repositories"

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit the number of commits to fetch (default: fetch all)',
        )

    def handle(self, *args, **kwargs):
        limit = kwargs.get('limit')  # 명령줄에서 --limit으로 전달된 값
        for repo in Repository.objects.all():
            commits_data = self.fetch_commits(f"{repo.github_api_url}/commits", repo.github_token, limit=limit)
            if not commits_data:
                self.stdout.write(self.style.WARNING(f"No commits retrieved from {repo.github_api_url}"))
                continue

            commits_to_create = []
            commit_hashes = []
            existing_hashes = set(Commit.objects.filter(repo=repo).values_list('commit_hash', flat=True))
            for item in commits_data:
                try:
                    commit_hash = item['sha']
                    author = item['commit']['author'].get('name', 'Unknown')
                    date_str = item['commit']['author'].get('date')
                    message = item['commit'].get('message', '')
                    if not all([commit_hash, author, date_str, message is not None]):
                        self.stderr.write(self.style.WARNING(f"Skipping invalid commit data: {item}"))
                        continue
                    date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    if commit_hash not in existing_hashes:
                        commit = Commit(
                            repo=repo,
                            commit_hash=commit_hash,
                            author=author,
                            date=date,
                            message=message
                        )
                        commits_to_create.append(commit)
                        commit_hashes.append((commit_hash, message))
                except (KeyError, ValueError) as e:
                    self.stderr.write(self.style.WARNING(f"Invalid commit data: {e}"))
                    continue

            if commits_to_create:
                with transaction.atomic():
                    try:
                        Commit.objects.bulk_create(commits_to_create, ignore_conflicts=True)
                        self.stdout.write(self.style.SUCCESS(f"Created {len(commits_to_create)} commits"))
                        # 저장된 커밋 재조회
                        saved_commits = Commit.objects.filter(
                            repo=repo,
                            commit_hash__in=[c.commit_hash for c in commits_to_create])
                        commit_map = {c.commit_hash: c for c in saved_commits}
                        for commit_hash, message in commit_hashes:
                            commit = commit_map.get(commit_hash)
                            if not commit:
                                self.stderr.write(
                                    self.style.WARNING(f"Commit {commit_hash} was not saved (possibly ignored)"))
                                continue
                            issue_numbers = re.findall(r'#(\d+)', message)
                            try:
                                valid_issues = Issue.objects.filter(pk__in=issue_numbers)
                            except AttributeError:
                                self.stderr.write(
                                    self.style.WARNING(f"No project linked to repository {repo.github_api_url}"))
                                continue
                            if valid_issues:
                                commit.issues.set(valid_issues)
                                self.stdout.write(
                                    self.style.WARNING(f"Linked {len(valid_issues)} issues to commit {commit_hash}"))
                    except Exception as e:
                        self.stderr.write(self.style.ERROR(f"Bulk create failed: {e}"))
                        raise
            else:
                self.stdout.write(self.style.WARNING(f"No new commits to create for {repo.github_api_url}"))

            self.stdout.write(
                self.style.SUCCESS(
                    f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                    f"Fetched {len(commits_to_create)} new commits from {repo.github_api_url}"
                ))

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
        self.stdout.write(self.style.WARNING(f"Retrieved {len(commits_data)} commits from {api_url}"))
        return commits_data
