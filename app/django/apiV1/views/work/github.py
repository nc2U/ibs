import requests
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


class GithubRootTreeView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request, pk):
        try:
            repo = Repository.objects.get(pk=pk)
        except Repository.DoesNotExist:
            return Response({'error': 'Repository not found'}, status=404)

        repo_url = f"api.github.com/repos/{repo.owner}/{repo.slug}"
        tree_url = f"{repo_url}/git/trees/{request.query_params.get("sha")}"
        token = repo.github_token

        if not all([tree_url, repo_url, token]):
            return Response({"error": "Missing parameters"}, status=400)

        headers = GITHUB_API_HEADERS(token)

        try:
            tree_res = requests.get(tree_url, headers=headers)
            tree_res.raise_for_status()
            tree_data = tree_res.json().get("tree", [])
        except Exception as e:
            return Response({"error": "Tree fetch failed", "details": str(e)}, status=500)

        result = []
        for item in tree_data:
            try:
                commits_url = f"{repo_url}/commits?path={item['path']}"
                commit_res = requests.get(commits_url, headers=headers)
                commit_res.raise_for_status()
                commit = commit_res.json()[0] if commit_res.json() else None

                if not commit:
                    continue

                result.append({
                    "path": item["path"],
                    "mode": item["mode"],
                    "type": item["type"],
                    "sha": item["sha"],
                    "url": item["url"],
                    "size": item.get("size"),
                    "commit": {
                        "sha": commit["sha"][:5],
                        "url": commit.get("html_url") or commit.get("url"),
                        "author": commit["commit"]["author"]["name"],
                        "date": commit["commit"]["author"]["date"],
                        "message": commit["commit"]["message"],
                    },
                    "open": False,
                    "loaded": item["type"] == "tree" and False or None
                })
            except Exception as e:
                print(f"Error fetching commit for {item['path']}: {e}")
                continue

        return Response(result, status=status.HTTP_200_OK)
