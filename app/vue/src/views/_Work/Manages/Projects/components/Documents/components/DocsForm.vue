<script lang="ts" setup>
import { onMounted, onUpdated, type PropType, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { AFile, Docs } from '@/store/types/docs'
import { colorLight } from '@/utils/cssMixins'
import type { CodeValue } from '@/store/types/work'
import QuillEditor from '@/components/QuillEditor/index.vue'
import DatePicker from '@/components/DatePicker/index.vue'
import MultiSelect from '@/components/MultiSelect/index.vue'
import FileForms from '@/components/OtherParts/FileForms.vue'
import LinkForms from '@/components/OtherParts/LinkForms.vue'

const props = defineProps({
  docs: { type: Object as PropType<Docs>, default: () => null },
  typeNumber: { type: Number, default: 1 },
  projectSort: { type: String as PropType<'1' | '2' | '3'>, default: '2' },
  categories: { type: Array as PropType<CodeValue[]>, default: () => [] },
})

const form = ref<Docs>({
  pk: undefined,
  issue_project: null,
  doc_type: 1,
  category: null,
  lawsuit: null,
  execution_date: null,
  title: '',
  content: '',
  device: '',
  is_secret: false,
  password: '',
  is_blind: false,
  links: [],
  files: [],
})

const router = useRouter()

const filesSet = (payload: AFile[]) => (form.value.files = payload)

const setDocType = (type: 1 | 2) => (form.value.doc_type = type)

defineExpose({ setDocType })

const dataSetup = () => {
  if (props.docs) {
    form.value.pk = props.docs.pk
    form.value.issue_project = props.docs.issue_project
    form.value.doc_type = props.docs.doc_type
    form.value.category = props.docs.category
    form.value.lawsuit = props.docs.lawsuit
    form.value.execution_date = props.docs.execution_date
    form.value.title = props.docs.title
    form.value.content = props.docs.content
    form.value.device = props.docs.device
    form.value.is_secret = props.docs.is_secret
    form.value.password = props.docs.password
    form.value.is_blind = props.docs.is_blind
  } else form.value.doc_type = props.typeNumber
}

onUpdated(() => dataSetup())
onMounted(() => dataSetup())
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5 v-if="!docs">새 문서</h5>
      <h5 v-else>문서</h5>
    </CCol>
  </CRow>

  <CRow>
    <CCard :color="colorLight" class="mb-3">
      <CCardBody>
        <CRow v-if="projectSort !== '3'" class="mb-3">
          <CFormLabel class="col-form-label text-right col-2">유형</CFormLabel>
          <CCol class="col-sm-10 col-md-6 col-lg-4 col-xl-3">
            <CFormSelect v-model.number="form.doc_type" disabled>
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
          <CCol class="col-sm-10 mb-5">
            <QuillEditor
              v-model:content="form.content"
              placeholder="문서 내용 설명"
              style="background: white"
            />
          </CCol>
        </CRow>
        <FileForms :files="docs?.files ?? []" @files-set="filesSet" />
        <LinkForms />
      </CCardBody>
    </CCard>
  </CRow>

  <CRow class="mb-5">
    <CCol>
      <CButton type="submit" color="primary" variant="outline"> 저장</CButton>
      <CButton color="light" @click="router.replace({ name: '(문서)' })">취소</CButton>
    </CCol>
  </CRow>
</template>
