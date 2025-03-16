<script lang="ts" setup>
import { onBeforeMount, type PropType, ref } from 'vue'
import { colorLight } from '@/utils/cssMixins'
import type { CodeValue } from '@/store/types/work'
import DatePicker from '@/components/DatePicker/index.vue'
import MultiSelect from '@/components/MultiSelect/index.vue'
import MdEditor from '@/components/MdEditor/Index.vue'
import AddNewDoc from './AddNewDoc.vue'

defineProps({
  projStatus: { type: String, default: '' },
  projectSort: { type: String as PropType<'1' | '2' | '3'>, default: '2' },
  categories: { type: Array as PropType<CodeValue[]>, default: () => [] },
})

const emit = defineEmits(['get-categories'])

const form = ref({
  doc_type: 1,
  category: null,
  lawsuit: null,
  execution_date: null,
  title: '',
  content: '',
})

const cageChange = event => emit('get-categories', event.target.value)

onBeforeMount(() => 1)
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>새 문서</h5>
    </CCol>

    <AddNewDoc :proj-status="projStatus" />
  </CRow>

  <CRow>
    <CCard :color="colorLight" class="mb-3">
      <CCardBody>
        <CRow v-if="projectSort !== '3'" class="mb-3">
          <CFormLabel class="col-form-label text-right col-2">유형</CFormLabel>
          <CCol class="col-sm-10 col-md-6 col-lg-4 col-xl-3">
            <CFormSelect v-model.number="form.doc_type" @change="cageChange">
              <option :value="1">일반 문서</option>
              <option :value="2">소송 기록</option>
            </CFormSelect>
          </CCol>
        </CRow>

        <CRow>
          <CCol sm="12" lg="6" class="mb-3">
            <CRow>
              <CFormLabel class="col-form-label text-right col-2 col-lg-4">범주</CFormLabel>
              <CCol class="col-sm-10 col-md-6 col-lg-8 col-xl-6">
                <CFormSelect v-model.number="form.category">
                  <option value="">---------</option>
                  <option v-for="cate in categories" :value="cate.pk" :key="cate.pk">
                    {{ cate.name }}
                  </option>
                </CFormSelect>
              </CCol>
            </CRow>
          </CCol>

          <CCol v-if="form.doc_type === 1" sm="12" lg="6" class="mb-3">
            <CRow>
              <CFormLabel class="col-form-label text-right col-2 col-lg-4"> 발행일자</CFormLabel>
              <CCol class="col-sm-10 col-md-6 col-lg-8 col-xl-6">
                <DatePicker v-model="form.execution_date" />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow v-if="projectSort !== '3' && form.doc_type === 2">
          <CCol sm="12" lg="6" class="mb-3">
            <CRow>
              <CFormLabel class="col-form-label text-right col-2 col-lg-4">사건번호</CFormLabel>
              <CCol class="col-sm-10 col-md-6 col-lg-8 col-xl-6">
                <MultiSelect v-model.number="form.lawsuit" />
              </CCol>
            </CRow>
          </CCol>

          <CCol sm="12" lg="6" class="mb-3">
            <CRow>
              <CFormLabel class="col-form-label text-right col-2 col-lg-4">발행일자</CFormLabel>
              <CCol class="col-sm-10 col-md-6 col-lg-8 col-xl-6">
                <DatePicker v-model="form.execution_date" />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CFormLabel class="col-form-label text-right col-2 required">제목</CFormLabel>
          <CCol class="col-sm-10">
            <CFormInput v-model="form.title" placeholder="문서 제목" />
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CFormLabel class="col-form-label text-right col-2">설명</CFormLabel>
          <CCol class="col-sm-10">
            <MdEditor v-model="form.content" placeholder="문서 내용 설명" />
          </CCol>
        </CRow>

        <CRow class="">
          <CFormLabel class="col-form-label text-right col-2">파일</CFormLabel>
          <CCol class="col-sm-10">
            <CFormInput type="file" />
          </CCol>
        </CRow>
      </CCardBody>
    </CCard>
  </CRow>

  <CRow class="mb-5">
    <CCol>
      <CButton type="submit" color="primary" variant="outline"> 저장</CButton>
      <CButton color="light" type="submit">취소</CButton>
    </CCol>
  </CRow>
</template>
