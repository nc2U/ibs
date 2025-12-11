"""
File Upload Utilities

Django 6.0과 Python 3.14 환경에서 한글 파일명 인코딩 문제를 해결하기 위한
공통 파일 업로드 유틸리티 모듈
"""

import hashlib
import os
import uuid
from django.utils import timezone


def generate_safe_filename(original_filename, base_path='files', include_microseconds=True):
    """
    한글 파일명을 포함한 모든 파일명을 ASCII 안전한 형태로 변환

    Args:
        original_filename (str): 원본 파일명
        base_path (str): 기본 경로 (기본값: 'files')
        include_microseconds (bool): 마이크로초 포함 여부 (기본값: True)

    Returns:
        str: ASCII 안전한 파일명

    Example:
        >>> generate_safe_filename('새 문서.txt', 'uploads')
        '20251211_081530_123456_a1b2c3d4.txt'
    """
    try:
        # 파일 확장자 추출
        name, ext = os.path.splitext(original_filename)

        # 원본 파일명의 해시 생성 (고유성 보장)
        filename_hash = hashlib.md5(original_filename.encode('utf-8')).hexdigest()[:8]

        # 타임스탬프 생성
        if include_microseconds:
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S_%f')
        else:
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')

        # ASCII 안전한 파일명 생성
        safe_filename = f"{timestamp}_{filename_hash}{ext}"

        return safe_filename

    except Exception:
        # 최종 백업: UUID 사용
        name, ext = os.path.splitext(original_filename)
        return f"{uuid.uuid4().hex}{ext}"


def get_upload_path(instance, filename, app_name, subfolder='', date_format='%Y/%m'):
    """
    표준화된 업로드 경로 생성

    Args:
        instance: Django 모델 인스턴스
        filename (str): 원본 파일명
        app_name (str): 앱 이름
        subfolder (str): 하위 폴더 (선택사항)
        date_format (str): 날짜 형식 (기본값: '%Y/%m')

    Returns:
        str: 업로드 경로

    Example:
        >>> get_upload_path(instance, '문서.txt', 'docs', 'files')
        'docs/files/2025/12/20251211_081530_123456_a1b2c3d4.txt'
    """
    try:
        # 안전한 파일명 생성
        safe_filename = generate_safe_filename(filename)

        # 날짜 경로 생성
        date_path = timezone.now().strftime(date_format)

        # 전체 경로 조합
        if subfolder:
            return os.path.join(app_name, subfolder, date_path, safe_filename)
        else:
            return os.path.join(app_name, date_path, safe_filename)

    except Exception:
        # 백업 경로
        safe_filename = f"{uuid.uuid4().hex}.file"
        return os.path.join(app_name, 'error', safe_filename)


def get_project_upload_path(instance, filename, subfolder=''):
    """
    프로젝트 기반 업로드 경로 생성

    Args:
        instance: 프로젝트 관련 모델 인스턴스
        filename (str): 원본 파일명
        subfolder (str): 하위 폴더 (선택사항)

    Returns:
        str: 프로젝트별 업로드 경로

    Example:
        >>> get_project_upload_path(instance, '문서.txt', 'docs')
        'projects/project-slug/docs/2025/12/20251211_081530_123456_a1b2c3d4.txt'
    """
    try:
        # 프로젝트 slug 추출 (다양한 방법으로 접근 시도)
        project_slug = None

        # 직접 project 속성이 있는 경우
        if hasattr(instance, 'project') and hasattr(instance.project, 'slug'):
            project_slug = instance.project.slug
        # issue_project 속성이 있는 경우 (docs 앱처럼)
        elif hasattr(instance, 'issue_project') and hasattr(instance.issue_project, 'slug'):
            project_slug = instance.issue_project.slug
        # docs.issue_project 속성이 있는 경우 (파일 모델처럼)
        elif hasattr(instance, 'docs') and hasattr(instance.docs, 'issue_project') and hasattr(instance.docs.issue_project, 'slug'):
            project_slug = instance.docs.issue_project.slug
        # 기본 slug 생성
        else:
            project_slug = 'default-project'

        # 안전한 파일명 생성
        safe_filename = generate_safe_filename(filename)

        # 날짜 경로 생성
        date_path = timezone.now().strftime('%Y/%m')

        # 전체 경로 조합
        if subfolder:
            return os.path.join('projects', project_slug, subfolder, date_path, safe_filename)
        else:
            return os.path.join('projects', project_slug, date_path, safe_filename)

    except Exception:
        # 백업 경로
        safe_filename = f"{uuid.uuid4().hex}.file"
        return os.path.join('projects', 'error', safe_filename)


# 앱별 편의 함수들
def get_docs_file_path(instance, filename):
    """docs 앱 파일 업로드 경로"""
    return get_project_upload_path(instance, filename, 'files')


def get_docs_image_path(instance, filename):
    """docs 앱 이미지 업로드 경로"""
    return get_project_upload_path(instance, filename, 'images')


def get_board_file_path(instance, filename):
    """board 앱 파일 업로드 경로"""
    return get_project_upload_path(instance, filename, 'board/files')


def get_board_image_path(instance, filename):
    """board 앱 이미지 업로드 경로"""
    return get_project_upload_path(instance, filename, 'board/images')


def get_work_file_path(instance, filename):
    """work 앱 파일 업로드 경로"""
    return get_project_upload_path(instance, filename, 'work')


def get_contract_file_path(instance, filename):
    """contract 앱 파일 업로드 경로"""
    return get_upload_path(instance, filename, 'contracts', 'files')


def get_company_image_path(instance, filename):
    """company 앱 이미지 업로드 경로"""
    return get_upload_path(instance, filename, 'companies', 'images')


def get_book_image_path(instance, filename):
    """book 앱 이미지 업로드 경로"""
    return get_upload_path(instance, filename, 'books', 'images')


def get_project_file_path(instance, filename):
    """project 앱 파일 업로드 경로"""
    return get_upload_path(instance, filename, 'project', 'files')


# 레거시 호환성을 위한 래퍼 함수들
def legacy_safe_upload_path(instance, filename, base_dir, sub_dir=''):
    """
    기존 함수들과의 호환성을 위한 래퍼 함수

    Args:
        instance: 모델 인스턴스
        filename: 원본 파일명
        base_dir: 기본 디렉토리
        sub_dir: 서브 디렉토리

    Returns:
        str: 안전한 업로드 경로
    """
    safe_filename = generate_safe_filename(filename)
    date_path = timezone.now().strftime('%Y/%m')

    if sub_dir:
        return os.path.join(base_dir, sub_dir, date_path, safe_filename)
    else:
        return os.path.join(base_dir, date_path, safe_filename)