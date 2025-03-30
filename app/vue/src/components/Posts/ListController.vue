<script lang="ts" setup>
import { computed, nextTick, onBeforeMount, ref } from 'vue'
import { bgLight } from '@/utils/cssMixins'
import { numFormat } from '@/utils/baseMixins'
import { useProject } from '@/store/pinia/project'
import { type PostFilter, useBoard } from '@/store/pinia/board'

const props = defineProps({
  comFrom: { type: Boolean, default: false },
  getSuitCase: { type: Object, default: null },
  postFilter: { type: Object, required: true },
})
const emit = defineEmits(['list-filter'])

const form = ref<PostFilter>({
  issue_project: '',
  ordering: '-created',
  search: '',
  page: 1,
})

const formsCheck = computed(() => {
  const a = form.value.issue_project === ''
  const b = form.value.ordering === '-created'
  const c = form.value.search === ''
  return a && b && c
})

const boardStore = useBoard()
const postCount = computed(() => boardStore.postCount)

const listFiltering = (page = 1) => {
  nextTick(() => {
    emit('list-filter', {
      ...{ page },
      ...form,
    })
  })
}

const firstSorting = (event: { target: { value: number | null } }) => {
  form.value.issue_project = event.target.value ?? ''

  listFiltering(1)
}

const projectChange = (project: number | null) => (form.value.issue_project = project ?? '')

const resetForm = () => {
  form.value.issue_project = ''
  form.value.ordering = '-created'
  form.value.search = ''
  listFiltering(1)
}

defineExpose({ listFiltering, projectChange, resetForm })

const projectStore = useProject()
const projSelect = computed(() => projectStore.projSelect)
const fetchProjectList = () => projectStore.fetchProjectList()
onBeforeMount(() => {
  fetchProjectList()
  if (props.postFilter) {
    form.value.issue_project = props.postFilter.issue_project
    form.value.ordering = props.postFilter.ordering
    form.value.search = props.postFilter.search
    form.value.page = props.postFilter.page
  }
})
</script>

<template>
  <CCallout :color="comFrom ? 'primary' : 'success'" class="pb-0 mb-4" :class="bgLight">
    <CRow>
      <CCol lg="6">
        <CRow>
          <CCol v-if="comFrom" md="6" lg="5" xl="4" class="mb-3">
            <CFormSelect v-model="form.issue_project" @change="firstSorting">
              <option value="">본사</option>
              <option v-for="proj in projSelect" :key="proj.value" :value="proj.value">
                {{ proj.label }}
              </option>
            </CFormSelect>
          </CCol>

          <CCol md="6" lg="5" xl="4" class="mb-3">
            <CFormSelect v-model="form.ordering" @change="listFiltering(1)">
              <option value="created">작성일자 오름차순</option>
              <option value="-created">작성일자 내림차순</option>
              <option value="execution_date">발행일자 오름차순</option>
              <option value="-execution_date">발행일자 내림차순</option>
              <option value="-hit">조회수 오름차순</option>
              <option value="hit">조회수 내림차순</option>
            </CFormSelect>
          </CCol>
        </CRow>
      </CCol>

      <CCol lg="6">
        <CRow class="justify-content-md-end">
          <CCol md="6" lg="5" class="mb-3">
            <CInputGroup class="flex-nowrap">
              <CFormInput
                v-model="form.search"
                :placeholder="`제목, 내용, 첨부링크, 첨부파일명, 작성자${
                  getSuitCase ? ', 사건번호(명)' : ''
                }`"
                @keydown.enter="listFiltering(1)"
              />
              <CInputGroupText @click="listFiltering(1)">검색</CInputGroupText>
            </CInputGroup>
          </CCol>
        </CRow>
      </CCol>
    </CRow>
    <CRow>
      <CCol color="warning" class="p-2 pl-3">
        <strong> 문서 건수 조회 결과 : {{ numFormat(postCount, 0, 0) }} 건 </strong>
      </CCol>
      <CCol v-if="!formsCheck" class="text-right mb-0">
        <CButton color="info" size="sm" @click="resetForm"> 검색조건 초기화</CButton>
      </CCol>
    </CRow>
  </CCallout>
</template>
