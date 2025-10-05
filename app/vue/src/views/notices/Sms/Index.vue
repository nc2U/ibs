<script lang="ts" setup>
import { onBeforeMount, ref, computed, inject, type ComputedRef } from 'vue'
import { pageTitle, navMenu } from '@/views/notices/_menu/headermixin'
import { useNotice } from '@/store/pinia/notice.ts'
import type { Company } from '@/store/types/settings.ts'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import BalanceCard from './components/BalanceCard.vue'
import SelectRecipient from './components/SelectRecipient.vue'
import SelectMessage from './components/SelectMessage.vue'
import SendMessage from './components/SendMessage.vue'
import HistoryTab from './components/HistoryTab.vue'

const loading = ref(true)
const mainTab = ref('send') // 'send' or 'history'
const activeTab = ref('sms')

// 공통 데이터
const recipientInput = ref('')
const recipientsList = ref<string[]>([])

const messageCount = ref(0)
const sendProgress = ref(0)
const isSending = ref(false)

// 회사 정보
const company = inject<ComputedRef<Company | null>>('company')

// 폼 데이터
const smsForm = ref({
  messageType: 'SMS',
  message: '',
  senderNumber: '',
  companyId: company?.value?.pk ? `company${company.value.pk}` : 'default', // 회사 PK로 자동 생성
  scheduledSend: false,
  scheduleDate: '',
  scheduleTime: '',
})

const kakaoForm = ref({
  templateId: '',
  message: '',
  parameters: {},
  scheduledSend: false,
  scheduleDate: '',
  scheduleTime: '',
})

// Computed 속성들
const currentForm = computed(() => {
  return activeTab.value === 'sms' ? smsForm.value : kakaoForm.value
})

const isDisabled = computed(() => {
  if (activeTab.value === 'sms') {
    return recipientsList.value.length === 0 || !smsForm.value.message
  } else {
    return recipientsList.value.length === 0 || !kakaoForm.value.templateId
  }
})

const buttonText = computed(() => {
  const prefix = activeTab.value === 'sms' ? 'SMS' : '알림톡'
  return currentForm.value.scheduledSend ? '예약 등록' : `${prefix} 전송`
})

const selectTemplate = () => {
  // UI만 구현
}

const previewMessage = () => {
  // UI만 구현
}

const notiStore = useNotice()

const sendMessage = async () => {
  // 이미 발송 중이면 중복 실행 방지
  if (isSending.value) {
    console.warn('이미 발송 중입니다.')
    return
  }

  isSending.value = true
  sendProgress.value = 0

  try {
    if (activeTab.value === 'sms') {
      // SMS/LMS 발송
      await notiStore.sendSMS({
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
      })
    } else {
      // 카카오 알림톡 발송
      await notiStore.sendKakao({
        template_code: kakaoForm.value.templateId,
        recipients: recipientsList.value.map(phone => ({ phone })),
        sender_number: '02-1234-5678', // TODO: 실제 발신번호로 변경
        scheduled_send: kakaoForm.value.scheduledSend,
        schedule_date: kakaoForm.value.scheduledSend ? kakaoForm.value.scheduleDate : undefined,
        schedule_time: kakaoForm.value.scheduledSend ? kakaoForm.value.scheduleTime : undefined,
      })
    }
  } catch (error) {
    console.error('발송 실패:', error)
  } finally {
    isSending.value = false
    sendProgress.value = 100
  }
}

// 잔액 관련
const balance = ref(0)
const balanceLoading = ref(false)

const refreshBalance = () => {
  balanceLoading.value = true
  // TODO: 실제 API 호출
  // await noticeStore.fetchBalance()
  setTimeout(() => {
    balance.value = 12500 // 더미 데이터
    balanceLoading.value = false
  }, 500)
}

// 초기화 (잔액은 사용자가 아코디언 열 때 로드)
onBeforeMount(() => {
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />

  <ContentHeader :page-title="pageTitle" :nav-menu="navMenu" selector="ProjectSelect" />

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
              <v-tab :active="mainTab === 'history'" @click="mainTab = 'history'" variant="tonal">
                히스토리
              </v-tab>
            </v-tabs>
          </CCol>
        </CRow>
      </CCardHeader>
      <CCardBody>
        <!-- 발송 탭 내용 -->
        <div v-show="mainTab === 'send'">
          <CRow>
            <CCol>
              <!-- 메시지 작성 섹션 (탭으로 구분) -->
              <SelectMessage
                v-model:active-tab="activeTab"
                v-model:sms-form="smsForm"
                v-model:kakao-form="kakaoForm"
                v-model:message-count="messageCount"
                @select-template="selectTemplate"
                @preview-message="previewMessage"
              />
            </CCol>
            <CCol>
              <!-- 수신자 관리 섹션 (고정) -->
              <SelectRecipient
                v-model:recipient-input="recipientInput"
                v-model:recipients-list="recipientsList"
              />
            </CCol>
          </CRow>

          <CRow>
            <CCol>
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

            <CCol>
              <!-- 잔액 아코디언 -->
              <BalanceCard :balance="balance" :loading="balanceLoading" @refresh="refreshBalance" />
            </CCol>
          </CRow>
        </div>

        <!-- 히스토리 탭 내용 -->
        <div v-show="mainTab === 'history'">
          <HistoryTab />
        </div>
      </CCardBody>
    </CCol>
  </ContentBody>
</template>
