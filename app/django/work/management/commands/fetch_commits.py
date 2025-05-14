import re
import time
from datetime import datetime

import requests
from django.core.management.base import BaseCommand
from django.db import transaction

from work.models import Repository, Commit, Issue


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        for repo in Repository.objects.all():
            commits_data = self.fetch_commits(f"{repo.github_api_url}/commits", repo.github_token)
            if not commits_data:
                continue

            commits_to_create = []
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

                    existing_hashes = set(Commit.objects.filter(repo=repo).values_list('commit_hash', flat=True))
                    if commit_hash not in existing_hashes:
                        commit = Commit(
                            repo=repo,
                            commit_hash=commit_hash,
                            author=author,
                            date=date,
                            message=message
                        )
                        commits_to_create.append((commit, message))
                except (KeyError, ValueError) as e:
                    self.stderr.write(self.style.WARNING(f"Invalid commit data: {e}"))
                    continue

            if commits_to_create:
                with transaction.atomic():
                    try:
                        Commit.objects.bulk_create(commits_to_create, ignore_conflicts=True)
                    except Exception as e:
                        self.stderr.write(self.style.ERROR(f"Bulk create failed: {e}"))
                    for commit, message in commits_to_create:
                        issue_numbers = re.findall(r'#(\d+)', message)
                        issue_ids = [int(num) for num in issue_numbers]
                        valid_issues = Issue.objects.filter(pk__in=issue_ids, repo=repo)
                        if valid_issues:
                            commit.issues.set(valid_issues)

            self.stdout.write(
                self.style.SUCCESS(
                    f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                    f"Fetched {len(commits_to_create)} new commits from {repo.github_api_url}"
                ))

    def fetch_commits(self, api_url, token=None):
        commits_data = []
        page = 1
        headers = {'Authorization': f'token {token}'}
        while True:
            try:
                response = requests.get(api_url, headers=headers, params={'page': page, 'per_page': 100})
                response.raise_for_status()
                page_data = response.json()
                if not page_data:
                    break
                commits_data.extend(page_data)
                page += 1
                # 요청 제한 로깅
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
        self.stdout.write(self.style.NOTICE(f"Retrieved {len(commits_data)} commits from {api_url}"))
        return commits_data
