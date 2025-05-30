import os
import re
from datetime import datetime

from zoneinfo import ZoneInfo
from django.core.management.base import BaseCommand
from django.db import transaction, IntegrityError
from django.utils.timezone import make_aware
from git import Repo, GitCommandError, InvalidGitRepositoryError

from work.models import Repository, Commit, Issue


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

                # ensure fetch refspec exists
                try:
                    fetch_specs = git_repo.remote('origin').config_reader.get_value("fetch", None)
                except Exception:
                    fetch_specs = None

                if not fetch_specs:
                    git_repo.git.config('--add', 'remote.origin.fetch', '+refs/heads/*:refs/remotes/origin/*')

                git_repo.remote('origin').fetch()
                self.stdout.write(self.style.SUCCESS(f"Fetched from origin for {repo.slug}"))
            except GitCommandError as e:
                self.stderr.write(self.style.ERROR(f"Git fetch failed: {e}"))
                continue

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
                    self.stderr.write(self.style.ERROR(f"No default branch found in {repo.slug}"))
                    continue

                commits_iter = git_repo.iter_commits(default_branch, max_count=limit)
            except GitCommandError as e:
                self.stderr.write(self.style.ERROR(f"Failed to get commits: {e}"))
                continue

            existing_hashes = set(Commit.objects.filter(repo=repo).values_list('commit_hash', flat=True))
            commits_to_create = []
            commit_hashes = []

            for commit in reversed(list(commits_iter)):  # 오래된 순으로
                if commit.hexsha in existing_hashes:
                    self.stderr.write(self.style.WARNING(f"Skipping existing commit {commit.hexsha}"))
                    continue

                author = commit.author.name or "Unknown"
                seoul_tz = ZoneInfo("Asia/Seoul")
                date = make_aware(datetime.utcfromtimestamp(commit.committed_date), timezone=seoul_tz)
                message = commit.message.strip()

                commits_to_create.append(Commit(
                    repo=repo,
                    commit_hash=commit.hexsha,
                    author=author,
                    date=date,
                    message=message
                ))
                commit_hashes.append((commit.hexsha, message))

            if commits_to_create:
                with transaction.atomic():
                    try:
                        Commit.objects.bulk_create(commits_to_create, ignore_conflicts=True)
                        self.stdout.write(self.style.SUCCESS(f"Created {len(commits_to_create)} commits"))

                        saved_hashes = set(Commit.objects.filter(
                            repo=repo,
                            commit_hash__in=[c.commit_hash for c in commits_to_create]
                        ).values_list('commit_hash', flat=True))

                        for commit_hash, message in commit_hashes:
                            if commit_hash not in saved_hashes:
                                continue
                            issue_numbers = re.findall(r'#(\d+)', message)
                            if issue_numbers:
                                valid_issues = Issue.objects.filter(project=repo.project, pk__in=issue_numbers)
                                if valid_issues.exists():
                                    commit_obj = Commit.objects.get(commit_hash=commit_hash)
                                    commit_obj.issues.add(*valid_issues)
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
