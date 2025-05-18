from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination


class PageNumberPaginationCustomBasic(PageNumberPagination):
    max_page_size = 5000


class LimitOffsetPaginationCustomBasic(LimitOffsetPagination):
    max_limit = 500


class PageNumberPaginationThreeThousand(PageNumberPagination):
    page_size = 3000
    page_size_query_param = 'limit'  # 쿼리 파라미터로 사용할 이름

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })


class PageNumberPaginationOneThousand(PageNumberPagination):
    page_size = 1000
    page_size_query_param = 'limit'  # 쿼리 파라미터로 사용할 이름

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })


class PageNumberPaginationFiveHundred(PageNumberPagination):
    page_size = 500
    page_size_query_param = 'limit'  # 쿼리 파라미터로 사용할 이름

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })


class PageNumberPaginationThreeHundred(PageNumberPagination):
    page_size = 300
    page_size_query_param = 'limit'  # 쿼리 파라미터로 사용할 이름

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })


class PageNumberPaginationTwoHundred(PageNumberPagination):
    page_size = 200
    page_size_query_param = 'limit'  # 쿼리 파라미터로 사용할 이름

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })


class PageNumberPaginationOneHundred(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'limit'  # 쿼리 파라미터로 사용할 이름

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })


class PageNumberPaginationFifty(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'limit'  # 쿼리 파라미터로 사용할 이름

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })


class PageNumberPaginationTwentyFive(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'limit'  # 쿼리 파라미터로 사용할 이름

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })


class PageNumberPaginationTwenty(PageNumberPagination):
    page_size = 20


class PageNumberPaginationFifteen(PageNumberPagination):
    page_size = 15


class PageNumberPaginationTen(PageNumberPagination):
    page_size = 10
