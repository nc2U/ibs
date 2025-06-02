import os
import chardet
from datetime import timezone, datetime

from charset_normalizer import is_binary
from django.shortcuts import get_object_or_404
from git import Repo, GitCommandError
from git.exc import BadName
from rest_framework import viewsets, status
from rest_framework.exceptions import NotFound
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
        serializer = GitRepoApiSerializer(repo_info)
        return Response(serializer.data, status=status.HTTP_200_OK)


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
                        "sha": commit.hexsha,
                        "author": commit.author.name,
                        "date": commit.committed_datetime.isoformat(),
                        "message": commit.message.strip()
                    }
                })
            serializer = GitBranchSerializer(branches, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GitTagsView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request, pk, *args, **kwargs):
        repo_path = get_repo_path(pk)
        if not os.path.exists(repo_path):
            return Response({"error": "Repository path not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            repo = Repo(repo_path)

            tag_list = []
            for tag in repo.tags:
                try:
                    # Annotated tag이면 tag 객체의 tag 속성에서 커밋 추출
                    commit = tag.commit

                    tag_list.append({
                        "name": tag.name,
                        "commit": {
                            "sha": commit.hexsha,
                            "author": commit.author.name,
                            "date": commit.committed_datetime.isoformat(),
                            "message": commit.message.strip()
                        }
                    })
                except (BadName, ValueError) as e:
                    tag_list.append({
                        "name": tag.name,
                        "commit": None,
                        "error": str(e)
                    })
            serializer = GitBranchSerializer(tag_list, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
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
                "sha": commit.hexsha,
                "author": commit.author.name,
                "date": commit.authored_datetime.isoformat(),
                "message": commit.message.strip()
            }
        }

        # 트리 정보 구성
        tree = commit.tree
        trees_result = []

        for item in tree:
            item_path = item.path  # 상대 경로

            # 최근 커밋 찾기
            try:
                latest_commit = next(repo.iter_commits(branch, paths=item_path, max_count=1))
                latest_commit_data = {
                    "sha": latest_commit.hexsha,
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

            trees_result.append({
                "path": item.path,
                "name": item.name,
                "mode": item.mode,
                "type": "tree" if item.type == "tree" else "blob",
                "sha": item.hexsha,
                "size": item.size if item.type == "blob" else None,
                "commit": latest_commit_data
            })

        # 트리 정렬: 디렉터리 → 파일, 이름순
        trees_result.sort(key=lambda item: (item["type"] != "tree", item["path"].lower()))
        serializer = GitBranchAndTreeSerializer({"branch": branch_api, "trees": trees_result})
        return Response(serializer.data, status=status.HTTP_200_OK)


class GitSubTreeView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request, pk, path=None):
        sha = request.query_params.get("sha", "").strip()  # commit SHA

        if not sha:
            return Response({"error": "Missing commit SHA"}, status=400)

        repo_path = get_repo_path(pk)
        if not os.path.exists(repo_path):
            return Response({"error": "Repository path not found"}, status=404)

        try:
            repo = Repo(repo_path)
        except (BadName, KeyError) as e:
            return Response({"error": "Invalid SHA or path", "details": str(e)}, status=400)

        # 커밋 가져 오기
        try:
            commit = repo.commit(sha)  # repo.head.commit
        except ValueError:
            return Response({"error": "Repository HEAD is not set"}, status=400)

        if path:  # 트리 가져오기
            try:  # 특정 경로의 트리
                tree = commit.tree[path]
                if tree.type != "tree":
                    return Response({"error": f"Path {path} is not a directory"}, status=400)
            except KeyError:
                raise NotFound(f"Path {path} not found")
        else:
            # 루트 트리
            tree = commit.tree

        # 트리 항목 처리
        items = []
        # 하위 트리와 블롭 나열
        for item in tree.trees + tree.blobs:
            item_path = item.path
            # 최신 커밋 가져오기
            latest_commit = next(repo.iter_commits(paths=item_path, max_count=1), commit)
            items.append({
                "path": item_path,
                "name": item.name,
                "mode": item.mode,
                "type": item.type,
                "sha": item.hexsha,
                "size": item.size if item.type == "blob" else None,
                "commit": {
                    "sha": latest_commit.hexsha,
                    "author": latest_commit.author.name,
                    "date": latest_commit.authored_datetime.isoformat(),
                    "message": latest_commit.message.strip()
                }
            })

        # 정렬 및 시리얼라이저로 데이터 검증 및 변환
        items.sort(key=lambda x: (x["type"] != "tree", x["name"].lower()))
        serializer = TreeItemSerializer(items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GitFileContentView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def is_binary(data: bytes) -> bool:
        # NULL 바이트 포함 여부 확인
        if b'\x00' in data:
            return True
        # chardet 로 인코딩 추정
        result = chardet.detect(data)
        encoding = result.get("encoding")
        # 인코딩 판별 불가 => 바이너리 간주
        if encoding is None:
            return True
        try:
            data.decode(encoding)
            return False
        except UnicodeDecodeError:
            return True

    @staticmethod
    def get(request, pk, path, *args, **kwargs):
        sha = request.query_params.get("sha", "").strip()
        if not sha:
            return Response({"error": "Missing 'sha' parameter"}, status=status.HTTP_400_BAD_REQUEST)

        repo_path = get_repo_path(pk)
        if not os.path.exists(repo_path):
            return Response({"error": f"Repository path not found: {repo_path}"}, status=status.HTTP_404_NOT_FOUND)

        try:
            repo = Repo(repo_path)
            try:
                # sha 가 커밋인지 확인
                commit = repo.commit(sha)
                tree = commit.tree
            except (BadName, ValueError) as e:
                return Response({"error": f"Invalid SHA: {sha}", "details": str(e)}, status=400)

            # tree = repo.tree(sha)
            path_parts = path.strip("/").split("/")
            blob = tree
            for part in path_parts:
                blob = blob / part

            if blob.type != "blob":
                return Response({"error": f"The path is not a file (blob): {path}"}, status=400)

            raw_data = blob.data_stream.read()

            # 🟡 마지막 수정 커밋 가져오기
            try:
                last_commit = next(repo.iter_commits(sha, paths=path))
                last_modified = datetime.fromtimestamp(last_commit.committed_date).isoformat()
            except StopIteration:
                last_modified = None  # 기록 없음

            if is_binary(raw_data):
                return Response({
                    "name": blob.name,
                    "path": path,
                    "sha": sha,
                    "size": blob.size,
                    "modified": last_modified,
                    "binary": True,
                    "content": None,
                    "message": "This file is binary and cannot be displayed as text."
                })

            content = raw_data.decode("utf-8", errors="replace")
            return Response({
                "name": blob.name,
                "path": path,
                "sha": sha,
                "size": blob.size,
                "modified": last_modified,
                "binary": False,
                "content": content
            }, status=status.HTTP_200_OK)

        except (BadName, KeyError) as e:
            return Response({"error": "Invalid SHA or path", "details": str(e)}, status=400)
        except Exception as e:
            return Response({"error": "Unexpected server error", "details": str(e)}, status=500)


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
                        diff_text = ''
                try:
                    diff_lines = diff_text.splitlines()
                except AttributeError:
                    diff_lines = []
                truncated = False

                if len(diff_lines) > CompareCommitsView.MAX_LINES and not full:
                    diff_text = "\n".join(diff_lines[:CompareCommitsView.MAX_LINES]) + "\n... [truncated]"
                    truncated = True
            except GitCommandError:
                diff_text = ""
                truncated = False

            serializer = GitCompareCommitsSerializer({
                "base": base,
                "head": head,
                "commits": commit_list,
                "diff": diff_text,
                "truncated": truncated
            })
            return Response(serializer.data, status=status.HTTP_200_OK)

        except GitCommandError as e:
            return Response({"error": f"Git error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
