from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response

from notice.utils import IwinvSMSService
from ..permission import *
from ..serializers.notice import *


class BillIssueViewSet(viewsets.ModelViewSet):
    queryset = SalesBillIssue.objects.all()
    serializer_class = SallesBillIssueSerializer
    filterset_fields = ('project',)
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class MessageViewSet(viewsets.ViewSet):
    """SMS/MMS/카카오톡 메시지 발송 ViewSet"""
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    @action(detail=False, methods=['post'], url_path='send-sms')
    def send_sms(self, request):
        """SMS/LMS 메시지 발송"""
        serializer = SMSMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            # iwinv SMS 서비스 초기화
            sms_service = IwinvSMSService()

            # 발송 데이터 준비
            validated_data = serializer.validated_data
            message_type = validated_data.get('message_type', 'AUTO')

            # 예약 발송 시간 처리
            schedule_date = validated_data.get('schedule_date')
            schedule_time = validated_data.get('schedule_time')

            schedule_date_str = schedule_date.strftime('%Y-%m-%d') if schedule_date else None
            schedule_time_str = schedule_time.strftime('%H:%M') if schedule_time else None

            # 메시지 타입에 따른 발송
            if message_type == 'SMS':
                result = sms_service.send_sms(
                    recipients=validated_data['recipients'],
                    message=validated_data['message'],
                    sender_number=validated_data['sender_number'],
                    schedule_date=schedule_date_str,
                    schedule_time=schedule_time_str,
                    use_v2_api=validated_data.get('use_v2_api', True)
                )
            elif message_type == 'LMS':
                result = sms_service.send_lms(
                    recipients=validated_data['recipients'],
                    message=validated_data['message'],
                    title=validated_data.get('title', ''),
                    sender_number=validated_data['sender_number'],
                    schedule_date=schedule_date_str,
                    schedule_time=schedule_time_str,
                    use_v2_api=validated_data.get('use_v2_api', True)
                )
            else:  # AUTO
                result = sms_service.send_auto_message(
                    recipients=validated_data['recipients'],
                    message=validated_data['message'],
                    sender_number=validated_data['sender_number'],
                    title=validated_data.get('title'),
                    schedule_date=schedule_date_str,
                    schedule_time=schedule_time_str
                )

            # 결과에 따른 응답 상태 코드 결정
            result_code = result.get('resultCode')

            if result_code == 0:
                response_status = status.HTTP_200_OK
            else:
                response_status = status.HTTP_400_BAD_REQUEST

            # 에러 메시지 추가
            if 'message' not in result:
                result['message'] = IwinvSMSService.get_error_message(result.get('resultCode', -1))

            return Response(result, status=response_status)

        except ValueError as e:
            return Response({
                'resultCode': -1,
                'message': str(e),
                'requestNo': None,
                'msgType': message_type
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'resultCode': -1,
                'message': '서버 내부 오류가 발생했습니다.',
                'requestNo': None,
                'msgType': message_type
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='send-mms')
    def send_mms(self, request):
        """MMS 메시지 발송"""
        serializer = MMSMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            # iwinv SMS 서비스 초기화
            sms_service = IwinvSMSService()

            # 발송 데이터 준비
            validated_data = serializer.validated_data

            # 예약 발송 시간 처리
            schedule_date = validated_data.get('schedule_date')
            schedule_time = validated_data.get('schedule_time')

            schedule_date_str = schedule_date.strftime('%Y-%m-%d') if schedule_date else None
            schedule_time_str = schedule_time.strftime('%H:%M') if schedule_time else None

            # MMS 발송
            result = sms_service.send_mms(
                recipients=validated_data['recipients'],
                message=validated_data['message'],
                title=validated_data.get('title', ''),
                sender_number=validated_data['sender_number'],
                image_file=validated_data['image'],
                schedule_date=schedule_date_str,
                schedule_time=schedule_time_str,
                use_v2_api=validated_data.get('use_v2_api', True)
            )

            # 결과에 따른 응답 상태 코드 결정
            if result.get('resultCode') == 0:
                response_status = status.HTTP_200_OK
            else:
                response_status = status.HTTP_400_BAD_REQUEST

            # 에러 메시지 추가
            if 'message' not in result:
                result['message'] = IwinvSMSService.get_error_message(result.get('resultCode', -1))

            return Response(result, status=response_status)

        except ValueError as e:
            # Optionally log the original error internally
            # import logging is at the top if used; otherwise add as needed
            # logging.error(f"ValueError in send_mms: {str(e)}")
            return Response({
                'resultCode': -1,
                'message': '서버 내부 오류가 발생했습니다.',  # Generic message: "Input value error occurred."
                'requestNo': None,
                'msgType': 'MMS'
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            # Optionally log the original error internally
            # logging.error(f"Unhandled exception in send_mms: {str(e)}")
            return Response({
                'resultCode': -1,
                'message': '서버 내부 오류가 발생했습니다.',  # Generic message: "Internal server error occurred."
                'requestNo': None,
                'msgType': 'MMS'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='send-kakao')
    def send_kakao(self, request):
        """카카오 알림톡 발송"""
        serializer = KakaoMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            # iwinv SMS 서비스 초기화
            sms_service = IwinvSMSService()

            # 발송 데이터 준비
            validated_data = serializer.validated_data

            # 예약 발송 시간 처리
            schedule_date = validated_data.get('schedule_date')
            schedule_time = validated_data.get('schedule_time')

            schedule_date_str = schedule_date.strftime('%Y-%m-%d') if schedule_date else None
            schedule_time_str = schedule_time.strftime('%H:%M') if schedule_time else None

            # 카카오 알림톡 발송
            result = sms_service.send_kakao_alimtalk(
                recipients=validated_data['recipients'],
                template_code=validated_data['template_code'],
                sender_number=validated_data['sender_number'],
                reserve=validated_data.get('scheduled_send', False),
                send_date=schedule_date_str,
                send_time=schedule_time_str,
                re_send=validated_data.get('re_send', False),
                resend_type=validated_data.get('resend_type', 'Y'),
                resend_title=validated_data.get('resend_title'),
                resend_content=validated_data.get('resend_content')
            )

            # 결과에 따른 응답 상태 코드 결정
            if result.get('code') == 200:
                response_status = status.HTTP_200_OK
            else:
                response_status = status.HTTP_400_BAD_REQUEST

            # 에러 메시지 추가
            if 'message' not in result:
                result['message'] = IwinvSMSService.get_kakao_error_message(result.get('code', -1))

            return Response(result, status=response_status)

        except ValueError as e:
            # Handle case where validated_data might not be defined
            fail_count = 0
            try:
                fail_count = len(validated_data.get('recipients', []))
            except NameError:
                fail_count = 0

            return Response({
                'code': -1,
                'message': str(e),
                'success': 0,
                'fail': fail_count
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            # Handle case where validated_data might not be defined
            fail_count = 0
            try:
                fail_count = len(validated_data.get('recipients', []))
            except NameError:
                fail_count = 0

            return Response({
                'code': -1,
                'message': '서버 내부 오류가 발생했습니다.',
                'success': 0,
                'fail': fail_count
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='error-codes')
    def get_error_codes(self, request):
        """에러 코드 목록 조회"""
        sms_error_codes = {}
        for code in range(0, 51):
            sms_error_codes[code] = IwinvSMSService.get_error_message(code)

        kakao_error_codes = {}
        kakao_codes = [200, 501, 502, 503, 504, 505, 506, 507, 508, 509, 510, 511, 512, 513, 514, 515, 516, 517, 518,
                       519, 540]
        for code in kakao_codes:
            kakao_error_codes[code] = IwinvSMSService.get_kakao_error_message(code)

        return Response({
            'sms_error_codes': sms_error_codes,
            'kakao_error_codes': kakao_error_codes
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='send-history')
    def get_send_history(self, request):
        """전송 내역 조회"""
        from ..serializers.notice import SMSHistoryQuerySerializer

        serializer = SMSHistoryQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            # iwinv SMS 서비스 초기화
            sms_service = IwinvSMSService()

            # 조회 데이터 준비
            validated_data = serializer.validated_data

            # 날짜를 문자열로 변환
            start_date = validated_data['start_date'].strftime('%Y-%m-%d')
            end_date = validated_data['end_date'].strftime('%Y-%m-%d')

            page_num = validated_data.get('page_num', 1)
            page_size = validated_data.get('page_size', 15)

            # 전송 내역 조회
            result = sms_service.get_send_history(
                company_id=validated_data['company_id'],
                start_date=start_date,
                end_date=end_date,
                request_no=validated_data.get('request_no'),
                page_num=page_num,
                page_size=page_size,
                phone=validated_data.get('phone')
            )

            # 결과에 따른 응답 상태 코드 결정
            if result.get('resultCode') == 0:
                response_status = status.HTTP_200_OK

                # 각 항목에 상태 메시지 추가
                for item in result.get('list', []):
                    if 'sendStatusCode' in item and 'msgType' in item:
                        item['sendStatusMessage'] = IwinvSMSService.get_send_status_message(
                            item['msgType'],
                            item['sendStatusCode']
                        )
            else:
                response_status = status.HTTP_400_BAD_REQUEST

            return Response(result, status=response_status)

        except ValueError as e:
            return Response({
                'resultCode': -1,
                'message': '요청 값이 유효하지 않습니다.',  # "The request values are invalid."
                'totalCount': 0,
                'list': []
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'resultCode': -1,
                'message': '서버 내부 오류가 발생했습니다.',
                'totalCount': 0,
                'list': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='balance')
    def get_balance(self, request):
        """잔액 조회"""
        try:
            # iwinv SMS 서비스 초기화
            sms_service = IwinvSMSService()

            # 잔액 조회
            result = sms_service.get_balance()

            # 결과에 따른 응답 상태 코드 결정
            if result.get('code') == 0:
                response_status = status.HTTP_200_OK
            else:
                response_status = status.HTTP_400_BAD_REQUEST

            return Response(result, status=response_status)

        except Exception as e:
            return Response({
                'code': -1,
                'message': '서버 내부 오류가 발생했습니다.',
                'charge': 0.0
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='registered-sender-numbers')
    def get_registered_sender_numbers(self, request):
        """등록된 발신번호 목록 조회"""
        try:
            registered_numbers = getattr(settings, 'IWINV_REGISTERED_SENDER_NUMBERS', [])

            return Response({
                'numbers': registered_numbers,
                'count': len(registered_numbers)
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'numbers': [],
                'count': 0,
                'message': '발신번호 목록 조회 중 오류가 발생했습니다.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
