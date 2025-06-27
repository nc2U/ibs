import os
import re
from datetime import timezone, datetime

from django.shortcuts import get_object_or_404
from git import Repo, GitCommandError, NULL_TREE
from git.exc import BadName
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.views import APIView

from apiV1.pagination import *
from apiV1.permission import *
from apiV1.serializers.work.git_repo import *
from work.models import IssueProject


class RepositoryViewSet(viewsets.ModelViewSet):
    queryset = Repository.objects.all()
    serializer_class = RepositorySerializer
    permission_classes = (permissions.IsAuthenticated,)
    filterset_fields = ('project', 'is_default', 'is_report')


class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filterset_fields = ('repo', 'name')


def get_all_descendant_projects(project):
    descendants = set()
    children = IssueProject.objects.filter(parent=project)
    for child in children:
        descendants.add(child)
        descendants.update(get_all_descendant_projects(child))
    return descendants


class CommitViewSet(viewsets.ModelViewSet):
    queryset = Commit.objects.all().order_by('-id')
    serializer_class = CommitSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageNumberPaginationTwentyFive
    filterset_fields = ('repo', 'branches', 'branches__name', 'issues')
    search_fields = ('commit_hash',)

    def get_queryset(self):
        queryset = super().get_queryset()
        request = self.request

        up_to_hash = self.request.query_params.get("up_to")
        if up_to_hash:
            try:
                target_commit = Commit.objects.get(commit_hash__startswith=up_to_hash)
                queryset = queryset.filter(repo=target_commit.repo, id__lte=target_commit.id)
            except Commit.DoesNotExist:
                return Commit.objects.none()

        # repo__project 포함 필터 처리
        project_id = request.query_params.get("repo__project")
        if project_id:
            root_project = get_object_or_404(IssueProject, pk=project_id)
            descendants = get_all_descendant_projects(root_project)
            project_ids = [p.pk for p in descendants] + [root_project.pk]
            queryset = queryset.filter(repo__project_id__in=project_ids)

        return queryset

    @action(detail=False, methods=['get'], url_path='graph')
    def git_graph(self, request):
        """
        /commit/graph/
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        dag = {}
        for commit in page:
            sha = commit.commit_hash
            dag[sha] = {
                'sha': sha,
                'parents': list(commit.parents.values_list('commit_hash', flat=True)),
                # 'branches': list(commit.branches.values_list('name', flat=True)),
            }

        return self.get_paginated_response(dag)


def get_repo_path(repo_id):
    repo_obj = get_object_or_404(Repository, pk=repo_id)
    repo_path = repo_obj.local_path or f"/app/repos/{repo_obj.slug}.git"

    if not os.path.exists(repo_path):
        return Response({"error": "Local Repository path not found"},
                        status=status.HTTP_404_NOT_FOUND)
    return repo_path


def get_default_branch(repo: Repo) -> str | None:
    """
    Git 저장소의 기본 브랜치를 반환합니다.
    Args: repo: GitPython Repo 객체
    Returns:
        str: 기본 브랜치 이름 (예: 'main')
        None: 기본 브랜치를 찾을 수 없는 경우
    """

    try:  # 1. origin/HEAD 확인
        origin_head_ref = repo.refs['origin/HEAD']
        if origin_head_ref and origin_head_ref.reference:
            ref_name = origin_head_ref.reference.name
            if ref_name.startswith('refs/remotes/origin/'):
                return ref_name.split('refs/remotes/origin/')[1]
    except (KeyError, IndexError, AttributeError):
        pass

    try:  # 2. HEAD가 가리키는 브랜치 (non-bare only)
        if not repo.bare and repo.head.is_valid() and not repo.head.is_detached:
            branch_name = repo.head.reference.name
            if branch_name.startswith('refs/heads/'):
                return branch_name.split('refs/heads/')[1]
            return branch_name
    except (ValueError, TypeError, AttributeError):
        pass

    heads = [head.name for head in repo.heads]
    for branch_name in ['main', 'master']:  # 3. 일반적인 브랜치 후보
        if branch_name in heads:
            return branch_name

    if heads:  # 4. 사용 가능한 첫 번째 브랜치
        return heads[0]

    return None


class GitRepoApiView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request, pk):
        repo_path = get_repo_path(pk)

        repo = Repo(repo_path)

        # 저장소 이름
        repo_name = os.path.basename(repo_path).replace(".git", "")

        # 가장 오래된 커밋 시간 (created_at 추정)
        oldest_commit = next(repo.iter_commits('--all', max_count=1, reverse=True))
        created_at = oldest_commit.committed_datetime.astimezone(timezone.utc)

        # 가장 최근 커밋 시간 (pushed_at 추정)
        latest_commit = repo.head.commit
        pushed_at = latest_commit.committed_datetime.astimezone(timezone.utc)

        repo_info = {
            "name": repo_name,
            "created_at": created_at,
            "pushed_at": pushed_at,
            "default_branch": get_default_branch(repo),
        }
        serializer = GitRepoApiSerializer(repo_info)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GitBranchesView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request, pk):
        repo_path = get_repo_path(pk)

        try:
            repo = Repo(repo_path)

            branches = []
            for head in repo.branches:
                if head.name == "HEAD":
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


class GitTreeView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request, pk, path=None):
        refs = request.query_params.get("refs", "").strip()  # refs name

        repo_path = get_repo_path(pk)

        try:
            repo = Repo(repo_path)
        except (BadName, KeyError) as e:
            return Response({"error": "Invalid repository", "details": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 기본 브랜치 설정
            default_branch = get_default_branch(repo)
            curr_refs = default_branch

            # refs 가 제공되면 해당 refs(브랜치/태그/해시) 사용, 없으면 기본 브랜치 시도
            if refs:  # commit 객체 특정
                try:
                    commit = repo.commit(refs)
                    curr_refs = refs
                except (BadName, ValueError):
                    return Response({"error": f"Invalid refs: {refs}", "details": "Branch not found"},
                                    status=status.HTTP_400_BAD_REQUEST)
            else:
                # 기본 브랜치 (main/master) 또는 HEAD
                branch_ref = next((b for b in repo.heads if b.name == default_branch), None)
                if not branch_ref:
                    return Response({"Error": f"Default branch '{default_branch}' not found"}, status=404)
                commit = branch_ref.commit

            # refs 정보
            branches = repo.git.branch('--contains', commit.hexsha).split('\n')
            branches = [b.strip().lstrip('* ') for b in branches if b.strip()]
            refs_api = {
                "name": curr_refs,
                "branches": branches,
                "commit": {
                    "sha": commit.hexsha,
                    "author": commit.author.name or "Unknown",
                    "date": commit.authored_datetime.isoformat() if commit.authored_datetime else "",
                    "message": commit.message.strip() if commit.message else ""
                }
            }

            # 트리 정보
            if path:  # 경로가 주어진 경우 해당 경로
                try:
                    tree = commit.tree[path]
                    if tree.type != "tree":
                        return Response({"error": f"Path {path} is not a directory"},
                                        status=status.HTTP_400_BAD_REQUEST)
                except KeyError:
                    raise NotFound(f"Path {path} not found")
            else:  # 주어진 경로가 없으면 루트 경로
                tree = commit.tree  # 루트 트리

            tree_items = []
            commit_cache = {}  # 성능 최적화를 위한 커밋 캐시
            for item in tree.trees + tree.blobs:
                item_path = item.path
                # 최신 커밋 가져오기 (캐시 활용)
                if item_path not in commit_cache:
                    commit_cache[item_path] = next(repo.iter_commits(paths=item_path, max_count=1), commit)
                latest_commit = commit_cache[item_path]
                latest_commit_data = {
                    "sha": latest_commit.hexsha,
                    "author": latest_commit.author.name or "Unknown",
                    "date": latest_commit.authored_datetime.isoformat() if latest_commit.authored_datetime else "",
                    "message": latest_commit.message.strip() if latest_commit.message else ""
                }
                tree_items.append({
                    "path": item_path,
                    "name": item.name,
                    "mode": item.mode,
                    "type": item.type,
                    "sha": item.hexsha,
                    "size": item.size if item.type == "blob" else None,
                    "commit": latest_commit_data
                })

            # 정렬 및 시리얼라이저
            tree_items.sort(key=lambda x: (x["type"] != "tree", x["name"].lower()))
            serializer = GitRefsAndTreeSerializer({"refs": refs_api, "trees": tree_items})
            return Response(serializer.data, status=status.HTTP_200_OK)

        except (BadName, ValueError) as e:
            return Response({"Error": "Invalid Git reference", "details": str(e)}, status=400)
        except GitCommandError as e:
            return Response({"Error": "Git command failed", "details": str(e)}, status=500)
        except Exception as e:
            return Response({"Error": "Unexpected error", "details": str(e)}, status=500)


class GitFileContentView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def is_binary(data: bytes) -> bool:
        """
        간단한 휴리스틱 방식으로 바이너리 판별
        """
        text_chars = bytearray({7, 8, 9, 10, 12, 13, 27}
                               | set(range(0x20, 0x100)) - {0x7f})
        return bool(data.translate(None, text_chars))

    def get(self, request, pk, path, *args, **kwargs):
        sha = request.query_params.get("sha", "").strip()
        if not sha:
            return Response({"error": "Missing 'sha' parameter"}, status=status.HTTP_400_BAD_REQUEST)

        repo_path = get_repo_path(pk)

        try:
            repo = Repo(repo_path)
            try:
                # sha 가 커밋인지 확인
                commit = repo.commit(sha)
                tree = commit.tree
            except (BadName, ValueError) as e:
                return Response({"error": f"Invalid SHA: {sha}", "details": str(e)}, status=400)

            path_parts = path.strip("/").split("/")
            blob = tree
            for part in path_parts:
                blob = blob / part

            if blob.type != "blob":
                return Response({"error": f"The path is not a file (blob): {path}"}, status=400)

            try:  # 마지막 수정 커밋 가져 오기
                last_commit = next(repo.iter_commits(sha, paths=path))
                last_modified = datetime.fromtimestamp(last_commit.committed_date).isoformat()
            except StopIteration:
                last_modified = None  # 기록 없음

            commits = []  # ✅ 이력 조회 (최대 100개)
            for c in repo.iter_commits(sha, paths=path, max_count=100):
                commits.append({
                    "sha": c.hexsha,
                    "author": c.author.name,
                    "date": datetime.fromtimestamp(c.committed_date).isoformat(),
                    "message": c.message.strip(),
                })

            raw_data = blob.data_stream.read()

            if self.is_binary(raw_data):
                return Response({"file": {
                    "name": blob.name,
                    "path": path,
                    "sha": sha,
                    "size": blob.size,
                    "modified": last_modified,
                    "binary": True,
                    "content": None,
                    "message": "This file is binary and cannot be displayed as text.",
                }, "commits": commits})

            content = raw_data.decode("utf-8", errors="replace")
            return Response({"file": {
                "name": blob.name,
                "path": path,
                "sha": sha,
                "size": blob.size,
                "modified": last_modified,
                "binary": False,
                "content": content,
            }, "commits": commits}, status=status.HTTP_200_OK)

        except (BadName, KeyError) as e:
            return Response({"error": "Invalid SHA or path", "details": str(e)}, status=400)
        except Exception as e:
            return Response({"error": "Unexpected server error", "details": str(e)}, status=500)


class CompareCommitsView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    MAX_LINES = 1000

    @staticmethod
    def validate_sha(sha):
        """SHA-1 해시 형식 검증"""
        if not sha or not re.match(r'^[0-9a-f]{7,40}$', sha, re.I):
            return False
        return True

    def get(self, request, pk, *args, **kwargs):
        base = request.query_params.get("base")
        head = request.query_params.get("head")
        full = request.query_params.get("full")

        if not head or head == 'undefined':
            return Response({"error": "Missing or invalid 'head' parameter"}, status=status.HTTP_400_BAD_REQUEST)
        if base == 'undefined':
            base = None

        head = head.strip()
        if not self.validate_sha(head):
            return Response({"error": f"Invalid head SHA format: {head}"}, status=status.HTTP_400_BAD_REQUEST)

        repo_path = get_repo_path(pk)

        try:
            repo = Repo(repo_path)
            # 저장소 최신화
            repo.git.fetch('origin')

            try:  # Head 커밋 검증
                head_commit = repo.commit(head)
            except BadName as e:
                return Response({"error": f"Head commit {head} not found in repository"},
                                status=status.HTTP_400_BAD_REQUEST)

            if not base:  # Base 처리
                if not head_commit.parents:  # 최초 커밋 또는 head 만으로 처리
                    # 최초 커밋
                    diff_text = repo.git.show(head, unified=3)
                    commit_list = [{
                        "sha": head,
                        "author": head_commit.author.name,
                        "date": head_commit.committed_datetime.isoformat(),
                        "message": head_commit.message.strip(),
                    }]
                    serializer = GitCompareCommitsSerializer({
                        "base": None,
                        "head": head,
                        "commits": commit_list,
                        "diff": diff_text,
                        "truncated": False
                    })
                    return Response(serializer.data, status=status.HTTP_200_OK)
                base = head_commit.parents[0].hexsha  # head의 부모 커밋 사용
            else:
                base = base.strip()
                if not self.validate_sha(base):
                    return Response({"error": f"Invalid base SHA format: {base}"}, status=status.HTTP_400_BAD_REQUEST)
                try:
                    repo.commit(base)
                except BadName:
                    return Response({"error": f"Base commit {base} not found in repository"},
                                    status=status.HTTP_400_BAD_REQUEST)

            try:  # 커밋 목록 수집
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
                for c in commits]

            try:  # Unified diff 생성 및 길이 제한 적용
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

                if len(diff_lines) > self.MAX_LINES and not full:
                    diff_text = "\n".join(diff_lines[:self.MAX_LINES]) + "\n... [truncated]"
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
            return Response({"error": f"GitCommand error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"error": f"Unexpected error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetChangedFilesView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request, pk, *args, **kwargs):
        sha = request.query_params.get("sha", None)

        repo_path = get_repo_path(pk)

        try:
            repo = Repo(repo_path)

            try:
                commit = repo.commit(sha)
            except BadName:
                return Response({"error": "Invalid commit hash"}, status=status.HTTP_400_BAD_REQUEST)

            # 부모 커밋과 비교해 변경된 파일 목록을 가져 오기
            if commit.parents:
                diff_index = commit.diff(commit.parents[0])
            else:
                # 초기 커밋: 부모가 없으므로 전체 트리 대상으로 비교
                diff_index = commit.diff(NULL_TREE)

            changed_files = []
            for diff in diff_index:
                changed_files.append({
                    "path": diff.a_path or diff.b_path,
                    "type": (
                        "A" if diff.new_file else
                        "D" if diff.deleted_file else
                        "R" if diff.renamed_file else
                        "C" if diff.copied_file else
                        "M"
                    )
                })

            serializer = GetChangedFilesSerializer({"sha": sha, "changed": changed_files})
            return Response(serializer.data, status=status.HTTP_200_OK)


        except GitCommandError as e:
            return Response({"error": f"Git error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
