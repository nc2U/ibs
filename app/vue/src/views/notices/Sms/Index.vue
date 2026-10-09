<script lang="ts" setup>
import { computed, onBeforeMount, ref } from 'vue'
import { navMenu, pageTitle } from '@/views/notices/_menu/headermixin'
import { useNotice } from '@/store/pinia/notice.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { useProject } from '@/store/pinia/project.ts'
import { usePerms } from '@/composables/usePerms.ts'
import type { Company } from '@/store/types/settings.ts'
import type { Project } from '@/store/types/project.ts'
import type { KakaoMessage } from '@/store/types/notice.ts'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import NoticeAuthGuard from '@/components/AuthGuard/NoticeAuthGuard.vue'
import BalanceCard from './components/BalanceCard.vue'
import SelectRecipient from './components/SelectRecipient.vue'
import SelectMessage from './components/SelectMessage.vue'
import SendMessage from './components/SendMessage.vue'
import HistoryTab from './components/HistoryTab.vue'

const { can, PERM } = usePerms()
const canNoticeRead = computed(() => can(PERM.NOTICE_READ))

const loading = ref(true)
const mainTab = ref('send') // 'send' or 'history'
const activeTab = ref('sms')

// 공통 데이터
const recipientInput = ref('')
const recipientsList = ref<string[]>([])

const messageCount = ref(0)
const sendProgress = ref(0)
const isSending = ref(false)

// 템플릿 변수 관련 상태
const templateHasVariables = ref(false)
const templateVariableNames = ref<string[]>([])
const recipientsWithVariables = ref<Array<{ phone: string; variables: Record<string, string> }>>([])

// MMS 이미지 첨부
const attachedImages = ref<File[]>([])

// 회사 및 프로젝트 정보
const comStore = useCompany()
const company = computed<Company | null>(() => comStore.company)
const projectStore = useProject()
const project = computed<Project | null>(() => projectStore.project as Project)

// 폼 데이터
const smsForm = ref({
  messageType: 'SMS',
  message: '',
  senderNumber: '',
  companyId: company?.value?.pk ? `company${company.value.pk}` : '', // 회사 PK로 자동 생성, 없으면 빈 문자열
  scheduledSend: false,
  scheduleDate: '',
  scheduleTime: '',
})

const kakaoForm = ref({
  templateId: '',
  message: '',
  senderNumber: '',
  parameters: {} as Record<string, string>,
  scheduledSend: false,
  scheduleDate: '',
  scheduleTime: '',
  reSend: true,
  resendType: 'Y' as 'Y' | 'N',
  resendTitle: '',
  resendContent: '',
})

// Computed 속성들
const currentForm = computed(() => {
  return activeTab.value === 'sms' ? smsForm.value : kakaoForm.value
})

const isDisabled = computed(() => {
  if (activeTab.value === 'sms') {
    const basicValidation =
      recipientsList.value.length === 0 || !smsForm.value.message || !smsForm.value.senderNumber
    // MMS 타입일 때는 이미지 첨부 필수
    if (smsForm.value.messageType === 'MMS') {
      return basicValidation || attachedImages.value.length === 0
    }
    return basicValidation
  } else {
    // 알림톡 유효성 검사: 수신자, 템플릿 코드, 발신번호 필수
    const basicKakao =
      recipientsList.value.length === 0 ||
      !kakaoForm.value.templateId ||
      !kakaoForm.value.senderNumber

    // 실패 시 직접 입력 내용으로 대체 발송 시 대체 본문 필수
    if (
      kakaoForm.value.reSend &&
      kakaoForm.value.resendType === 'N' &&
      !kakaoForm.value.resendContent
    ) {
      return true
    }

    return basicKakao
  }
})

const buttonText = computed(() => {
  let prefix = '알림톡'
  if (activeTab.value === 'sms') {
    prefix = smsForm.value.messageType || 'SMS' // SMS, LMS, MMS 타입 표시
  }
  return currentForm.value.scheduledSend ? '예약 등록' : `${prefix} 전송`
})

const selectTemplate = () => {
  // UI만 구현
}

const previewMessage = () => {
  // UI만 구현
}

const notiStore = useNotice()

// 변수 치환 함수
const replaceVariables = (template: string, variables: Record<string, string>): string => {
  let result = template
  for (const [key, value] of Object.entries(variables)) {
    const regex = new RegExp(`\\{${key}\\}`, 'g')
    result = result.replace(regex, value)
  }
  return result
}

