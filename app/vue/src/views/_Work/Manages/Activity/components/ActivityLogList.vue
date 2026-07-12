<script lang="ts" setup>
import { type PropType } from 'vue'
import { dateFormat } from '@/utils/baseMixins'
import type { ActLogEntry } from '@/store/types/work_logging.ts'
import NoData from '@/components/NoData/Index.vue'
import ActivityLog from './ActivityLog.vue'

const props = defineProps({
  toDate: { type: Date as PropType<Date>, required: true },
  fromDate: { type: Date as PropType<Date>, required: true },
  activities: {
    type: Object as PropType<{ [key: string]: ActLogEntry[] }>,
    default: () => {},
  },
})

const emit = defineEmits(['to-move'])

const toBack = () => {
  if (props.toDate)
    emit('to-move', new Date(new Date(props.toDate).setDate(new Date(props.toDate).getDate() - 10)))
}

const toNext = () => {
  if (props.toDate)
    emit('to-move', new Date(new Date(props.toDate).setDate(new Date(props.toDate).getDate() + 10)))
}
</script>

<template>
  <CRow class="fst-italic">
    <CCol> {{ dateFormat(fromDate, '/') }}부터 {{ dateFormat(toDate, '/') }}까지</CCol>
  </CRow>

  <NoData v-if="!Object.getOwnPropertyNames(activities).length" />

  <CRow v-else class="my-3">
    <CCol>
      <ActivityLog
        v-for="(activity, date) in activities"
        :key="date"
        :activity="activity"
        :date="date as string"
      />
    </CCol>
  </CRow>

  <CRow>
    <CCol>
      <CButtonGroup role="group">
        <CButton color="secondary" variant="outline" size="sm" @click="toBack">« 뒤로</CButton>
        <CButton
          v-if="dateFormat(toDate) < dateFormat(new Date())"
          color="secondary"
          variant="outline"
          size="sm"
          @click="toNext"
        >
          다음 »
        </CButton>
      </CButtonGroup>
    </CCol>
  </CRow>
</template>
