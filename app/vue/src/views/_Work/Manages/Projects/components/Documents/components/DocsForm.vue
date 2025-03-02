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
  realProject: { type: Boolean, default: false },
  categories: { type: Array as PropType<CodeValue[]>, default: () => [] },
})

const emit = defineEmits(['get-categories'])

const form = ref({
  type: '1',
  category: null,
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
        <CRow v-if="realProject" class="mb-3">
          <CFormLabel class="col-form-label text-right col-2">유형</CFormLabel>
          <CCol class="col-sm-10 col-md-6 col-lg-4 col-xl-3">
            <CFormSelect v-model.number="form.type" @change="cageChange">
              <option :value="1">일반 문서</option>
              <option :value="2">소송 기록</option>
            </CFormSelect>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CFormLabel class="col-form-label text-right col-2">범주</CFormLabel>
          <CCol class="col-sm-10 col-md-6 col-lg-4 col-xl-3">
            <CFormSelect v-model.number="form.category">
              <option value="">---------</option>
              <option v-for="cate in categories" :value="cate.pk" :key="cate.pk">
                {{ cate.name }}
              </option>
            </CFormSelect>
          </CCol>

          <CFormLabel v-if="form.type === 1" class="col-form-label text-right col-2">
            발행일자
          </CFormLabel>
          <CCol v-if="form.type === 1" class="col-sm-10 col-md-6 col-lg-4 col-xl-3">
            <DatePicker />
          </CCol>
        </CRow>

        <CRow v-if="realProject && form.type === 2" class="mb-3">
          <CFormLabel class="col-form-label text-right col-2">사건번호</CFormLabel>
          <CCol class="col-sm-10 col-md-6 col-lg-4 col-xl-3">
            <MultiSelect />
          </CCol>

          <CFormLabel class="col-form-label text-right col-2">발행일자</CFormLabel>
          <CCol class="col-sm-10 col-md-6 col-lg-4 col-xl-3">
            <DatePicker />
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CFormLabel class="col-form-label text-right col-2 required">제목</CFormLabel>
          <CCol class="col-sm-10">
            <CFormInput placeholder="문서 제목" />
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CFormLabel class="col-form-label text-right col-2">설명</CFormLabel>
          <CCol class="col-sm-10">
            <MdEditor placeholder="문서 내용 설명" />
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