const sendMessage = async () => {
  // 이미 발송 중이면 중복 실행 방지
  if (isSending.value) {
    return
  }

  isSending.value = true
  sendProgress.value = 0

  try {
    if (activeTab.value === 'sms') {
      // MMS 타입이면서 이미지가 첨부된 경우
      if (smsForm.value.messageType === 'MMS' && attachedImages.value.length > 0) {
        const mmsData = {
          message: smsForm.value.message,
          title: '포토 메시지',
          sender_number: smsForm.value.senderNumber,
          recipients: recipientsList.value,
          image: attachedImages.value[0], // 첫 번째 이미지
          company_id: smsForm.value.companyId || undefined,
          scheduled_send: smsForm.value.scheduledSend,
          schedule_date: smsForm.value.scheduledSend ? smsForm.value.scheduleDate : undefined,
          schedule_time: smsForm.value.scheduledSend ? smsForm.value.scheduleTime : undefined,
          use_v2_api: true,
        }

        await notiStore.sendMMS(mmsData as any)
      }
      // 변수 모드: 개별 메시지 생성
      else if (templateHasVariables.value && recipientsWithVariables.value.length > 0) {
        // 각 수신자마다 개별 메시지 생성
        const personalizedRecipients = recipientsWithVariables.value.map(item => ({
          phone: item.phone,
          message: replaceVariables(smsForm.value.message, item.variables),
        }))

        // 개별 메시지 발송 (백엔드에서 지원하는 경우)
        const smsData = {
          message_type: smsForm.value.messageType as 'SMS' | 'LMS' | 'AUTO',
          title: smsForm.value.messageType === 'LMS' ? '안내' : undefined,
          sender_number: smsForm.value.senderNumber,
          personalized_recipients: personalizedRecipients, // 개별 메시지 배열
          company_id: smsForm.value.companyId || undefined,
          scheduled_send: smsForm.value.scheduledSend,
          schedule_date: smsForm.value.scheduledSend ? smsForm.value.scheduleDate : undefined,
          schedule_time: smsForm.value.scheduledSend ? smsForm.value.scheduleTime : undefined,
          use_v2_api: true,
          is_personalized: true, // 개별 메시지 플래그
        }

        await notiStore.sendSMS(smsData as any)
      } else {
        // 일반 모드: 동일 메시지 발송
        const smsData = {
          message_type: smsForm.value.messageType as 'SMS' | 'LMS' | 'AUTO',
          message: smsForm.value.message,
          title: smsForm.value.messageType === 'LMS' ? '안내' : undefined,
          sender_number: smsForm.value.senderNumber,
          recipients: recipientsList.value,
          company_id: smsForm.value.companyId || undefined,
          scheduled_send: smsForm.value.scheduledSend,
          schedule_date: smsForm.value.scheduledSend ? smsForm.value.scheduleDate : undefined,
          schedule_time: smsForm.value.scheduledSend ? smsForm.value.scheduleTime : undefined,
          use_v2_api: true,
        }

        await notiStore.sendSMS(smsData)
      }
    } else {
      // 카카오 알림톡 발송
      // 수신자별 변수 매핑 구성 (iwinv 규격: template_param 배열)
      const paramKeys = Object.keys(kakaoForm.value.parameters || {})
      const kakaoRecipients = recipientsList.value.map(phone => {
        const matchingWithVar = recipientsWithVariables.value.find(item => item.phone === phone)
        let template_param: string[] = []

        if (matchingWithVar && matchingWithVar.variables) {
          template_param = paramKeys.map(
            k => matchingWithVar.variables[k] || kakaoForm.value.parameters[k] || '',
          )
        } else if (paramKeys.length > 0) {
          template_param = paramKeys.map(k => kakaoForm.value.parameters[k] || '')
        }

        return {
          phone,
          ...(template_param.length > 0 ? { template_param } : {}),
        }
      })

      const kakaoPayload: KakaoMessage = {
        template_code: kakaoForm.value.templateId,
        recipients: kakaoRecipients,
        sender_number: kakaoForm.value.senderNumber,
        scheduled_send: kakaoForm.value.scheduledSend,
        schedule_date: kakaoForm.value.scheduledSend ? kakaoForm.value.scheduleDate : undefined,
        schedule_time: kakaoForm.value.scheduledSend ? kakaoForm.value.scheduleTime : undefined,
        re_send: kakaoForm.value.reSend,
        resend_type: kakaoForm.value.reSend ? kakaoForm.value.resendType : undefined,
        resend_title:
          kakaoForm.value.reSend && kakaoForm.value.resendType === 'N'
            ? kakaoForm.value.resendTitle
            : undefined,
        resend_content:
          kakaoForm.value.reSend && kakaoForm.value.resendType === 'N'
            ? kakaoForm.value.resendContent
            : undefined,
        company_id: smsForm.value.companyId || undefined,
        project: project.value?.pk || undefined,
      }

      await notiStore.sendKakao(kakaoPayload)
    }

    // 발송 성공 후 히스토리 새로고침 및 탭 전환
    await notiStore.fetchMessageSendHistory({
      page: 1,
      ordering: '-created',
    })

    mainTab.value = 'history'
  } catch (error) {
    console.error('발송 실패:', error)
  } finally {
    isSending.value = false
    sendProgress.value = 100
  }
}

