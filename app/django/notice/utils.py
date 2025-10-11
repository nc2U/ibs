import base64
from datetime import datetime
from typing import List, Optional, Dict, Any

import requests
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile


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

            return result

        except requests.exceptions.RequestException as e:
            return {
                "resultCode": -1,
                "message": f"API 요청 실패: {str(e)}",
                "requestNo": None,
                "msgType": "SMS"
            }
        except Exception as e:
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

            return result

        except requests.exceptions.RequestException as e:
            return {
                "resultCode": -1,
                "message": f"API 요청 실패: {str(e)}",
                "requestNo": None,
                "msgType": "LMS"
            }
        except Exception as e:
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

            return result

        except requests.exceptions.RequestException as e:
            return {
                "resultCode": -1,
                "message": f"API 요청 실패: {str(e)}",
                "requestNo": None,
                "msgType": "MMS"
            }
        except Exception as e:
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

            return result

        except requests.exceptions.RequestException as e:
            return {
                "code": -1,
                "message": f"API 요청 실패: {str(e)}",
                "success": 0,
                "fail": len(recipients) if recipients else 0
            }
        except Exception as e:
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

    def get_send_history(self,
                        company_id: str,
                        start_date: str,
                        end_date: str,
                        request_no: Optional[str] = None,
                        page_num: int = 1,
                        page_size: int = 15,
                        phone: Optional[str] = None) -> Dict[str, Any]:
        """
        전송 내역 조회 (최근 90일 이내)

        Args:
            company_id: 조직(업체) 발송 아이디
            start_date: 발송 요청 시작일자 (YYYY-MM-DD)
            end_date: 발송 요청 마감일자 (YYYY-MM-DD)
            request_no: 메시지 발송요청 고유번호 (선택)
            page_num: 페이지 번호 (기본:1)
            page_size: 조회 건수 (기본:15, 최대:1000)
            phone: 수신번호 (선택)

        Returns:
            API 응답 결과
        """
        try:
            # 날짜 유효성 검사
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d")
                end = datetime.strptime(end_date, "%Y-%m-%d")

                # 90일 이내 체크
                if (end - start).days > 90:
                    raise ValueError("조회 기간은 90일 이내만 가능합니다.")

                if start > end:
                    raise ValueError("시작일이 마감일보다 늦을 수 없습니다.")

            except ValueError as e:
                if "does not match format" in str(e):
                    raise ValueError("날짜 형식은 YYYY-MM-DD 형식이어야 합니다.")
                raise

            # 페이지 크기 검증
            if page_size > 1000:
                raise ValueError("조회 건수는 최대 1000건까지 가능합니다.")

            # API 요청 데이터 구성
            # 주의: iwinv API는 pageSize 파라미터를 지원하지 않음 (API 버그)
            # pageNum만 전송하고 pageSize는 제외
            page_num_str = str(page_num) if page_num is not None else "1"

            payload = {
                "version": "1.0",
                "companyid": company_id,
                "startDate": start_date,
                "endDate": end_date,
                "pageNum": page_num_str
            }

            # 선택적 파라미터 추가
            if request_no:
                payload["requestNo"] = str(request_no)
            if phone:
                payload["phone"] = self._format_phone_number(phone)

            # 헤더 구성
            headers = {
                'Content-Type': 'application/json;charset=UTF-8',
                'secret': self._get_secret_header()
            }

            # API 요청
            response = requests.post(
                "https://sms.bizservice.iwinv.kr/api/history/",
                json=payload,
                headers=headers,
                timeout=30,
                verify=True
            )

            response.raise_for_status()
            result = response.json()

            return result

        except requests.exceptions.RequestException as e:
            return {
                "resultCode": -1,
                "message": f"API 요청 실패: {str(e)}",
                "totalCount": 0,
                "list": []
            }
        except Exception as e:
            return {
                "resultCode": -1,
                "message": f"조회 중 오류: {str(e)}",
                "totalCount": 0,
                "list": []
            }

    @staticmethod
    def get_send_status_message(msg_type: str, status_code: str) -> str:
        """전송 결과 코드에 따른 상태 메시지 반환"""

        # SMS 전송 결과 코드
        sms_status_messages = {
            "0": "전송 대기 중",
            "WAIT": "전송 대기 중",
            "01": "시스템 장애",
            "02": "인증실패, 직후 연결을 끊음",
            "03": "메시지 형식 오류",
            "04": "BIND 안됨",
            "06": "전송 성공",
            "07": "비가입자, 결번, 서비스정지",
            "08": "단말기 Power-off 상태",
            "09": "음영",
            "10": "단말기 메시지 FULL",
            "11": "타임아웃",
            "17": "CallbackURL 사용자 아님",
            "18": "메시지 중복 발송",
            "19": "월 송신 건수 초과",
            "20": "이동통신사에서 정의되지 않은 결과 코드",
            "21": "착신번호 에러(자리수 에러)",
            "22": "착신번호 에러(없는 국번)",
            "23": "수신거부 메시지 없음",
            "24": "21시 이후 광고",
            "25": "성인광고, 대출광고 등 기타 제한",
            "26": "데이콤 스팸 필터링",
            "27": "야간 발송차단",
            "28": "사전 미등록 발신번호 사용",
            "29": "전화번호 세칙 미준수 발신번호 사용",
            "30": "발신번호 변작으로 등록된 발신번호 사용",
            "31": "번호 도용 문자 차단 서비스에 가입된 발신번호 사용",
            "40": "단말기착신거부(스팸등)",
            "91": "발송 미허용 시간 때 발송 실패 처리",
            "92": "발신 번호 사전 등록 테이블(PCB)에 등록되지 않은 발신 번호 차단",
            "93": "수신 거부 테이블(SPAM)에 등록된 수신 번호 차단",
            "99": "적용 시간(초) 이내에 수진자번호+메시지내용 이 중복되어 실패"
        }

        # LMS/MMS 전송 결과 코드
        lms_mms_status_messages = {
            "0": "전송 대기 중",
            "WAIT": "전송 대기 중",
            "1000": "전송 성공",
            "2000": "포맷 에러",
            "2001": "잘못된 번호",
            "2002": "컨텐츠 사이즈 및 개수 초과",
            "2003": "잘못된 컨텐츠",
            "3000": "기업형 MMS 미지원 단말기",
            "3001": "단말기 메시지 저장개수 초과",
            "3002": "전송시간 초과",
            "3004": "전원 꺼짐",
            "3005": "음영지역",
            "3006": "기타",
            "4000": "서버문제로 인한 접수 실패",
            "4001": "단말기 일시 서비스 정지",
            "4002": "통신사 내부 실패(무선망단)",
            "4003": "서비스의 일시적인 에러",
            "4101": "계정 차단",
            "4102": "허용되지 않은 IP 접근",
            "4104": "건수 부족",
            "4201": "국제 MMS 발송 권한이 없음",
            "4202": "PUSH 권한 없음",
            "5000": "번호이동에러",
            "5001": "선불발급 발송건수 초과",
            "5003": "스팸",
            "5201": "중복된 키 접수 차단",
            "5202": "중복된 수신번호 접수 차단",
            "5301": "사전 미등록 발신번호 사용",
            "5302": "전화번호 세칙 미 준수 발신번호 사용",
            "5303": "발신번호 변작으로 등록된 발신번호 사용",
            "5304": "번호 도용 문자 차단 서비스에 가입된 발신번호 사용",
            "6000": "폰 정보 조회 실패",
            "6100": "이미지 변환 실패",
            "9001": "발송 미허용 시간 때 발송 실패",
            "9002": "폰 넘버 에러",
            "9003": "스팸 번호",
            "9004": "이통사에서 응답 없음",
            "9005": "파일크기 오류",
            "9006": "지원되지 않는 파일",
            "9007": "파일오류",
            "9008": "MMS_MSG의 MSG_TYPE 값이 잘못되었음",
            "9010": "재전송 횟수 초과로 실패",
            "9011": "발송 지연으로 인한 실패",
            "9012": "발신 번호 사전 등록 테이블(PCB)에 등록되지 않은 발신 번호 차단",
            "9013": "수신 거부 테이블(SPAM)에 등록된 수신 번호 차단",
            "9014": "템플릿 키 값 없음",
            "9015": "바코드 키 값 없음",
            "9016": "CLI_EXT_OBJ 데이터값 오류"
        }

        if msg_type == "SMS":
            return sms_status_messages.get(status_code, f"알 수 없는 상태 코드: {status_code}")
        elif msg_type in ["LMS", "MMS"]:
            return lms_mms_status_messages.get(status_code, f"알 수 없는 상태 코드: {status_code}")
        else:
            return f"알 수 없는 메시지 타입: {msg_type}"

    def get_balance(self) -> Dict[str, Any]:
        """
        잔액 조회
        자동 결제(충전)된 요금에서 메시지 발송 후 남은 금액과
        메시지 발송 실패 시 반환된 금액의 합계

        Returns:
            API 응답 결과
        """
        try:
            # API 요청 데이터 구성
            payload = {
                "version": "1.0"
            }

            # 헤더 구성
            headers = {
                'Content-Type': 'application/json;charset=UTF-8',
                'secret': self._get_secret_header()
            }

            # API 요청
            response = requests.post(
                "https://sms.bizservice.iwinv.kr/api/charge/",
                json=payload,
                headers=headers,
                timeout=30,
                verify=True
            )

            response.raise_for_status()
            result = response.json()

            # 응답 포맷 통일 (iwinv API는 resultCode를 사용하지만, 프론트엔드는 code를 기대)
            if 'resultCode' in result:
                result['code'] = result['resultCode']

            return result

        except requests.exceptions.RequestException as e:
            return {
                "code": -1,
                "message": f"API 요청 실패: {str(e)}",
                "charge": 0.0
            }
        except Exception as e:
            return {
                "code": -1,
                "message": f"조회 중 오류: {str(e)}",
                "charge": 0.0
            }
