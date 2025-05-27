import requests
from django.shortcuts import get_object_or_404
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


GITHUB_API_HEADERS = lambda token: {
    "Accept": "application/vnd.github+json",
    "Authorization": f"token {token}"
}


class GetTagTree(APIView):
    permission_classes = (permissions.IsAuthenticated,)


class GithubBranchTreeView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request, pk, branch):
        repo = get_object_or_404(Repository, pk=pk)

        token = repo.github_token
        headers = GITHUB_API_HEADERS(token)

        base_url = f"https://api.github.com/repos/{repo.owner}/{repo.slug}"
        branch_url = f"{base_url}/branches/{branch}"

        try:
            branch_res = requests.get(branch_url, headers=headers)
            branch_res.raise_for_status()
            branch_commit = branch_res.json().get("commit", {})
            commit_info = branch_commit.get("commit", {})
            author_info = commit_info.get("author", {})
        except Exception as e:
            return Response({"Error": "Branch fetch failed", "details": str(e)}, status=500)

        branch_api = {
            "name": branch,
            "commit": {
                "sha": branch_commit.get("sha", "")[:5],
                "url": branch_commit.get("url"),
                "author": author_info.get("name", "Unknown"),
                "date": author_info.get("date"),
                "message": commit_info.get("message"),
            }
        }

        # 트리 URL에서 파일 트리 정보 가져 오기
        tree_url = commit_info.get("tree", {}).get("url")
        if not tree_url:
            return Response({"Error": "Tree URL not found in branch commit"}, status=500)

        try:
            tree_res = requests.get(tree_url, headers=headers)
            tree_res.raise_for_status()
            tree_data = tree_res.json().get("tree", [])
        except Exception as e:
            return Response({"Error": "Tree fetch failed", "details": str(e)}, status=500)

        trees_api = []
        for item in tree_data:
            try:
                commits_url = f"{base_url}/commits?path={item['path']}"
                commit_res = requests.get(commits_url, headers=headers)
                commit_res.raise_for_status()
                commit_json = commit_res.json()
                if not commit_json:
                    continue

                commit = commit_json[0]
                commit_meta = commit.get("commit", {})
                commit_author = commit_meta.get("author", {})

                trees_api.append({
                    "path": item.get("path"),
                    "mode": item.get("mode"),
                    "type": item.get("type"),
                    "sha": item.get("sha"),
                    "url": item.get("url"),
                    "size": item.get("size"),
                    "commit": {
                        "sha": commit.get("sha", "")[:5],
                        "url": commit.get("url"),
                        "author": commit_author.get("name", "Unknown"),
                        "date": commit_author.get("date"),
                        "message": commit_meta.get("message"),
                    },
                    "open": False,
                    "loaded": False if item.get("type") == "tree" else None,
                })
            except Exception as e:
                print(f"[!] Commit fetch failed for {item.get('path')}: {e}")
                continue

        # 트리 정렬: 디렉터리(tree) 먼저, 그 다음 파일(blob), 이름 오름차순
        trees_api.sort(key=lambda item: (item["type"] != "tree", item["path"].lower()))
        return Response({"branch": branch_api, "trees": trees_api}, status=status.HTTP_200_OK)


class GithubSubTreeView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request, pk, sha):
        repo = get_object_or_404(Repository, pk=pk)

        token = repo.github_token
        headers = GITHUB_API_HEADERS(token)

        base_url = f"https://api.github.com/repos/{repo.owner}/{repo.slug}"
        tree_url = f"{base_url}/git/trees/{sha}"

        try:
            tree_res = requests.get(tree_url, headers=headers)
            tree_res.raise_for_status()
            sub_tree = tree_res.json().get("tree", {})
        except Exception as e:
            return Response({"Error": "Sub Tree fetch failed", "details": str(e)}, status=500)

        # 트리 정렬: 디렉터리(tree) 먼저, 그 다음 파일(blob), 이름 오름차순
        sub_tree.sort(key=lambda item: (item["type"] != "tree", item["path"].lower()))
        return Response(sub_tree, status=status.HTTP_200_OK)
