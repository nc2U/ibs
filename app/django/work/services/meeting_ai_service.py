import json
import logging
import re
from typing import Dict, Any, Optional
from django.conf import settings
import requests

logger = logging.getLogger(__name__)

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
GEMINI_UPLOAD_URL = "https://generativelanguage.googleapis.com/upload/v1beta/files"
GEMINI_FILE_URL = "https://generativelanguage.googleapis.com/v1beta/files"

SYSTEM_PROMPT = """당신은 건설 시행 및 부동산 개발 회사의 전문 서기(회의 기록관)입니다.
제공된 회의 음성 녹음을 듣고, 한국어로 건설/시행/시공 실무 맥락에 맞추어 정확하게 분석한 후, 반드시 아래 JSON 형식으로만 응답하세요. 다른 설명이나 마크다운 백틱(```json) 없이 순수 JSON 문자열만 출력하세요.

{
  "title": "회의의 핵심 주제와 목적이 명확히 드러나는 제목 (예: [인허가협의] 교육영향평가 보완 대책 회의)",
  "category_name": "경영/기획, 정기/주간, 내부/협의, 대외/협력, 기타/임시 중 가장 부합하는 카테고리명 1개",
  "agenda": "회의에서 다루어진 주요 안건들을 번호 매김 형식으로 정리 (예:\n1. 교육영향평가 2차 보완 요청 사항 점검\n2. 일조권 시뮬레이션 결과 검토)",
  "content": "회의에서 오간 논의 내용 및 세부 발언 요지를 마크다운 형식으로 체계적으로 정리",
  "decisions": "회의를 통해 최종 합의되거나 확정된 핵심 결정 사항들을 불릿 또는 번호 형식으로 정리",
  "action_items": "회의 후속 조치 사항들을 정확히 다음 양식으로 작성:\n- [ ] 조치내용 (담당: 담당자명 / 기한: YYYY-MM-DD)\n(만약 담당자나 기한이 음성에 명시되지 않았으면 빈칸으로 남김: - [ ] 조치내용 (담당: / 기한: ))"
}
"""


def summarize_meeting_audio(audio_bytes: bytes, mime_type: str = 'audio/webm') -> Dict[str, Any]:
    """
    회의 음성 데이터를 Google Gemini 1.5 Flash에 전송하여
    회의록 구조화 데이터(제목, 카테고리, 의제, 본문, 결정사항, 액션아이템)를 추출합니다.
    """
    api_key = getattr(settings, 'GEMINI_API_KEY', '')
    if not api_key:
        raise ValueError("GEMINI_API_KEY가 설정되어 있지 않습니다. .env 파일에 GEMINI_API_KEY를 등록해 주세요.")

    # 1. 파일 크기 체크 (20MB 미만은 직접 inlineData base64 전송, 이상은 Resumable Upload API 사용)
    import base64
    file_size = len(audio_bytes)

    if file_size <= 20 * 1024 * 1024:
        # Inline Base64 Data
        b64_audio = base64.b64encode(audio_bytes).decode('utf-8')
        request_body = {
            "system_instruction": {
                "parts": [{"text": SYSTEM_PROMPT}]
            },
            "contents": [
                {
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": b64_audio
                            }
                        },
                        {
                            "text": "이 회의 음성을 듣고 시스템 지침에 정의된 JSON 규격에 맞추어 회의록을 작성해 주세요."
                        }
                    ]
                }
            ],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.2
            }
        }

        resp = requests.post(
            f"{GEMINI_API_URL}?key={api_key}",
            json=request_body,
            timeout=120
        )
        if not resp.ok:
            logger.error("Gemini API Error: %s %s", resp.status_code, resp.text)
            raise RuntimeError(f"Gemini API 호출 실패 ({resp.status_code}): {resp.text}")

        result_json = resp.json()
        return _extract_meeting_data(result_json)

    else:
        # 20MB 초과 대용량 파일: Files API 업로드 -> 분석 -> 완료 즉시 Files API에서 삭제
        file_name = None
        try:
            # Step 1: Upload to Gemini Files API
            upload_headers = {
                "X-Goog-Upload-Command": "start, upload, finalize",
                "X-Goog-Upload-Header-Content-Length": str(file_size),
                "X-Goog-Upload-Header-Content-Type": mime_type,
                "Content-Type": mime_type
            }
            upload_resp = requests.post(
                f"{GEMINI_UPLOAD_URL}?key={api_key}",
                headers=upload_headers,
                data=audio_bytes,
                timeout=180
            )
            if not upload_resp.ok:
                raise RuntimeError(f"Gemini Files Upload Error ({upload_resp.status_code}): {upload_resp.text}")

            upload_result = upload_resp.json()
            file_uri = upload_result['file']['uri']
            file_name = upload_result['file']['name']

            # Step 2: Generate Content with fileData
            request_body = {
                "system_instruction": {
                    "parts": [{"text": SYSTEM_PROMPT}]
                },
                "contents": [
                    {
                        "parts": [
                            {
                                "file_data": {
                                    "mime_type": mime_type,
                                    "file_uri": file_uri
                                }
                            },
                            {
                                "text": "이 회의 음성을 듣고 시스템 지침에 정의된 JSON 규격에 맞추어 회의록을 작성해 주세요."
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "response_mime_type": "application/json",
                    "temperature": 0.2
                }
            }

            resp = requests.post(
                f"{GEMINI_API_URL}?key={api_key}",
                json=request_body,
                timeout=180
            )
            if not resp.ok:
                raise RuntimeError(f"Gemini API 호출 실패 ({resp.status_code}): {resp.text}")

            result_json = resp.json()
            return _extract_meeting_data(result_json)

        finally:
            # Step 3: 반드시 원격 파일 즉시 삭제 (보안 및 스토리지 관리)
            if file_name:
                try:
                    del_resp = requests.delete(f"{GEMINI_FILE_URL}/{file_name}?key={api_key}", timeout=10)
                    if del_resp.ok:
                        logger.info("Successfully deleted remote Gemini file: %s", file_name)
                except Exception as del_err:
                    logger.warning("Failed to delete remote Gemini file %s: %s", file_name, del_err)


def _extract_meeting_data(api_response: Dict[str, Any]) -> Dict[str, Any]:
    """Gemini API 응답에서 text를 꺼내 JSON 객체로 파싱합니다."""
    candidates = api_response.get('candidates', [])
    if not candidates:
        raise ValueError("Gemini API로부터 응답 후보를 받지 못했습니다.")

    parts = candidates[0].get('content', {}).get('parts', [])
    if not parts:
        raise ValueError("Gemini 응답 내용이 비어 있습니다.")

    raw_text = parts[0].get('text', '').strip()

    # Markdown 백틱 제거
    cleaned = re.sub(r'^```json\s*', '', raw_text, flags=re.MULTILINE)
    cleaned = re.sub(r'```\s*$', '', cleaned, flags=re.MULTILINE).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as err:
        logger.error("Failed to decode JSON from Gemini output: %s", cleaned)
        raise ValueError(f"AI 회의록 JSON 파싱 실패: {err}")
