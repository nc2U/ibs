import os

from django.shortcuts import get_object_or_404
from datetime import timezone
from git import Repo, GitCommandError
from git.exc import BadName
from rest_framework import viewsets, status
from rest_framework.views import APIView

from apiV1.pagination import *
from apiV1.permission import *
from apiV1.serializers.work.github import *


class RepositoryViewSet(viewsets.ModelViewSet):
    queryset = Repository.objects.all()
    serializer_class = RepositorySerializer
    permission_classes = (permissions.IsAuthenticated,)
    filterset_fields = ('project', 'is_default', 'is_report')


class CommitViewSet(viewsets.ModelViewSet):
    queryset = Commit.objects.all()
    serializer_class = CommitSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageNumberPaginationTwentyFive
    filterset_fields = ('repo__project', 'repo', 'commit_hash', 'issues')


def get_repo_path(repo_id):
    repo_obj = get_object_or_404(Repository, pk=repo_id)
    repo_path = repo_obj.local_path or f"/app/repos/{repo_obj.slug}.git"
    return repo_path


class GitRepoApiView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request, pk):
        repo_path = get_repo_path(pk)

        repo = Repo(repo_path)

        # 가장 오래된 커밋 시간 (created_at 추정)
        oldest_commit = next(repo.iter_commits('--all', max_count=1, reverse=True))
        created_at = oldest_commit.committed_datetime.astimezone(timezone.utc)

        # 가장 최근 커밋 시간 (pushed_at 추정)
        latest_commit = repo.head.commit
        pushed_at = latest_commit.committed_datetime.astimezone(timezone.utc)

        # 디폴트 브랜치 추정
        try:
            default_branch = repo.git.symbolic_ref("refs/remotes/origin/HEAD").split("/")[-1]
        except Exception:
            default_branch = repo.active_branch.name

        # 저장소 이름
        repo_name = os.path.basename(repo_path).replace(".git", "")

        repo_info = {
            "name": repo_name,
            "created_at": created_at,
            "pushed_at": pushed_at,
            "default_branch": default_branch,
        }
        return Response(repo_info, status=status.HTTP_200_OK)


