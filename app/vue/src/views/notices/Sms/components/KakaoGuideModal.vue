<script lang="ts" setup>
import { ref } from 'vue'

const visible = ref(false)

const openModal = () => {
  visible.value = true
}

const closeModal = () => {
  visible.value = false
}

defineExpose({
  openModal,
  closeModal,
})
</script>

<template>
  <CModal :visible="visible" @close="closeModal" size="lg" backdrop="static" alignment="center">
    <CModalHeader class="bg-warning-subtle py-3">
      <CModalTitle class="d-flex align-items-center">
        <v-icon icon="mdi-chat" color="amber-darken-3" class="me-2" />
        <strong>카카오 알림톡 서비스 준비 및 연동 가이드</strong>
      </CModalTitle>
    </CModalHeader>

    <CModalBody class="p-4">
      <div class="mb-3">
        <p class="text-body-2 text-medium-emphasis">
          카카오 알림톡은 스팸 방지 및 카카오 정책에 따라
          <strong>카카오톡 비즈니스 채널 인증</strong> 및 <strong>iwinv 발신 프로필 등록</strong>,
          <strong>템플릿 사전 검수 승인</strong>을 완료한 후 발송할 수 있습니다. 아래 4단계를
          순서대로 진행해 주세요.
        </p>
      </div>

      <v-timeline side="end" density="compact" class="mb-4">
        <!-- 1단계 -->
        <v-timeline-item dot-color="warning" size="small">
          <div class="d-flex justify-content-between align-items-center mb-1">
            <strong class="text-subtitle-1">1단계: 카카오톡 채널 개설 및 비즈니스 채널 인증</strong>
            <v-btn
              size="x-small"
              variant="outlined"
              color="primary"
              href="https://business.kakao.com"
              target="_blank"
              prepend-icon="mdi-open-in-new"
            >
              카카오 비즈니스
            </v-btn>
          </div>
          <p class="text-caption text-medium-emphasis mb-1">
            카카오톡 채널 관리자센터(business.kakao.com)에서 회사/브랜드 채널을 생성한 후,
            <strong>[관리 > 비즈니스 채널 신청]</strong> 메뉴에서 사업자등록증 및 재직증명서를
            제출하여 <strong>인증 마크(골드 배지)</strong>를 획득해야 합니다.
          </p>
          <small class="text-warning-emphasis"
            >※ 일반(개인) 채널은 알림톡 발송이 불가하며 비즈니스 인증이 필수입니다.</small
          >
        </v-timeline-item>

        <!-- 2단계 -->
        <v-timeline-item dot-color="info" size="small">
          <div class="d-flex justify-content-between align-items-center mb-1">
            <strong class="text-subtitle-1">2단계: iwinv 콘솔에서 알림톡 발신 프로필 등록</strong>
            <v-btn
              size="x-small"
              variant="outlined"
              color="info"
              href="https://console.iwinv.kr/msg/allimtalk/profile"
              target="_blank"
              prepend-icon="mdi-open-in-new"
            >
              iwinv 발신 프로필
            </v-btn>
          </div>
          <p class="text-caption text-medium-emphasis mb-1">
            iwinv 관리콘솔 로그인 후 <strong>[메시지 > 알림톡 > 발신 프로필 관리]</strong>에서
            1단계에서 승인된 카카오 채널 검색용 아이디(@채널명)를 입력하고, 채널 관리자 휴대전화로
            전송된 인증번호를 입력하여 프로필을 등록합니다.
          </p>
        </v-timeline-item>

        <!-- 3단계 -->
        <v-timeline-item dot-color="primary" size="small">
          <div class="d-flex justify-content-between align-items-center mb-1">
            <strong class="text-subtitle-1">3단계: 알림톡 템플릿 등록 및 카카오 검수 승인</strong>
            <v-btn
              size="x-small"
              variant="outlined"
              color="primary"
              href="https://console.iwinv.kr/msg/allimtalk/template"
              target="_blank"
              prepend-icon="mdi-open-in-new"
            >
              iwinv 템플릿 관리
            </v-btn>
          </div>
          <p class="text-caption text-medium-emphasis mb-1">
            알림톡은 계약 안내, 수납 고지 등 <strong>정보성 메시지만 발송 가능</strong>합니다(광고
            불가). iwinv 콘솔에서 메시지 본문과 가변 변수(예: <code>#{이름}</code>,
            <code>#{금액}</code>), 버튼 링크를 작성하여 카카오에 검수를 요청합니다. (승인 소요:
            영업일 기준 1~3일)
          </p>
          <small class="text-primary-emphasis">
            ※ 검수가 승인되면 고유한 <strong>템플릿 코드(templateCode)</strong>가 발급됩니다.
          </small>
        </v-timeline-item>

        <!-- 4단계 -->
        <v-timeline-item dot-color="success" size="small">
          <strong class="text-subtitle-1">4단계: IBS 시스템에 승인 템플릿 등록 및 발송</strong>
          <p class="text-caption text-medium-emphasis mb-1">
            발급받은 <strong>템플릿 코드</strong>와 <strong>승인된 본문 내용</strong>을 본 시스템의
            <strong>[메시지 템플릿 관리 > 카카오 알림톡]</strong>에 등록합니다. 이제 발송 화면에서
            승인된 템플릿을 선택하여 수신자별 변수를 입력하고 간편하게 발송할 수 있습니다!
          </p>
        </v-timeline-item>
      </v-timeline>

      <!-- 팁/대체 발송 안내 카드 -->
      <v-alert type="info" variant="tonal" density="compact" class="mb-0">
        <div class="d-flex align-items-center mb-1">
          <v-icon icon="mdi-shield-check" class="me-1" size="small" />
          <strong>실패 시 대체 발송(Failover) 안내</strong>
        </div>
        <small class="d-block">
          카카오톡을 사용하지 않거나 채널을 차단한 수신자에게는 알림톡 발송이 실패합니다. 발송
          옵션에서 <strong>[실패 시 대체 문자 발송]</strong>을 켜두시면 자동으로 일반 SMS/LMS로
          전환되어 안전하게 전달됩니다. (※ iwinv에 사전 등록된 발신번호 필요)
        </small>
      </v-alert>
    </CModalBody>

    <CModalFooter>
      <v-btn color="secondary" variant="outlined" @click="closeModal">닫기</v-btn>
    </CModalFooter>
  </CModal>
</template>
