import os

from django.shortcuts import get_object_or_404
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


class GetTagTree(APIView):
    permission_classes = (permissions.IsAuthenticated,)


def get_repo_path(repo_id):
    repo_obj = get_object_or_404(Repository, pk=repo_id)
    repo_path = repo_obj.local_path or f"/app/repos/{repo_obj.slug}.git"
    return repo_path


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

    @staticmethod
    def get(request, pk, *args, **kwargs):
        base = request.query_params.get('base')
        head = request.query_params.get('head')

        if not base or not head:
            return Response({"Error": "Missing 'base' or 'head' parameter"}, status=status.HTTP_400_BAD_REQUEST)

        repo_path = get_repo_path(pk)
        if not os.path.exists(repo_path):
            return Response({"Error": "Repository path not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            repo = Repo(repo_path)
            base_commit = repo.commit(base)
            head_commit = repo.commit(head)

            commits = list(repo.iter_commits(f'{base}..{head}'))
            if not commits:
                commits = list(repo.iter_commits(f'{head}..{base}'))

            commit_list = [{
                "sha": commit.hexsha,
                "author": commit.author.name,
                "date": commit.committed_datetime.isoformat(),
                "message": commit.message.strip(),
            } for commit in commits]

            diffs = base_commit.diff(head_commit)
            file_list = []
            for diff in diffs:
                try:
                    if diff.new_file:
                        change_type = 'A'
                    elif diff.deleted_file:
                        change_type = 'D'
                    elif diff.renamed:
                        change_type = 'R'
                    else:
                        change_type = 'M'

                    file_list.append({
                        "path": diff.b_path or diff.a_path,
                        "change_type": change_type,
                        "diff": diff.diff.decode('utf-8', errors='ignore') if diff.diff else None,
                    })
                except Exception as e:
                    file_list.append({
                        "path": diff.b_path or diff.a_path,
                        "change_type": '?',
                        "diff": None,
                        "error": str(e),
                    })

            return Response({
                "base": base,
                "head": head,
                "commits": commit_list,
                "files": file_list,
            })

        except BadName:
            return Response({"Error": "Invalid commit hash"}, status=status.HTTP_400_BAD_REQUEST)
        except GitCommandError as e:
            return Response({"Error": f"Git error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
