from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from _pdf.mixins import PdfExportMixin, PdfUtilsMixin
from work.models.meeting import Meeting


class PdfExportMeeting(PdfExportMixin, PdfUtilsMixin):
    """회의록 PDF 내보내기 뷰"""

    def get(self, request, pk):
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            raise PermissionDenied("로그인이 필요합니다.")

        # 회의록 데이터 조회 (잠금보관 워크스페이스 제외)
        meeting = get_object_or_404(
            Meeting.objects.exclude(project__status='9').select_related(
                'project', 'project__company', 'project__module', 'category', 'creator'
            ).prefetch_related(
                'attendees', 'issues__status', 'issues__assigned_to'
            ),
            pk=pk
        )

        # 권한 및 행 단위 보안(RLS) 검증
        if not (user.is_superuser or getattr(user, 'work_manager', False)):
            project = meeting.project
            if hasattr(project, 'module') and not getattr(project.module, 'meeting', True):
                raise PermissionDenied("해당 워크스페이스에서 회의 모듈이 비활성화되어 있습니다.")

            member_user_pks = {m['user']['pk'] for m in project.all_members()}
            is_participant = (
                meeting.creator_id == user.pk or
                any(att.pk == user.pk for att in meeting.attendees.all())
            )
            has_workspace_access = project.is_public or (user.pk in member_user_pks) or is_participant
            user_perms = project.get_user_permissions(user)

            if not has_workspace_access or ('meeting.read' not in user_perms and not is_participant):
                raise PermissionDenied("이 회의록을 열람할 권한이 없습니다.")

        # 기본 컨텍스트 및 데이터 구성
        context = self.get_base_context(
            meeting=meeting,
            company=meeting.project.company if meeting.project else None
        )

        # 파일명 생성 (확장자 없이 베이스 파일명 전달)
        filename = f"{meeting.title}"

        # PDF 응답 생성
        return self.create_pdf_response('pdf/meeting.html', context, filename)