// 잔액 관련
const balance = computed(() => notiStore.balance)
const balanceLoading = computed(() => notiStore.loading)

const refreshBalance = async () => {
  try {
    await notiStore.fetchBalance()
  } catch (error: any) {
    // Store에서 기본 에러 처리는 하지만, 추가 로깅이 필요한 경우
    console.error('잔액 조회 실패:', error)
  }
}

const projSelect = () => {
  // 프로젝트 전환 시 기존 수신자 및 폼 관련 상태 초기화
  recipientInput.value = ''
  recipientsList.value = []
  recipientsWithVariables.value = []
}

// 초기화 (잔액 자동 조회)
onBeforeMount(async () => {
  loading.value = false
  // 페이지 로드 시 잔액 자동 조회
  await refreshBalance()
})
</script>

<template>
  <NoticeAuthGuard>
    <Loading v-model:active="loading" />

    <ContentHeader
      :page-title="pageTitle"
      :nav-menu="navMenu"
      selector="ProjectSelect"
      @proj-select="projSelect"
    />

    <ContentBody>
      <!-- 메인 탭 (발송 / 히스토리) -->
      <CCol>
        <CCardHeader>
          <CRow class="mt-3">
            <CCol>
              <v-tabs density="compact">
                <v-tab :active="mainTab === 'send'" @click="mainTab = 'send'" variant="tonal">
                  발송
                </v-tab>
                <v-tab
                  :active="mainTab === 'history'"
                  @click="mainTab = 'history'"
                  variant="tonal"
                  :disabled="!canNoticeRead"
                >
                  내역
                </v-tab>
              </v-tabs>
            </CCol>
          </CRow>
        </CCardHeader>
        <CCardBody>
          <!-- 발송 탭 내용 -->
          <CCol v-show="mainTab === 'send'">
            <CRow>
              <CCol sm="6">
                <!-- 메시지 작성 섹션 (탭으로 구분) -->
                <SelectMessage
                  v-model:active-tab="activeTab"
                  v-model:sms-form="smsForm"
                  v-model:kakao-form="kakaoForm"
                  v-model:message-count="messageCount"
                  @select-template="selectTemplate"
                  @preview-message="previewMessage"
                  @update:has-variables="templateHasVariables = $event"
                  @update:variable-names="templateVariableNames = $event"
                  @update:attached-images="attachedImages = $event"
                />
              </CCol>
              <CCol sm="6">
                <!-- 수신자 관리 섹션 (고정) -->
                <SelectRecipient
                  v-model:recipient-input="recipientInput"
                  v-model:recipients-list="recipientsList"
                  :has-template-variables="templateHasVariables"
                  :variable-names="templateVariableNames"
                  @update:recipients-with-variables="recipientsWithVariables = $event"
                />
              </CCol>
            </CRow>

            <CRow>
              <CCol sm="6">
                <!-- 발송 설정 및 실행 -->
                <SendMessage
                  :active-tab="activeTab"
                  :current-form="currentForm"
                  :is-disabled="isDisabled"
                  :button-text="buttonText"
                  :is-sending="isSending"
                  :send-progress="sendProgress"
                  @send-message="sendMessage"
                />
              </CCol>

              <CCol sm="6">
                <!-- 잔액 확인 -->
                <BalanceCard
                  :balance="balance"
                  :loading="balanceLoading"
                  @refresh="refreshBalance"
                />
              </CCol>
            </CRow>
          </CCol>

          <!-- 히스토리 탭 내용 -->
          <CCol v-show="mainTab === 'history'">
            <HistoryTab />
          </CCol>
        </CCardBody>
      </CCol>
    </ContentBody>
  </NoticeAuthGuard>
</template>
