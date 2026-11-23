"""
계약자 고유식별정보(주민등록번호) 검증·암복호화·해싱 유틸리티
"""
import base64
import datetime
import hashlib
import hmac
import re

from cryptography.fernet import Fernet, InvalidToken, MultiFernet
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.utils import timezone


def _resolve_fernet_keys() -> list[bytes]:
    configured = [
        k.strip().encode('utf-8')
        for k in getattr(settings, 'RRN_ENCRYPTION_KEYS', [])
        if str(k).strip()
    ]
    if configured:
        return configured
    if getattr(settings, 'DEBUG', False):
        # 개발/로컬 테스트 환경 전용 결정적 폴백 키 (운영 DEBUG=False에서는 차단)
        digest = hashlib.sha256(f'ibs-dev-rrn:{settings.SECRET_KEY}'.encode('utf-8')).digest()
        return [base64.urlsafe_b64encode(digest)]
    raise ImproperlyConfigured('운영 환경에서는 RRN_ENCRYPTION_KEYS 환경변수가 필수입니다.')


def _get_fernet() -> MultiFernet:
    return MultiFernet([Fernet(key) for key in _resolve_fernet_keys()])


def _resolve_hash_key() -> bytes:
    hash_key = str(getattr(settings, 'RRN_HASH_KEY', '') or '').strip()
    if hash_key:
        return hash_key.encode('utf-8')
    keys = _resolve_fernet_keys()
    return keys[0]


def normalize_and_parse_rrn(raw_rrn: str) -> tuple[str, datetime.date, str, str]:
    """
    주민등록번호를 정규화하고 형식/생년월일/성별코드를 검증합니다.
    (2020년 10월 이후 뒷자리 임의번호 체계 반영으로 13번째 체크섬은 강제하지 않음)

    Returns:
        (digits_13, birth_date, gender('M'|'F'), masked_rrn)
    """
    digits = re.sub(r'\D', '', str(raw_rrn or ''))
    if len(digits) != 13:
        raise ValidationError('주민등록번호는 숫자 13자리여야 합니다.')

    yy = int(digits[0:2])
    mm = int(digits[2:4])
    dd = int(digits[4:6])
    gender_code = digits[6]

    century_map = {
        '1': 1900, '2': 1900, '5': 1900, '6': 1900,
        '3': 2000, '4': 2000, '7': 2000, '8': 2000,
        '9': 1800, '0': 1800,
    }
    if gender_code not in century_map:
        raise ValidationError('유효하지 않은 주민등록번호 성별 코드입니다.')

    try:
        birth_date = datetime.date(century_map[gender_code] + yy, mm, dd)
    except ValueError as exc:
        raise ValidationError('주민등록번호 앞자리의 생년월일이 올바르지 않습니다.') from exc

    if birth_date > timezone.localdate():
        raise ValidationError('주민등록번호 생년월일이 현재 날짜보다 미래일 수 없습니다.')

    gender = 'M' if gender_code in ('1', '3', '5', '7', '9') else 'F'
    masked = f'{digits[:6]}-{gender_code}******'
    return digits, birth_date, gender, masked


def encrypt_rrn(digits: str) -> str:
    return _get_fernet().encrypt(digits.encode('utf-8')).decode('utf-8')


def decrypt_rrn(token: str, formatted: bool = True) -> str:
    try:
        digits = _get_fernet().decrypt(token.encode('utf-8')).decode('utf-8')
    except InvalidToken as exc:
        raise ValidationError('저장된 주민등록번호 복호화에 실패했습니다. 암호화 키를 확인하십시오.') from exc
    return f'{digits[:6]}-{digits[6:]}' if formatted else digits


def hash_rrn(digits: str) -> str:
    """프로젝트 내 동일인 식별/중복 확인용 HMAC-SHA256 Blind Index"""
    return hmac.new(_resolve_hash_key(), digits.encode('utf-8'), hashlib.sha256).hexdigest()


def get_client_ip(request) -> str | None:
    """요청 클라이언트 IP 추출 (프록시 X-Forwarded-For 우선)"""
    if not request:
        return None
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip() or None
    return request.META.get('REMOTE_ADDR') or None
