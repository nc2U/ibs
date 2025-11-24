<script lang="ts" setup>
import { ref, watch } from 'vue'
import { getToday } from '@/utils/baseMixins'
import DatePicker from '@/components/DatePicker/DatePicker.vue'

const emit = defineEmits(['set-date'])

const date = ref(getToday())

watch(date, val => {
  if (!val) date.value = getToday()
  setDate()
})
const setDate = () => emit('set-date', date.value)
</script>

<template>
  <CCallout color="success">
    <CRow>
      <CFormLabel class="col-lg-1 col-form-label">기준일자</CFormLabel>
      <CCol md="6" lg="3">
        <DatePicker v-model="date" :clearable="false" @keydown.enter="setDate" />
      </CCol>
    </CRow>
  </CCallout>
</template>
