from _pdf.mixins import PdfExportMixin, PdfUtilsMixin
from work.models.meeting import Meeting


class PdfExportMeeting(PdfExportMixin, PdfUtilsMixin):
    """회의록 PDF 내보내기 뷰"""

    def get(self, request, pk):
        # 회의록 데이터 조회
        meeting = Meeting.objects.select_related(
            'project', 'project__company', 'category', 'creator'
        ).prefetch_related(
            'attendees', 'issues__status', 'issues__assigned_to'
        ).get(pk=pk)

        # 기본 컨텍스트 및 데이터 구성
        context = self.get_base_context(
            meeting=meeting,
            company=meeting.project.company if meeting.project else None
        )

        # 파일명 생성 (확장자 없이 베이스 파일명 전달)
        filename = f"{meeting.title}"

        # PDF 응답 생성
        return self.create_pdf_response('pdf/meeting.html', context, filename)
