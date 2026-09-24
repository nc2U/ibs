import json
import logging
import re
from typing import Dict, Any, Optional
from django.conf import settings
import requests

logger = logging.getLogger(__name__)

PRIMARY_GEMINI_MODEL = "gemini-3.5-flash-lite"
FALLBACK_GEMINI_MODEL = "gemini-3-flash-preview"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_UPLOAD_URL = f"https://generativelanguage.googleapis.com/upload/v1beta/files"
GEMINI_FILE_URL = f"{GEMINI_BASE_URL}/files"

SYSTEM_PROMPT = """당신은 회의 음성 녹취를 듣고 회의록을 작성하는 전문 서기(기록관)입니다.

[절대 원칙 - 사실(Fact) 기반 작성]
1. 반드시 제공된 음성 파일에서 참석자가 "실제로 말한 내용(음성 인식 결과)"에 기반하여 작성해야 합니다.
2. 음성에 나오지 않는 가상의 안건, 허위 결정사항, 존재하지 않는 인물이나 내용을 지어내는 행위(환각, Hallucination)를 엄격히 금지합니다.
3. 음성 발화의 실제 분량과 의미에 맞추어 비례하여 작성하세요.
   - 단문/테스트 발화인 경우: 발화된 사실만을 간결하게 정리하고, 결정사항/조치과제가 음성에 없으면 "없음"으로 작성.
   - 실제 긴 회의인 경우: 논의된 세부 내용, 결정사항, 조치과제를 체계적으로 정리.
4. 조치과제(Action Item)는 음성에 실제로 언급된 경우에만 다음 양식으로 작성하세요:
   - [ ] 조치내용 (담당: 담당자명 / 기한: YYYY-MM-DD)
   (담당자나 기한이 음성에 언급되지 않았으면 빈칸 유지: - [ ] 조치내용 (담당: / 기한: ))
   (조치과제가 음성에 전혀 언급되지 않았다면 "없음"으로 작성)
5. 음성에 사람의 목소리가 없거나(묵음, 잡음만 있는 경우), 식별 불가능한 경우:
   - title: "녹음 내용 없음"
   - content: "음성에서 인식된 회의 발화 내용이 없습니다."
   - agenda, decisions, action_items: "없음"

반드시 아래 JSON 스키마 형식으로만 응답하세요:
{
  "title": "실제 발화된 음성 내용을 가장 잘 표현하는 회의 제목",
  "category_name": "경영/기획, 정기/주간, 내부/협의, 대외/협력, 기타/임시 중 실제 내용에 가장 적합한 카테고리 1개",
  "agenda": "실제 음성에서 다룬 안건 (번호 매김 형식 또는 요약)",
  "content": "실제 음성 발화 내용을 마크다운으로 정리한 본문",
  "decisions": "실제 음성에서 결정된 사항",
  "action_items": "실제 음성에서 언급된 후속 조치 과제"
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
                "temperature": 0.0
            }
        }

        resp = _post_generate_content(request_body, api_key)
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
                    "temperature": 0.0
                }
            }

            resp = _post_generate_content(request_body, api_key)
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


def _post_generate_content(request_body: Dict[str, Any], api_key: str) -> requests.Response:
    """기본 모델(gemini-3.5-flash-lite)로 호출하고 실패 시 fallback 모델(gemini-3-flash-preview)로 재시도합니다."""
    models_to_try = [PRIMARY_GEMINI_MODEL, FALLBACK_GEMINI_MODEL]
    last_error_text = ""
    last_status = 500

    for model in models_to_try:
        url = f"{GEMINI_BASE_URL}/models/{model}:generateContent?key={api_key}"
        try:
            resp = requests.post(url, json=request_body, timeout=120)
            if resp.ok:
                return resp
            last_status = resp.status_code
            last_error_text = resp.text
            logger.warning("Gemini model %s call failed (%s): %s", model, resp.status_code, resp.text)
        except Exception as e:
            last_error_text = str(e)
            logger.warning("Gemini model %s request exception: %s", model, e)

    raise RuntimeError(f"Gemini API 호출 실패 ({last_status}): {last_error_text}")


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
