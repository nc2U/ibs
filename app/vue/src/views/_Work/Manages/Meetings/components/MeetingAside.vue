<script lang="ts" setup>
import { reactive } from 'vue'
import { useRoute } from 'vue-router'
import type { MeetingCategory, MeetingFilter } from '@/store/types/work_meeting.ts'
import DatePicker from '@/components/DatePicker/DatePicker.vue'

defineProps({
  categories: { type: Array as () => MeetingCategory[], default: () => [] },
})

const emit = defineEmits(['filter-submit'])

const filter = reactive<MeetingFilter>({
  project: '',
  category: undefined,
  status: '',
  meeting_date: '',
  search: '',
})

const route = useRoute()

const filterSubmit = () => {
  if (route.params.projId) filter.project = route.params.projId as string
  emit('filter-submit', { ...filter })
}
</script>

<template>
  <CCol class="px-3">
    <CRow class="mb-3">
      <CCol><h6 class="asideTitle">회의록 필터</h6></CCol>
    </CRow>

    <CRow class="mb-2">
      <CFormLabel for="meeting-date" class="col-sm-4 col-form-label">회의 일시</CFormLabel>
      <CCol class="col-xxl-8">
        <DatePicker v-model="filter.meeting_date" id="meeting-date" />
      </CCol>
    </CRow>

    <CRow class="mb-3">
      <CFormLabel for="meeting-status" class="col-sm-4 col-form-label">회의 상태</CFormLabel>
      <CCol class="col-xxl-8">
        <CFormSelect v-model="filter.status" id="meeting-status" size="sm">
          <option value="">---------</option>
          <option value="1">준비중</option>
          <option value="2">완료됨</option>
          <option value="3">취소됨</option>
        </CFormSelect>
      </CCol>
    </CRow>

    <CRow class="mb-3">
      <CFormLabel for="meeting-category" class="col-sm-4 col-form-label">카테고리</CFormLabel>
      <CCol class="col-xxl-8">
        <CFormSelect v-model="filter.category" id="meeting-category" size="sm">
          <option :value="undefined">---------</option>
          <option v-for="cat in categories" :value="cat.pk" :key="cat.pk">
            {{ cat.name }}
          </option>
        </CFormSelect>
      </CCol>
    </CRow>

    <CRow class="mb-3">
      <CFormLabel for="meeting-search" class="col-sm-4 col-form-label">검색어</CFormLabel>
      <CCol class="col-xxl-8">
        <CFormInput
          v-model="filter.search"
          id="meeting-search"
          size="sm"
          placeholder="제목, 내용 검색"
          @keyup.enter="filterSubmit"
        />
      </CCol>
    </CRow>

    <CRow>
      <CCol>
        <v-btn color="blue-grey-darken-1" size="small" @click="filterSubmit">적용</v-btn>
      </CCol>
    </CRow>
  </CCol>
</template>

<style lang="scss" scoped>
.asideTitle {
  font-size: 1.1em;
}
</style>
