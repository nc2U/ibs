from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination


class PageNumberPaginationBase(PageNumberPagination):
    """모든 커스텀 페이지네이션의 기본 클래스"""
    page_size_query_param = 'limit'


class PageNumberPaginationCustomBasic(PageNumberPaginationBase):
    max_page_size = 5000


class LimitOffsetPaginationCustomBasic(LimitOffsetPagination):
    max_limit = 500


class PageNumberPaginationThreeThousand(PageNumberPaginationBase):
    page_size = 3000

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })


class PageNumberPaginationOneThousand(PageNumberPaginationBase):
    page_size = 1000

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })


class PageNumberPaginationFiveHundred(PageNumberPaginationBase):
    page_size = 500

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })


class PageNumberPaginationThreeHundred(PageNumberPaginationBase):
    page_size = 300

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })


class PageNumberPaginationTwoHundred(PageNumberPaginationBase):
    page_size = 200

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })


class PageNumberPaginationOneHundred(PageNumberPaginationBase):
    page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })


class PageNumberPaginationFifty(PageNumberPaginationBase):
    page_size = 50

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })


class PageNumberPaginationTwentyFive(PageNumberPaginationBase):
    page_size = 25

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })


class PageNumberPaginationTwenty(PageNumberPaginationBase):
    page_size = 20


class PageNumberPaginationFifteen(PageNumberPaginationBase):
    page_size = 15


class PageNumberPaginationTen(PageNumberPaginationBase):
    page_size = 10
