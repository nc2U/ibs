<script lang="ts" setup>
import { reactive, computed, nextTick, onBeforeMount } from 'vue'
import { type PostFilter, useBoard } from '@/store/pinia/board'
import { numFormat } from '@/utils/baseMixins'
import { bgLight } from '@/utils/cssMixins'

const props = defineProps({
  sort: { type: String, default: 'post' },
  postFilter: { type: Object, required: true },
})
const emit = defineEmits(['list-filter'])

const form = reactive<PostFilter>({
  ordering: '-created',
  search: '',
})

const formsCheck = computed(() => {
  const a = form.ordering === '-created'
  const b = form.search === ''
  return a && b
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

const resetForm = () => {
  form.ordering = '-created'
  form.search = ''
  listFiltering(1)
}

defineExpose({ listFiltering, resetForm })

onBeforeMount(() => {
  if (props.postFilter) {
    form.ordering = props.postFilter.ordering
    form.search = props.postFilter.search
    form.page = props.postFilter.page
  }
})
</script>

<template>
  <CCallout color="secondary" class="pb-0 mb-4" :class="bgLight">
    <CRow>
      <CCol lg="6">
        <CRow>
          <CCol md="6" lg="5" xl="4" class="mb-3">
            <CFormSelect
              v-model="form.ordering"
              @change="listFiltering(1)"
              :disabled="sort !== 'post'"
            >
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
                placeholder="제목, 내용, 첨부링크, 첨부파일명, 작성자"
                @keydown.enter="listFiltering(1)"
                :disabled="sort !== 'post'"
              />
              <CInputGroupText @click="listFiltering(1)">검색</CInputGroupText>
            </CInputGroup>
          </CCol>
        </CRow>
      </CCol>
    </CRow>
    <CRow>
      <CCol color="warning" class="p-2 pl-3">
        <strong> 게시물 건수 조회 결과 : {{ numFormat(postCount, 0, 0) }} 건 </strong>
      </CCol>
      <CCol v-if="!formsCheck" class="text-right mb-0">
        <v-btn color="info" size="small" @click="resetForm"> 검색조건 초기화</v-btn>
      </CCol>
    </CRow>
  </CCallout>
</template>
