from django.contrib.auth.mixins import LoginRequiredMixin

from _pdf.mixins import PdfExportMixin, PdfUtilsMixin
from work.models.meeting import Meeting


class PdfExportMeeting(LoginRequiredMixin, PdfExportMixin, PdfUtilsMixin):
    """회의록 PDF 내보내기 뷰"""

    def get(self, request, pk):
        # 회의록 데이터 조회
        meeting = Meeting.objects.select_related(
            'project', 'category', 'creator'
        ).prefetch_related('attendees', 'issues').get(pk=pk)

        # 기본 컨텍스트 및 데이터 구성
        context = self.get_base_context(
            meeting=meeting,
            company=meeting.project.company
        )

        # 파일명 생성
        filename = self.create_filename('Meeting_Minutes', meeting.pk)

        # PDF 응답 생성
        return self.create_pdf_response('pdf/meeting.html', context, filename)
