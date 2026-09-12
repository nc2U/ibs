import os
import base64
from celery import shared_task
from django.core.cache import cache
from .seal_extractor import extract_seals_from_file


@shared_task(bind=True)
def extract_seals_task(self, temp_file_path, is_pdf=True):
    """
    Celery 워커에서 스캔 파일(PDF 또는 이미지)을 처리하여 인장들을 추출하는 비동기 태스크

    Args:
        temp_file_path (str): 임시 저장된 스캔 파일 경로
        is_pdf (bool): PDF 여부
    """
    task_id = self.request.id
    cache_key = f"seal_extraction_{task_id}"

    # 진행 상태 캐시에 저장 (5분 TTL)
    cache.set(cache_key, {'status': 'PROGRESS', 'message': '인장 감지 및 이미지 분석 중...'}, timeout=300)

    try:
        with open(temp_file_path, 'rb') as f:
            file_bytes = f.read()

        detected = extract_seals_from_file(file_bytes, is_pdf=is_pdf)

        # Celery 결과 및 캐시 저장을 위해 bytes는 제외하고 base64 프리뷰 위주로 가공
        serializable_results = []
        for seal in detected:
            serializable_results.append({
                'index': seal['index'],
                'position_hint': seal['position_hint'],
                'preview_base64': seal['preview_base64'],
                'width': seal['width'],
                'height': seal['height'],
            })

        result_data = {
            'status': 'SUCCESS',
            'seals': serializable_results,
            'count': len(serializable_results),
        }
        cache.set(cache_key, result_data, timeout=600)
        return result_data

    except Exception as exc:
        error_data = {
            'status': 'FAILURE',
            'error': str(exc),
        }
        cache.set(cache_key, error_data, timeout=300)
        raise exc

    finally:
        # 임시 파일 삭제 정리
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except OSError:
                pass
