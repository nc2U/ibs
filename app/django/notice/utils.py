import base64
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

import requests
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile

logger = logging.getLogger(__name__)


class IwinvSMSService:
    """iwinv SMS API 서비스 클래스"""

    def __init__(self):
        self.sms_api_url_v2 = "https://sms.bizservice.iwinv.kr/api/v2/send/"
        self.sms_api_url_v1 = "https://sms.bizservice.iwinv.kr/api/send/"
        self.kakao_api_url = "https://alimtalk.bizservice.iwinv.kr/api/v2/send/"
        self.api_key = getattr(settings, 'IWINV_API_KEY', '')
        self.auth_key = getattr(settings, 'IWINV_AUTH_KEY', '')

        if not self.api_key or not self.auth_key:
            raise ValueError("IWINV_API_KEY and IWINV_AUTH_KEY must be set in settings")

    def _get_secret_header(self) -> str:
        """SMS API 인증을 위한 Secret 헤더 생성"""
        secret_string = f"{self.api_key}&{self.auth_key}"
        return base64.b64encode(secret_string.encode('utf-8')).decode('utf-8')

    def _get_kakao_auth_header(self) -> str:
        """카카오 알림톡 API 인증을 위한 AUTH 헤더 생성"""
        return base64.b64encode(self.api_key.encode('utf-8')).decode('utf-8')

    @staticmethod
    def _format_phone_number(phone: str) -> str:
        """전화번호 포맷 정리 (하이픈 제거)"""
        return phone.replace('-', '').replace(' ', '')

    def _validate_recipients(self, recipients: List[str]) -> List[str]:
        """수신자 번호 유효성 검사 및 포맷팅"""
        if not recipients:
            raise ValueError("수신자를 입력해주세요.")

        if len(recipients) > 1000:
            raise ValueError("최대 1000건까지 전송 가능합니다.")

        formatted_recipients = []
        for phone in recipients:
            formatted_phone = self._format_phone_number(phone)
            if len(formatted_phone) < 10 or len(formatted_phone) > 11:
                raise ValueError(f"잘못된 전화번호 형식: {phone}")
            formatted_recipients.append(formatted_phone)

        return formatted_recipients

    @staticmethod
    def _format_datetime(date_str: Optional[str], time_str: Optional[str]) -> Optional[str]:
        """예약 발송을 위한 날짜/시간 포맷팅"""
        if not date_str or not time_str:
            return None

        try:
            # YYYY-MM-DD HH:mm:ss 형식으로 변환
            datetime_str = f"{date_str} {time_str}:00"
            # 유효성 검사
            datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
            return datetime_str
        except ValueError:
            raise ValueError("날짜와 시간 표현 형식(예: 2015-09-02 14:17:03)에 맞춰 입력하여 주십시오.")

    def send_sms(self,
                 recipients: List[str],
                 message: str,
                 sender_number: str,
                 schedule_date: Optional[str] = None,
                 schedule_time: Optional[str] = None,
                 use_v2_api: bool = True) -> Dict[str, Any]:
        """
        단문(SMS) 발송

        Args:
            recipients: 수신자 번호 리스트
            message: 메시지 내용 (90byte 초과시 자동으로 LMS로 발송)
            sender_number: 발신번호
            schedule_date: 예약 발송 날짜 (YYYY-MM-DD)
            schedule_time: 예약 발송 시간 (HH:mm)
            use_v2_api: v2 API 사용 여부 (기본값: True)

        Returns:
            API 응답 결과
        """
        try:
            # 수신자 유효성 검사
            formatted_recipients = self._validate_recipients(recipients)
            formatted_sender = self._format_phone_number(sender_number)

            # 예약 발송 시간 포맷팅
            scheduled_datetime = self._format_datetime(schedule_date, schedule_time)

            # API 요청 데이터 구성
            payload = {
                "version": "1.0",
                "from": formatted_sender,
                "to": formatted_recipients,
                "text": message,
                "date": scheduled_datetime
            }

            # 헤더 구성
            headers = {
                'Content-Type': 'application/json;charset=UTF-8',
                'secret': self._get_secret_header()
            }

            # API URL 선택
            api_url = self.sms_api_url_v2 if use_v2_api else self.sms_api_url_v1

            # API 요청
            response = requests.post(
                api_url,
                json=payload,
                headers=headers,
                timeout=30,
                verify=True
            )

            response.raise_for_status()
            result = response.json()

            # 로깅
            logger.info(f"SMS 발송 요청: {len(recipients)}명, 결과: {result.get('resultCode')}")

            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"SMS API 요청 실패: {str(e)}")
            return {
                "resultCode": -1,
                "message": f"API 요청 실패: {str(e)}",
                "requestNo": None,
                "msgType": "SMS"
            }
        except Exception as e:
            logger.error(f"SMS 발송 중 오류: {str(e)}")
            return {
                "resultCode": -1,
                "message": f"발송 중 오류: {str(e)}",
                "requestNo": None,
                "msgType": "SMS"
            }

    def send_lms(self,
                 recipients: List[str],
                 message: str,
                 title: str,
                 sender_number: str,
                 schedule_date: Optional[str] = None,
                 schedule_time: Optional[str] = None,
                 use_v2_api: bool = True) -> Dict[str, Any]:
        """
        장문(LMS) 발송

        Args:
            recipients: 수신자 번호 리스트
            message: 메시지 내용 (최대 2000byte)
            title: 제목 (최대 40byte)
            sender_number: 발신번호
            schedule_date: 예약 발송 날짜 (YYYY-MM-DD)
            schedule_time: 예약 발송 시간 (HH:mm)
            use_v2_api: v2 API 사용 여부 (기본값: True)

        Returns:
            API 응답 결과
        """
        try:
            # 입력값 유효성 검사
            if len(title.encode('utf-8')) > 40:
                raise ValueError("제목은 40 Byte까지만 입력이 가능합니다.")

            if len(message.encode('utf-8')) > 2000:
                raise ValueError("장문 메시지는 2000 Bytes까지만 입력이 가능합니다.")

            # 수신자 유효성 검사
            formatted_recipients = self._validate_recipients(recipients)
            formatted_sender = self._format_phone_number(sender_number)

            # 예약 발송 시간 포맷팅
            scheduled_datetime = self._format_datetime(schedule_date, schedule_time)

            # API 요청 데이터 구성
            payload = {
                "version": "1.0",
                "from": formatted_sender,
                "to": formatted_recipients,
                "title": title,
                "text": message,
                "date": scheduled_datetime
            }

            # 헤더 구성
            headers = {
                'Content-Type': 'application/json;charset=UTF-8',
                'secret': self._get_secret_header()
            }

            # API URL 선택
            api_url = self.sms_api_url_v2 if use_v2_api else self.sms_api_url_v1

            # API 요청
            response = requests.post(
                api_url,
                json=payload,
                headers=headers,
                timeout=30,
                verify=True
            )

            response.raise_for_status()
            result = response.json()

            # 로깅
            logger.info(f"LMS 발송 요청: {len(recipients)}명, 결과: {result.get('resultCode')}")

            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"LMS API 요청 실패: {str(e)}")
            return {
                "resultCode": -1,
                "message": f"API 요청 실패: {str(e)}",
                "requestNo": None,
                "msgType": "LMS"
            }
        except Exception as e:
            logger.error(f"LMS 발송 중 오류: {str(e)}")
            return {
                "resultCode": -1,
                "message": f"발송 중 오류: {str(e)}",
                "requestNo": None,
                "msgType": "LMS"
            }

    def send_mms(self,
                 recipients: List[str],
                 message: str,
                 title: str,
                 sender_number: str,
                 image_file: InMemoryUploadedFile,
                 schedule_date: Optional[str] = None,
                 schedule_time: Optional[str] = None,
                 use_v2_api: bool = True) -> Dict[str, Any]:
        """
        포토(MMS) 발송

        Args:
            recipients: 수신자 번호 리스트
            message: 메시지 내용 (최대 2000byte)
            title: 제목 (최대 40byte)
            sender_number: 발신번호
            image_file: 이미지 파일 (100KB 미만 JPG)
            schedule_date: 예약 발송 날짜 (YYYY-MM-DD)
            schedule_time: 예약 발송 시간 (HH:mm)
            use_v2_api: v2 API 사용 여부 (기본값: True)

        Returns:
            API 응답 결과
        """
        try:
            # 입력값 유효성 검사
            if len(title.encode('utf-8')) > 40:
                raise ValueError("제목은 40 Byte까지만 입력이 가능합니다.")

            if len(message.encode('utf-8')) > 2000:
                raise ValueError("장문 메시지는 2000 Bytes까지만 입력이 가능합니다.")

            # 이미지 파일 유효성 검사
            if image_file.size > 100 * 1024:  # 100KB
                raise ValueError("파일 업로드는 100KB까지 가능합니다.")

            if not image_file.name.lower().endswith('.jpg'):
                raise ValueError("허용되지 않는 파일 확장자입니다. JPG 파일만 가능합니다.")

            # 수신자 유효성 검사 및 포맷팅 (MMS는 단일 발송을 위해 배열을 쿼리 스트링으로 변환)
            formatted_recipients = self._validate_recipients(recipients)
            formatted_sender = self._format_phone_number(sender_number)

            # 예약 발송 시간 포맷팅
            scheduled_datetime = self._format_datetime(schedule_date, schedule_time)

            # MMS는 multipart/form-data 형식으로 전송
            # 수신자 번호를 쿼리 스트링 형태로 변환 (PHP의 http_build_query와 동일)
            to_query_string = '&'.join([f'0={phone}' for phone in formatted_recipients])

            # Form data 구성
            form_data = {
                'version': '1.0',
                'from': formatted_sender,
                'to': to_query_string,
                'title': title,
                'text': message,
                'date': scheduled_datetime
            }

            # 파일 데이터
            files = {
                'image': (image_file.name, image_file.read(), image_file.content_type)
            }

            # 헤더 구성 (multipart/form-data는 requests가 자동으로 설정)
            headers = {
                'secret': self._get_secret_header()
            }

            # API URL 선택
            api_url = self.sms_api_url_v2 if use_v2_api else self.sms_api_url_v1

            # API 요청
            response = requests.post(
                api_url,
                data=form_data,
                files=files,
                headers=headers,
                timeout=60,  # 이미지 업로드를 위해 타임아웃 증가
                verify=True
            )

            response.raise_for_status()
            result = response.json()

            # 로깅
            logger.info(f"MMS 발송 요청: {len(recipients)}명, 결과: {result.get('resultCode')}")

            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"MMS API 요청 실패: {str(e)}")
            return {
                "resultCode": -1,
                "message": f"API 요청 실패: {str(e)}",
                "requestNo": None,
                "msgType": "MMS"
            }
        except Exception as e:
            logger.error(f"MMS 발송 중 오류: {str(e)}")
            return {
                "resultCode": -1,
                "message": f"발송 중 오류: {str(e)}",
                "requestNo": None,
                "msgType": "MMS"
            }

    def send_auto_message(self,
                          recipients: List[str],
                          message: str,
                          sender_number: str,
                          title: Optional[str] = None,
                          schedule_date: Optional[str] = None,
                          schedule_time: Optional[str] = None) -> Dict[str, Any]:
        """
        자동 메시지 타입 판별 발송
        90byte 이하: SMS, 초과: LMS로 자동 발송

        Args:
            recipients: 수신자 번호 리스트
            message: 메시지 내용
            sender_number: 발신번호
            title: 제목 (LMS용, 없으면 자동 생성)
            schedule_date: 예약 발송 날짜
            schedule_time: 예약 발송 시간

        Returns:
            API 응답 결과
        """
        message_bytes = len(message.encode('utf-8'))

        if message_bytes <= 90:
            # SMS 발송
            return self.send_sms(
                recipients=recipients,
                message=message,
                sender_number=sender_number,
                schedule_date=schedule_date,
                schedule_time=schedule_time
            )
        else:
            # LMS 발송
            if not title:
                title = message[:20] + "..." if len(message) > 20 else message

            return self.send_lms(
                recipients=recipients,
                message=message,
                title=title,
                sender_number=sender_number,
                schedule_date=schedule_date,
                schedule_time=schedule_time
            )

    def send_kakao_alimtalk(self,
                            recipients: List[Dict[str, Any]],
                            template_code: str,
                            sender_number: str,
                            reserve: bool = False,
                            send_date: Optional[str] = None,
                            send_time: Optional[str] = None,
                            re_send: bool = False,
                            resend_type: str = 'Y',
                            resend_title: Optional[str] = None,
                            resend_content: Optional[str] = None) -> Dict[str, Any]:
        """
        카카오 알림톡 발송

        Args:
            recipients: 수신자 정보 리스트 [{"phone": "01012345678", "template_param": ["값1", "값2"]}]
            template_code: 템플릿 코드
            sender_number: 발신번호 (사전 등록된 번호)
            reserve: 예약 발송 여부
            send_date: 예약 발송 날짜 (YYYY-MM-DD)
            send_time: 예약 발송 시간 (HH:mm)
            re_send: 실패 시 대체 문자 발송 여부
            resend_type: 대체 발송 내용 타입 (Y: 알림톡 내용, N: 직접 입력)
            resend_title: 대체 문자 제목 (LMS용)
            resend_content: 대체 문자 내용

        Returns:
            API 응답 결과
        """
        try:
            # 수신자 유효성 검사
            if not recipients or len(recipients) > 10000:
                raise ValueError("수신자는 1명 이상 10,000명 이하여야 합니다.")

            # 전화번호 포맷팅 및 유효성 검사
            formatted_recipients = []
            for recipient in recipients:
                phone = self._format_phone_number(recipient.get('phone', ''))
                if len(phone) < 10 or len(phone) > 11:
                    raise ValueError(f"잘못된 전화번호 형식: {recipient.get('phone')}")

                formatted_recipient = {
                    "phone": phone,
                    "templateParam": recipient.get('template_param', [])
                }
                formatted_recipients.append(formatted_recipient)

            # 예약 발송 시간 포맷팅
            scheduled_datetime = None
            if reserve:
                if not send_date or not send_time:
                    raise ValueError("예약 발송 시 날짜와 시간을 모두 입력해야 합니다.")
                scheduled_datetime = self._format_datetime(send_date, send_time)

            # 발신번호 포맷팅
            formatted_sender = self._format_phone_number(sender_number)

            # API 요청 데이터 구성
            payload = {
                "templateCode": template_code,
                "reserve": "Y" if reserve else "N",
                "list": formatted_recipients
            }

            # 예약 발송 데이터 추가
            if scheduled_datetime:
                payload["sendDate"] = scheduled_datetime

            # 대체 발송 설정
            if re_send:
                payload.update({
                    "reSend": "Y",
                    "resendCallback": formatted_sender,
                    "resendType": resend_type
                })

                if resend_type == "N":  # 직접 입력
                    if not resend_content:
                        raise ValueError("대체 발송 내용 타입이 직접 입력일 때 대체 문자 내용이 필요합니다.")
                    payload["resendContent"] = resend_content
                    if resend_title:
                        payload["resendTitle"] = resend_title
            else:
                payload["reSend"] = "N"

            # 헤더 구성
            headers = {
                'Content-Type': 'application/json;charset=UTF-8',
                'AUTH': self._get_kakao_auth_header()
            }

            # API 요청
            response = requests.post(
                self.kakao_api_url,
                json=payload,
                headers=headers,
                timeout=30,
                verify=True
            )

            response.raise_for_status()
            result = response.json()

            # 로깅
            logger.info(f"카카오 알림톡 발송 요청: {len(recipients)}명, 결과: {result.get('code')}")

            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"카카오 알림톡 API 요청 실패: {str(e)}")
            return {
                "code": -1,
                "message": f"API 요청 실패: {str(e)}",
                "success": 0,
                "fail": len(recipients) if recipients else 0
            }
        except Exception as e:
            logger.error(f"카카오 알림톡 발송 중 오류: {str(e)}")
            return {
                "code": -1,
                "message": f"발송 중 오류: {str(e)}",
                "success": 0,
                "fail": len(recipients) if recipients else 0
            }

    @staticmethod
    def get_error_message(result_code: int) -> str:
        """결과 코드에 따른 에러 메시지 반환"""
        error_messages = {
            0: "전송 성공",
            1: "메시지가 전송되지 않았습니다.",
            11: "운영 중인 서비스가 아닙니다.",
            12: "요금제 충전 중입니다. 잠시 후 다시 시도해 보시기 바랍니다.",
            13: "등록되지 않은 발신번호입니다.",
            14: "인증 요청이 올바르지 않습니다.",
            15: "등록하지 않은 IP에서는 발송되지 않습니다.",
            21: "장문 메시지는 2000 Bytes까지만 입력이 가능합니다.",
            22: "제목 입력 가능 문자 : 한글, 영어, 숫자 허용된 특수문자는 [ ] ( ) <> 입니다.",
            23: "제목은 40 Byte까지만 입력이 가능합니다.",
            31: "파일 업로드는 100KB까지 가능합니다.",
            32: "허용되지 않는 파일 확장자입니다.",
            33: "이미지 업로드에 실패했습니다.",
            41: "수신 번호를 입력하여 주세요.",
            42: "예약 전송은 현재 시간 15분 이후 한달 이전까지만 가능",
            43: "날짜와 시간 표현 형식(예: 2015-09-02 14:17:03)에 맞춰 입력하여 주십시오.",
            44: "최대 1000건 전송 가능합니다.",
            50: "SMS 자동 충전 하루 5번 충전 한도를 초과하였습니다."
        }

        return error_messages.get(result_code, f"알 수 없는 오류 (코드: {result_code})")

    @staticmethod
    def get_kakao_error_message(code: int) -> str:
        """카카오 알림톡 결과 코드에 따른 에러 메시지 반환"""
        kakao_error_messages = {
            200: "메시지가 발송되었습니다.",
            501: "{templateCode}값을 정확히 입력해 주세요.",
            502: "{list}값을 정확히 입력해 주세요.",
            503: "{reSend}값을 정확히 입력해 주세요.",
            504: "유효하지 않는 값(resendType)입니다.",
            505: "발신번호는 발신번호 관리에서 사전에 등록된 발신번호로만 발송이 가능합니다.",
            506: "유효하지 않는 값(sendDate)입니다.",
            507: "예약 전송은 현재 시간 15분 이후 이틀 이전까지만 가능합니다.",
            508: "templateParam은(는) 필수 입력 항목입니다.",
            509: "메시지 내용이 템플릿과 일치하지 않습니다.",
            510: "제목은 40 Bytes 까지만 입력이 가능합니다.",
            511: "제목 입력 가능 문자 : 한글, 영어, 숫자, 허용된 특수문자는 ( [ ] ( ) < > )입니다.",
            512: "수신 번호를 입력하여 주세요.",
            513: "핸드폰 번호 형식(예: 010-1234-45678 혹은 01012345678)에 맞춰 입력하여 주십시오.",
            514: "알림톡 발송은 1회 최대 10,000건까지 전송 가능합니다.",
            515: "대체 발송 메시지는 1,000자까지만 입력이 가능합니다.",
            516: "대체 발송으로 알림톡 내용 발송 시 변수가 치환되어 1,000자까지만 입력할 수 있습니다.",
            517: "알림톡 메시지 변수가 치환되어 1,000자까지만 입력할 수 있습니다.",
            518: "요금 충전 호출에 실패했습니다.",
            519: "잔액이 부족합니다.",
            540: "금칙어가 포함되어 메시지 발송이 금지됩니다."
        }

        return kakao_error_messages.get(code, f"알 수 없는 오류 (코드: {code})")
