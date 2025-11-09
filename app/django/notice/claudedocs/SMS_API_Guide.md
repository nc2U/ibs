# SMS/MMS/카카오톡 API 사용 가이드

IBS 프로젝트에서 제공하는 문자 메시지 발송 및 관리 REST API 가이드입니다.

## 목차

1. [인증](#인증)
2. [공통 사항](#공통-사항)
3. [SMS/LMS 발송](#smslms-발송)
4. [MMS 발송](#mms-발송)
5. [카카오 알림톡 발송](#카카오-알림톡-발송)
6. [전송 내역 조회](#전송-내역-조회)
7. [잔액 조회](#잔액-조회)
8. [에러 코드 조회](#에러-코드-조회)
9. [에러 처리](#에러-처리)

---

[//]: # (## 인증)

[//]: # ()

[//]: # (모든 API 요청은 JWT 토큰을 사용한 인증이 필요합니다.)

[//]: # ()

[//]: # (### 헤더 설정)

[//]: # ()

[//]: # (```http)

[//]: # (Authorization: Bearer <your_jwt_token>)

[//]: # (Content-Type: application/json)

[//]: # (```)

[//]: # ()

[//]: # (### 토큰 발급)

[//]: # ()

[//]: # (```javascript)

[//]: # (// 로그인 후 토큰 발급)

[//]: # (const response = await fetch&#40;'/api/v1/token/', {)

[//]: # (  method: 'POST',)

[//]: # (  headers: { 'Content-Type': 'application/json' },)

[//]: # (  body: JSON.stringify&#40;{)

[//]: # (    username: 'your_username',)

[//]: # (    password: 'your_password')

[//]: # (  }&#41;)

[//]: # (}&#41;;)

[//]: # ()

[//]: # (const { access, refresh } = await response.json&#40;&#41;;)

[//]: # (// access 토큰을 Authorization 헤더에 사용)

[//]: # (```)

---

## 공통 사항

### Base URL

```
https://your-domain.com/api/v1/messages/
```

### 공통 응답 형식

#### 성공 응답

- **HTTP Status**: `200 OK`
- **Body**: API별 상이 (각 섹션 참조)

#### 실패 응답

- **HTTP Status**: `400 Bad Request` 또는 `500 Internal Server Error`
- **Body**:

```json
{
  "resultCode": -1,
  "message": "오류 메시지",
  ...
}
```

---

## SMS/LMS 발송

단문(SMS) 또는 장문(LMS) 메시지를 발송합니다. 메시지 길이에 따라 자동으로 타입이 결정됩니다.

### 엔드포인트

```
POST /api/v1/messages/send-sms/
```

### 요청 파라미터

| 파라미터           | 타입      | 필수 | 설명                            | 예시                |
|----------------|---------|----|-------------------------------|-------------------|
| message_type   | String  | ❌  | 메시지 타입 (`SMS`, `LMS`, `AUTO`) | `"AUTO"`          |
| message        | String  | ✅  | 메시지 내용 (최대 2000 bytes)        | `"안녕하세요..."`      |
| title          | String  | ❌  | 제목 (LMS용, 최대 40 bytes)        | `"공지사항"`          |
| sender_number  | String  | ✅  | 발신번호                          | `"0212345678"`    |
| recipients     | Array   | ✅  | 수신자 번호 리스트 (최대 1000명)         | `["01012345678"]` |
| scheduled_send | Boolean | ❌  | 예약 발송 여부                      | `false`           |
| schedule_date  | Date    | ❌  | 예약 발송 날짜 (YYYY-MM-DD)         | `"2025-10-15"`    |
| schedule_time  | Time    | ❌  | 예약 발송 시간 (HH:mm)              | `"14:30"`         |
| use_v2_api     | Boolean | ❌  | v2 API 사용 여부                  | `true`            |

### 요청 예시

```javascript
const sendSMS = async () => {
  const response = await fetch('/api/v1/messages/send-sms/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${ accessToken }`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      message_type: 'AUTO',  // SMS/LMS 자동 판별
      message: '안녕하세요. 테스트 메시지입니다.',
      sender_number: '0212345678',
      recipients: ['01012345678', '01087654321'],
      scheduled_send: false
    })
  });

  const result = await response.json();
  return result;
};
```

### 응답 예시

#### 성공

```json
{
  "resultCode": 0,
  "message": "전송 성공",
  "requestNo": "20251002143000123",
  "msgType": "SMS"
}
```

#### 실패

```json
{
  "resultCode": 13,
  "message": "등록되지 않은 발신번호입니다.",
  "requestNo": null,
  "msgType": "SMS"
}
```

### 메시지 타입 자동 판별

- **90 bytes 이하**: SMS 발송
- **90 bytes 초과**: LMS 발송 (제목 자동 생성)

---

## MMS 발송

이미지를 포함한 멀티미디어 메시지를 발송합니다.

### 엔드포인트

```
POST /api/v1/messages/send-mms/
```

### 요청 파라미터

| 파라미터           | 타입      | 필수 | 설명           | 제약 조건         |
|----------------|---------|----|--------------|---------------|
| message        | String  | ✅  | 메시지 내용       | 최대 2000 bytes |
| title          | String  | ✅  | 제목           | 최대 40 bytes   |
| sender_number  | String  | ✅  | 발신번호         | -             |
| recipients     | Array   | ✅  | 수신자 번호 리스트   | 최대 1000명      |
| image          | File    | ✅  | 이미지 파일       | JPG, 100KB 미만 |
| scheduled_send | Boolean | ❌  | 예약 발송 여부     | -             |
| schedule_date  | Date    | ❌  | 예약 발송 날짜     | YYYY-MM-DD    |
| schedule_time  | Time    | ❌  | 예약 발송 시간     | HH:mm         |
| use_v2_api     | Boolean | ❌  | v2 API 사용 여부 | 기본 true       |

### 요청 예시

```javascript
const sendMMS = async (imageFile) => {
  const formData = new FormData();
  formData.append('message', '이미지가 포함된 메시지입니다.');
  formData.append('title', '제목');
  formData.append('sender_number', '0212345678');
  formData.append('recipients', JSON.stringify(['01012345678']));
  formData.append('image', imageFile);  // File object
  formData.append('scheduled_send', false);

  const response = await fetch('/api/v1/messages/send-mms/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${ accessToken }`
      // Content-Type은 브라우저가 자동 설정
    },
    body: formData
  });

  const result = await response.json();
  return result;
};
```

### 응답 예시

```json
{
  "resultCode": 0,
  "message": "전송 성공",
  "requestNo": "20251002143000456",
  "msgType": "MMS"
}
```

### 주의사항

- 이미지는 **JPG 형식만** 지원
- 파일 크기는 **100KB 미만**
- `Content-Type: multipart/form-data` 자동 설정 필요

---

## 카카오 알림톡 발송

승인된 템플릿을 사용하여 카카오 알림톡을 발송합니다.

### 엔드포인트

```
POST /api/v1/messages/send-kakao/
```

### 요청 파라미터

| 파라미터           | 타입      | 필수 | 설명                                 |
|----------------|---------|----|------------------------------------|
| template_code  | String  | ✅  | 승인된 템플릿 코드                         |
| recipients     | Array   | ✅  | 수신자 정보 배열 (최대 10,000명)             |
| sender_number  | String  | ✅  | 발신번호 (사전 등록 필요)                    |
| scheduled_send | Boolean | ❌  | 예약 발송 여부                           |
| schedule_date  | Date    | ❌  | 예약 발송 날짜 (YYYY-MM-DD)              |
| schedule_time  | Time    | ❌  | 예약 발송 시간 (HH:mm)                   |
| re_send        | Boolean | ❌  | 실패 시 대체 문자 발송 여부                   |
| resend_type    | String  | ❌  | 대체 발송 타입 (`Y`: 알림톡 내용, `N`: 직접 입력) |
| resend_title   | String  | ❌  | 대체 문자 제목 (LMS용)                    |
| resend_content | String  | ❌  | 대체 문자 내용                           |

### Recipients 배열 구조

```javascript
[
  {
    phone: "01012345678",           // 필수: 수신자 번호
    template_param: ["홍길동", "100"] // 선택: 템플릿 변수값
  }
]
```

### 요청 예시

```javascript
const sendKakao = async () => {
  const response = await fetch('/api/v1/messages/send-kakao/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${ accessToken }`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      template_code: 'TEMPLATE_001',
      sender_number: '0212345678',
      recipients: [
        {
          phone: '01012345678',
          template_param: ['홍길동', '2025-10-15', '100,000원']
        },
        {
          phone: '01087654321',
          template_param: ['김철수', '2025-10-16', '200,000원']
        }
      ],
      scheduled_send: false,
      re_send: true,        // 실패 시 SMS로 대체 발송
      resend_type: 'Y'      // 알림톡 내용 그대로 SMS 발송
    })
  });

  const result = await response.json();
  return result;
};
```

### 응답 예시

```json
{
  "code": 200,
  "message": "메시지가 발송되었습니다.",
  "success": 2,
  "fail": 0
}
```

### 대체 발송 설정

| resend_type | 설명                 | resend_content 필요 |
|-------------|--------------------|-------------------|
| `Y`         | 알림톡 내용 그대로 SMS 발송  | ❌                 |
| `N`         | 직접 입력한 내용으로 SMS 발송 | ✅                 |

---

## 전송 내역 조회

최근 90일 이내의 메시지 전송 내역을 조회합니다.

### 엔드포인트

```
GET /api/v1/messages/send-history/
```

### 쿼리 파라미터

| 파라미터       | 타입      | 필수 | 설명            | 제약 조건          |
|------------|---------|----|---------------|----------------|
| company_id | String  | ✅  | 조직(업체) 발송 아이디 | -              |
| start_date | String  | ✅  | 조회 시작일        | YYYY-MM-DD     |
| end_date   | String  | ✅  | 조회 마감일        | YYYY-MM-DD     |
| request_no | String  | ❌  | 메시지 발송요청 고유번호 | -              |
| page_num   | Integer | ❌  | 페이지 번호        | 기본 1           |
| page_size  | Integer | ❌  | 조회 건수         | 기본 15, 최대 1000 |
| phone      | String  | ❌  | 수신번호 필터       | -              |

### 요청 예시

```javascript
const getSendHistory = async (startDate, endDate) => {
  const params = new URLSearchParams({
    company_id: 'myCompany',
    start_date: startDate,  // '2025-09-01'
    end_date: endDate,      // '2025-10-02'
    page_num: 1,
    page_size: 20
  });

  const response = await fetch(`/api/v1/messages/send-history/?${ params }`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${ accessToken }`
    }
  });

  const result = await response.json();
  return result;
};
```

### 응답 예시

```json
{
  "resultCode": 0,
  "message": "데이터가 조회되었습니다.",
  "totalCount": 10,
  "list": [
    {
      "requestNo": "241640246571",
      "companyid": "myCompany",
      "msgType": "SMS",
      "phone": "01012345678",
      "callback": "0212345678",
      "sendStatusCode": "06",
      "sendStatusMessage": "전송 성공",
      "sendDate": "2025-10-01 15:22:40"
    },
    {
      "requestNo": "241640246572",
      "companyid": "myCompany",
      "msgType": "LMS",
      "phone": "01087654321",
      "callback": "0212345678",
      "sendStatusCode": "1000",
      "sendStatusMessage": "전송 성공",
      "sendDate": "2025-10-01 16:30:15"
    }
  ]
}
```

### 전송 상태 코드

#### SMS

- `06`: 전송 성공
- `07`: 비가입자, 결번, 서비스정지
- `08`: 단말기 Power-off 상태
- `28`: 사전 미등록 발신번호 사용
- [전체 코드](#sms-상태-코드)

#### LMS/MMS

- `1000`: 전송 성공
- `2001`: 잘못된 번호
- `4104`: 건수 부족
- `5301`: 사전 미등록 발신번호 사용
- [전체 코드](#lmsmms-상태-코드)

### 제약 사항

- 조회 기간: **최대 90일**
- 시작일 ≤ 마감일
- 페이지 크기: **최대 1000건**

---

## 잔액 조회

SMS 발송에 사용 가능한 잔액을 조회합니다.

### 엔드포인트

```
GET /api/v1/messages/balance/
```

### 요청 파라미터

없음 (인증 정보만 필요)

### 요청 예시

```javascript
const getBalance = async () => {
  const response = await fetch('/api/v1/messages/balance/', {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${ accessToken }`
    }
  });

  const result = await response.json();
  return result;
};
```

### 응답 예시

```json
{
  "code": 0,
  "message": "데이터가 조회되었습니다.",
  "charge": 10000.0
}
```

### 잔액 계산

**잔액** = (자동 충전 요금) - (발송 비용) + (실패 반환 금액)

---

## 에러 코드 조회

SMS/LMS/MMS 및 카카오톡 에러 코드 전체 목록을 조회합니다.

### 엔드포인트

```
GET /api/v1/messages/error-codes/
```

### 요청 파라미터

없음

### 요청 예시

```javascript
const getErrorCodes = async () => {
  const response = await fetch('/api/v1/messages/error-codes/', {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${ accessToken }`
    }
  });

  const result = await response.json();
  return result;
};
```

### 응답 예시

```json
{
  "sms_error_codes": {
    "0": "전송 성공",
    "1": "메시지가 전송되지 않았습니다.",
    "13": "등록되지 않은 발신번호입니다.",
    "14": "인증 요청이 올바르지 않습니다.",
    ...
  },
  "kakao_error_codes": {
    "200": "메시지가 발송되었습니다.",
    "501": "{templateCode}값을 정확히 입력해 주세요.",
    "505": "발신번호는 발신번호 관리에서 사전에 등록된 발신번호로만 발송이 가능합니다.",
    ...
  }
}
```

---

## 에러 처리

### HTTP 상태 코드

| 코드  | 의미     | 처리 방법         |
|-----|--------|---------------|
| 200 | 성공     | 응답 데이터 사용     |
| 400 | 잘못된 요청 | 요청 파라미터 확인    |
| 401 | 인증 실패  | 토큰 재발급 필요     |
| 500 | 서버 오류  | 재시도 또는 관리자 문의 |

### 공통 에러 응답 구조

#### SMS/LMS/MMS

```json
{
  "resultCode": -1,
  "message": "오류 메시지",
  "requestNo": null,
  "msgType": "SMS"
}
```

#### 카카오 알림톡

```json
{
  "code": -1,
  "message": "오류 메시지",
  "success": 0,
  "fail": 10
}
```

### 에러 처리 예시

```javascript
const handleSendSMS = async (data) => {
  try {
    const response = await fetch('/api/v1/messages/send-sms/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${ accessToken }`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });

    const result = await response.json();

    if (response.ok && result.resultCode === 0) {
      // 성공
      console.log('발송 성공:', result.requestNo);
      return { success: true, data: result };
    } else {
      // 실패
      console.error('발송 실패:', result.message);
      return { success: false, error: result.message };
    }
  } catch (error) {
    // 네트워크 오류
    console.error('네트워크 오류:', error);
    return { success: false, error: '네트워크 오류가 발생했습니다.' };
  }
};
```

---

## 주요 에러 코드 참조

### SMS 상태 코드

| 코드 | 메시지              | 설명          |
|----|------------------|-------------|
| 06 | 전송 성공            | ✅ 정상 발송     |
| 07 | 비가입자, 결번, 서비스정지  | 수신번호 확인 필요  |
| 08 | 단말기 Power-off 상태 | 재발송 권장      |
| 28 | 사전 미등록 발신번호 사용   | 발신번호 등록 필요  |
| 40 | 단말기착신거부(스팸등)     | 수신자가 차단한 상태 |
| 92 | 발신 번호 사전 등록되지 않음 | 발신번호 등록 필요  |
| 93 | 수신 거부 테이블에 등록됨   | 스팸 등록된 번호   |

### LMS/MMS 상태 코드

| 코드   | 메시지              | 설명           |
|------|------------------|--------------|
| 1000 | 전송 성공            | ✅ 정상 발송      |
| 2001 | 잘못된 번호           | 수신번호 형식 오류   |
| 3001 | 단말기 메시지 저장개수 초과  | 수신자 메시지함 가득참 |
| 4104 | 건수 부족            | 잔액 부족        |
| 5301 | 사전 미등록 발신번호 사용   | 발신번호 등록 필요   |
| 9012 | 발신 번호 사전 등록되지 않음 | 발신번호 등록 필요   |
| 9013 | 수신 거부 테이블에 등록됨   | 스팸 등록된 번호    |

### 카카오 알림톡 에러 코드

| 코드  | 메시지               | 설명           |
|-----|-------------------|--------------|
| 200 | 메시지가 발송되었습니다      | ✅ 정상 발송      |
| 501 | templateCode 값 오류 | 템플릿 코드 확인 필요 |
| 505 | 사전 등록되지 않은 발신번호   | 발신번호 등록 필요   |
| 509 | 메시지 내용이 템플릿과 불일치  | 템플릿 변수 확인    |
| 514 | 최대 10,000건 초과     | 발송 건수 제한     |
| 519 | 잔액 부족             | 충전 필요        |

---

## Vue.js 통합 예시

### Composition API

```vue

<script setup>
  import { ref } from 'vue';

  const accessToken = ref(localStorage.getItem('access_token'));
  const loading = ref(false);
  const error = ref(null);

  // SMS 발송
  const sendSMS = async (message, recipients, senderNumber) => {
    loading.value = true;
    error.value = null;

    try {
      const response = await fetch('/api/v1/messages/send-sms/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${ accessToken.value }`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message_type: 'AUTO',
          message,
          sender_number: senderNumber,
          recipients,
          scheduled_send: false
        })
      });

      const result = await response.json();

      if (response.ok && result.resultCode === 0) {
        return { success: true, requestNo: result.requestNo };
      } else {
        throw new Error(result.message);
      }
    } catch (err) {
      error.value = err.message;
      return { success: false, error: err.message };
    } finally {
      loading.value = false;
    }
  };

  // 잔액 조회
  const getBalance = async () => {
    try {
      const response = await fetch('/api/v1/messages/balance/', {
        headers: {
          'Authorization': `Bearer ${ accessToken.value }`
        }
      });

      const result = await response.json();
      return result.charge;
    } catch (err) {
      console.error('잔액 조회 실패:', err);
      return 0;
    }
  };

  // 전송 내역 조회
  const getHistory = async (startDate, endDate, pageNum = 1) => {
    const params = new URLSearchParams({
      company_id: 'myCompany',
      start_date: startDate,
      end_date: endDate,
      page_num: pageNum,
      page_size: 20
    });

    const response = await fetch(`/api/v1/messages/send-history/?${ params }`, {
      headers: {
        'Authorization': `Bearer ${ accessToken.value }`
      }
    });

    return await response.json();
  };
</script>

<template>
  <div>
    <button @click="sendSMS('테스트 메시지', ['01012345678'], '0212345678')">
      SMS 발송
    </button>
    <p v-if="loading">발송 중...</p>
    <p v-if="error" class="error">{{ error }}</p>
  </div>
</template>
```

---

## React 통합 예시

### Custom Hook

```javascript
// useSMS.js
import { useState } from 'react';

export const useSMS = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const sendSMS = async (message, recipients, senderNumber) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/messages/send-sms/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${ localStorage.getItem('access_token') }`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message_type: 'AUTO',
          message,
          sender_number: senderNumber,
          recipients,
          scheduled_send: false
        })
      });

      const result = await response.json();

      if (response.ok && result.resultCode === 0) {
        return { success: true, requestNo: result.requestNo };
      } else {
        throw new Error(result.message);
      }
    } catch (err) {
      setError(err.message);
      return { success: false, error: err.message };
    } finally {
      setLoading(false);
    }
  };

  const getBalance = async () => {
    const response = await fetch('/api/v1/messages/balance/', {
      headers: {
        'Authorization': `Bearer ${ localStorage.getItem('access_token') }`
      }
    });

    const result = await response.json();
    return result.charge;
  };

  return { sendSMS, getBalance, loading, error };
};
```

---

## 추가 참고사항

### 발신번호 등록

대부분의 에러는 **발신번호 미등록**으로 발생합니다. 사전에 발신번호를 등록해야 합니다.

### 요금 안내

- **SMS**: 약 20원/건
- **LMS**: 약 50원/건
- **MMS**: 약 200원/건
- **카카오 알림톡**: 약 8원/건 (실패 시 SMS 대체 발송 비용 추가)

### 발송 제한

- SMS/LMS/MMS: 1회 최대 **1,000건**
- 카카오 알림톡: 1회 최대 **10,000건**

### 예약 발송 제한

- SMS/LMS/MMS: 현재 시간 **15분 이후 ~ 1개월 이내**
- 카카오 알림톡: 현재 시간 **15분 이후 ~ 2일 이내**

---

## 문의

API 사용 중 문제가 발생하면 개발팀에 문의하세요.

- 프로젝트 이슈: [GitHub Issues](https://github.com/nc2u/ibs/issues)
- 이메일: kori.susie@gmail.com
