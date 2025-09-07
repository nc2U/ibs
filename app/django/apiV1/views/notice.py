from rest_framework import viewsets

from ..permission import *
from ..serializers.notice import *

from notice.models import SalesBillIssue


class BillIssueViewSet(viewsets.ModelViewSet):
    queryset = SalesBillIssue.objects.all()
    serializer_class = SallesBillIssueSerializer
    filterset_fields = ('project',)
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)
