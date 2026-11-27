<script lang="ts" setup>
import { computed } from 'vue'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import TimePicker from '@/components/DatePicker/TimePicker.vue'

export interface SendFormScheduleState {
  scheduledSend: boolean
  scheduleDate: string
  scheduleTime: string
}

// Props 정의
interface Props {
  activeTab: string
  currentForm: SendFormScheduleState
  isDisabled: boolean
  buttonText: string
  isSending: boolean
  sendProgress: number
}

const props = defineProps<Props>()

// Emits 정의
const emit = defineEmits<{
  (e: 'sendMessage'): void
  (e: 'update:scheduledSend', value: boolean): void
  (e: 'update:scheduleDate', value: string): void
  (e: 'update:scheduleTime', value: string): void
}>()

const scheduledSendModel = computed({
  get: () => props.currentForm.scheduledSend,
  set: (val: boolean) => emit('update:scheduledSend', val),
})

const scheduleDateModel = computed({
  get: () => props.currentForm.scheduleDate,
  set: (val: string) => emit('update:scheduleDate', val),
})

const scheduleTimeModel = computed({
  get: () => props.currentForm.scheduleTime,
  set: (val: string) => emit('update:scheduleTime', val),
})

const handleSendMessage = () => emit('sendMessage')
</script>

<template>
  <CCard class="mb-4">
    <CCardHeader style="">
      <v-icon icon="mdi-send" class="me-2" />
      <strong>발송 설정 및 실행</strong>
    </CCardHeader>
    <CCardBody>
      <CRow>
        <!-- 발송 옵션 -->
        <CCol :xl="6" :lg="12">
          <div>
            <v-radio-group v-model="scheduledSendModel" inline>
              <template v-slot:label>
                <div class="strong mb-2">발송 시점</div>
              </template>
              <v-radio label="즉시 발송" :value="false" />
              <v-radio label="예약 발송" :value="true" />
              <span>
                <v-icon icon="mdi-information-box-outline" class="m-2 pt-1" color="grey" />
                <v-tooltip activator="parent" location="top">
                  전송되길 원하는 시간을 선택해 주세요.<br />
                  예약 발송은 현재 시간 15분 이후 한달 이전까지만 가능합니다.
                </v-tooltip>
              </span>
            </v-radio-group>
          </div>

          <div v-if="scheduledSendModel" class="mb-3">
            <CRow>
              <CCol :md="6">
                <label class="form-label">발송 날짜</label>
                <DatePicker v-model="scheduleDateModel" />
              </CCol>
              <CCol :md="6">
                <label class="form-label">발송 시간</label>
                <TimePicker v-model="scheduleTimeModel" />
              </CCol>
            </CRow>
          </div>
        </CCol>

        <!-- 발송 실행 -->
        <CCol :md="6" :xs="12">
          <div class="text-end">
            <v-btn
              :color="props.activeTab === 'sms' ? 'primary' : 'success'"
              variant="flat"
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
                :model-value="props.sendProgress"
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
