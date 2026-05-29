<script lang="ts" setup>
import { reactive, computed, inject, onBeforeMount, type ComputedRef } from 'vue'
import { useRoute } from 'vue-router'
import { useAccount } from '@/store/pinia/account'
import type { IssueProject } from '@/store/types/work_project.ts'
import type { MeetingFilter, MeetingCategory } from '@/store/types/work_meeting.ts'
import DatePicker from '@/components/DatePicker/DatePicker.vue'

const props = defineProps({
  categories: { type: Array as () => MeetingCategory[], default: () => [] },
})

const emit = defineEmits(['filter-submit'])

const filter = reactive<MeetingFilter>({
  project: '',
  category: undefined,
  meeting_date: '',
  search: '',
})

const route = useRoute()

const filterSubmit = () => {
  if (route.params.projId) filter.project = route.params.projId as string
  emit('filter-submit', { ...filter })
}

const iProject = inject<ComputedRef<IssueProject>>('iProject')
const accStore = useAccount()
const getUsers = computed(() =>
  iProject?.value
    ? iProject.value?.all_members?.map(m => ({
        value: m.user.pk,
        label: m.user.username,
      }))
    : accStore.getUsers,
)

onBeforeMount(async () => {
  await accStore.fetchUsersList()
})
</script>

<template>
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
</template>

<style lang="scss" scoped>
.asideTitle {
  font-size: 1.1em;
}
</style>
