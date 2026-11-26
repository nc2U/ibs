<script lang="ts" setup>
import { ref, watch } from 'vue'
import { getToday } from '@/utils/baseMixins'
import DatePicker from '@/components/DatePicker/DatePicker.vue'

const props = defineProps<{
  value?: string
}>()

const emit = defineEmits<{
  (e: 'set-date', date: string): void
}>()

const date = ref(props.value || getToday())

watch(
  () => props.value,
  val => {
    if (val && val !== date.value) {
      date.value = val
    }
  },
)

watch(date, val => {
  if (!val) {
    date.value = getToday()
    return
  }
  setDate()
})
const setDate = () => emit('set-date', date.value)
</script>

<template>
  <CCallout color="primary">
    <CRow>
      <CFormLabel class="col-lg-1 col-form-label">기준일자</CFormLabel>
      <CCol md="6" lg="3">
        <DatePicker v-model="date" :clearable="false" @keydown.enter="setDate" />
      </CCol>
    </CRow>
  </CCallout>
</template>
