import requests
from datetime import datetime

from django.core.management.base import BaseCommand

from work.models import Repository, Commit


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        for repo in Repository.objects.all():
            try:
                api_url = f"{repo.github_api_url}/commits"  # e.g. https://api.github.com/repos/org/repo/commits
                response = requests.get(api_url)
                response.raise_for_status()
                commits_data = response.json()
            except requests.RequestException as e:
                self.stderr.write(self.style.ERROR(f"GitHub API request failed for {repo.github_api_url}: {e}"))
                continue

            commits_to_create = []
            for item in commits_data:
                try:
                    commit_hash = item['sha']
                    author = item['commit']['author']['name']
                    date_str = item['commit']['author']['date']
                    message = item['commit']['message']

                    if not all([commit_hash, author, date_str, message is not None]):
                        self.stderr.write(self.style.WARNING(f"Skipping invalid commit data: {item}"))
                        continue

                    date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    if not Commit.objects.filter(repo=repo, commit_hash=commit_hash).exists():
                        commits_to_create.append(Commit(
                            repo=repo,
                            commit_hash=commit_hash,
                            author=author,
                            date=date,
                            message=message
                        ))
                except (KeyError, ValueError) as e:
                    self.stderr.write(self.style.WARNING(f"Invalid commit data: {e}"))
                    continue

            Commit.objects.bulk_create(commits_to_create, ignore_conflicts=True)
            self.stdout.write(
                self.style.SUCCESS(f"Fetched {len(commits_to_create)} new commits from {repo.github_api_url}"))
