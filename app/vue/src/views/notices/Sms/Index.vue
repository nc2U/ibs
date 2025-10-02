<script lang="ts" setup>
import { onBeforeMount, ref, computed } from 'vue'
import { pageTitle, navMenu } from '@/views/notices/_menu/headermixin'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import SelectRecipient from './components/SelectRecipient.vue'
import SelectMessage from './components/SelectMessage.vue'
import SendMessage from './components/SendMessage.vue'

const loading = ref(true)
const activeTab = ref('sms')

// 공통 데이터
const recipientInput = ref('')
const recipientsList = ref([])
const messageCount = ref(0)
const sendProgress = ref(0)
const isSending = ref(false)

// 폼 데이터
const smsForm = ref({
  messageType: 'SMS',
  message: '',
  senderNumber: '',
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

onBeforeMount(() => {
  loading.value = false
})

// 메소드 (비즈니스 로직은 제외하고 UI만)
const addRecipient = () => {
  // UI만 구현
}

const removeRecipient = (index: number) => {
  // UI만 구현
}

const selectTemplate = () => {
  // UI만 구현
}

const previewMessage = () => {
  // UI만 구현
}

const sendMessage = () => {
  // UI만 구현
  isSending.value = true
  sendProgress.value = 0
}
</script>

<template>
  <Loading v-model:active="loading" />

  <ContentHeader :page-title="pageTitle" :nav-menu="navMenu" selector="ProjectSelect" />

  <ContentBody>
    <CCardBody>
      <CRow>
        <!-- 수신자 관리 섹션 (고정) -->
        <SelectRecipient
          v-model:recipient-input="recipientInput"
          v-model:recipients-list="recipientsList"
          @add-recipient="addRecipient"
          @remove-recipient="removeRecipient"
        />

        <!-- 메시지 작성 섹션 (탭으로 구분) -->
        <SelectMessage
          v-model:active-tab="activeTab"
          v-model:sms-form="smsForm"
          v-model:kakao-form="kakaoForm"
          v-model:message-count="messageCount"
          @select-template="selectTemplate"
          @preview-message="previewMessage"
        />
      </CRow>

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
    </CCardBody>
  </ContentBody>
</template>
