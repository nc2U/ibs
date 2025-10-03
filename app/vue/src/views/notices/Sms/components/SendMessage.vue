<script lang="ts" setup>
// Props 정의
interface Props {
  activeTab: string
  currentForm: any
  isDisabled: boolean
  buttonText: string
  isSending: boolean
  sendProgress: number
}

const props = defineProps<Props>()

// Emits 정의
const emit = defineEmits<{
  sendMessage: []
}>()

const handleSendMessage = () => emit('sendMessage')
</script>

<template>
  <CCard>
    <CCardHeader style="height: 48px; padding-top: 12px">
      <v-icon icon="mdi-send" class="me-2" />
      <strong>발송 설정 및 실행</strong>
    </CCardHeader>
    <CCardBody>
      <CRow>
        <!-- 발송 옵션 -->
        <CCol :md="6" :xs="12">
          <div class="mb-3">
            <CFormLabel>발송 시점</CFormLabel>
            <v-radio-group v-model="props.currentForm.scheduledSend" inline>
              <v-radio label="즉시 발송" :value="false" />
              <v-radio label="예약 발송" :value="true" />
            </v-radio-group>
          </div>

          <div v-if="props.currentForm.scheduledSend" class="mb-3">
            <CRow>
              <CCol :md="6">
                <CFormInput
                  v-model="props.currentForm.scheduleDate"
                  type="date"
                  label="발송 날짜"
                />
              </CCol>
              <CCol :md="6">
                <CFormInput
                  v-model="props.currentForm.scheduleTime"
                  type="time"
                  label="발송 시간"
                />
              </CCol>
            </CRow>
          </div>
        </CCol>

        <!-- 발송 실행 -->
        <CCol :md="6" :xs="12">
          <div class="text-right">
            <v-btn
              :color="props.activeTab === 'sms' ? 'primary' : 'success'"
              :loading="props.isSending"
              :disabled="props.isDisabled"
              :prepend-icon="props.activeTab === 'sms' ? 'mdi-send' : 'mdi-chat'"
              size="large"
              class="mb-3"
              @click="handleSendMessage"
            >
              {{ props.buttonText }}
            </v-btn>

            <div v-if="props.isSending" class="mt-3">
              <v-progress-linear
                v-model="props.sendProgress"
                :color="props.activeTab === 'sms' ? 'primary' : 'success'"
                height="8"
                rounded
              />
              <small class="text-muted mt-1"> 발송 중... {{ props.sendProgress }}% </small>
            </div>
          </div>
        </CCol>
      </CRow>
    </CCardBody>
  </CCard>
</template>