class GitBranchesView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request, pk):
        repo_path = get_repo_path(pk)
        if not os.path.exists(repo_path):
            return Response({"error": "Repository path not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            repo = Repo(repo_path)
            # 기본 브랜치명 (HEAD가 가리키는 브랜치)
            default_branch = repo.active_branch.name if not repo.bare else repo.head.ref.name

            branches = []
            for head in repo.branches:
                if head.name == default_branch:
                    continue
                commit = head.commit
                branches.append({
                    "name": head.name,
                    "commit": {
                        "sha": commit.hexsha[:5],
                        "author": commit.author.name,
                        "date": commit.committed_datetime.isoformat(),
                        "message": commit.message.strip()
                    }
                })

            return Response(branches, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GitBranchTreeView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request, pk, branch):
        repo_path = get_repo_path(pk)

        if not os.path.exists(repo_path):
            return Response({"Error": "Local repository path not found"}, status=404)

        try:
            repo = Repo(repo_path)
            if branch not in repo.heads:
                return Response({"Error": f"Branch '{branch}' not found"}, status=404)
            commit = repo.heads[branch].commit
        except GitCommandError as e:
            return Response({"Error": "Failed to access branch or commit", "details": str(e)}, status=500)

        # 브랜치 정보 구성
        branch_api = {
            "name": branch,
            "commit": {
                "sha": commit.hexsha[:5],
                "url": None,
                "author": commit.author.name,
                "date": commit.authored_datetime.isoformat(),
                "message": commit.message.strip()
            }
        }

        # 트리 정보 구성
        tree = commit.tree
        result = []

        for item in tree:
            item_path = item.path  # 상대 경로

            # 최근 커밋 찾기
            try:
                latest_commit = next(repo.iter_commits(branch, paths=item_path, max_count=1))
                latest_commit_data = {
                    "sha": latest_commit.hexsha[:5],
                    "author": latest_commit.author.name,
                    "date": latest_commit.authored_datetime.isoformat(),
                    "message": latest_commit.message.strip()
                }
            except StopIteration:
                latest_commit_data = {
                    "sha": "",
                    "author": "Unknown",
                    "date": "",
                    "message": ""
                }

            result.append({
                "path": item_path,
                "mode": item.mode,
                "type": "tree" if item.type == "tree" else "blob",
                "sha": item.hexsha,
                "size": getattr(item, "size", None),
                "commit": latest_commit_data
            })

        # 트리 정렬: 디렉터리 → 파일, 이름순
        result.sort(key=lambda item: (item["type"] != "tree", item["path"].lower()))
        return Response({"branch": branch_api, "trees": result}, status=status.HTTP_200_OK)


class GitSubTreeView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request, pk, sha):
        repo_path = get_repo_path(pk)

        if not os.path.exists(repo_path):
            return Response({"Error": "Local repository path not found"}, status=404)

        try:
            repo = Repo(repo_path)
            tree = repo.tree(sha)
        except (BadName, GitCommandError) as e:
            return Response({"Error": "Invalid SHA or repo access failed", "details": str(e)}, status=400)

        result = []

        for item in tree:
            result.append({
                "path": item.path,  # 상대 경로
                "mode": item.mode,
                "type": "tree" if item.type == "tree" else "blob",
                "sha": item.hexsha,
                "size": getattr(item, "size", None),
            })

        # 디렉터리 먼저, 파일 다음, 이름 오름차순 정렬
        result.sort(key=lambda item: (item["type"] != "tree", item["path"].lower()))
        return Response(result, status=status.HTTP_200_OK)


class CompareCommitsView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    MAX_LINES = 1000  # 최대 반환 줄 수

    @staticmethod
    def get(request, pk, *args, **kwargs):
        base = request.query_params.get("base")
        head = request.query_params.get("head")
        full = request.query_params.get("full")

        if not base or not head:
            return Response(
                {"error": "Missing 'base' or 'head' parameter"},
                status=status.HTTP_400_BAD_REQUEST
            )

        repo_path = get_repo_path(pk)
        if not os.path.exists(repo_path):
            return Response(
                {"error": "Repository path not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            repo = Repo(repo_path)

            try:
                repo.commit(base)
                repo.commit(head)
            except BadName:
                return Response({"error": "Invalid commit hash"}, status=status.HTTP_400_BAD_REQUEST)

            # 커밋 목록 수집
            try:
                commits = list(repo.iter_commits(f"{base}..{head}"))
            except GitCommandError:
                commits = list(repo.iter_commits(f"{head}..{base}"))

            commit_list = [
                {
                    "sha": c.hexsha,
                    "author": c.author.name,
                    "date": c.committed_datetime.isoformat(),
                    "message": c.message.strip(),
                }
                for c in commits
            ]

            # Unified diff 생성 및 길이 제한 적용
            try:
                diff_text = repo.git.diff(base, head, unified=3)
                if not diff_text.strip():
                    reversed_diff_text = repo.git.diff(head, base, unified=3)
                    if reversed_diff_text.strip():
                        diff_text = reversed_diff_text
                    else:
                        diff_text = None  # 또는 "" 등 fallback 처리
                diff_lines = diff_text.splitlines()
                truncated = False

                if len(diff_lines) > CompareCommitsView.MAX_LINES and not full:
                    diff_text = "\n".join(diff_lines[:CompareCommitsView.MAX_LINES]) + "\n... [truncated]"
                    truncated = True
            except GitCommandError:
                diff_text = ""
                truncated = False

            return Response({
                "base": base,
                "head": head,
                "commits": commit_list,
                "diff": diff_text,
                "truncated": truncated
            })

        except GitCommandError as e:
            return Response({"error": f"Git error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
