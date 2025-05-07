<script lang="ts" setup>
import { onBeforeMount, onBeforeUpdate, type PropType, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDocs } from '@/store/pinia/docs'
import type { AFile, Attatches, Docs, Link } from '@/store/types/docs'
import { colorLight } from '@/utils/cssMixins'
import type { CodeValue, IssueProject } from '@/store/types/work'
import QuillEditor from '@/components/QuillEditor/index.vue'
import DatePicker from '@/components/DatePicker/index.vue'
import MultiSelect from '@/components/MultiSelect/index.vue'
import FileForms from '@/components/OtherParts/FileForms.vue'
import LinkForms from '@/components/OtherParts/LinkForms.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AddNewDoc from './AddNewDoc.vue'

const props = defineProps({
  docs: { type: Object as PropType<Docs>, default: () => null },
  typeNumber: { type: Number, default: 1 },
  issueProject: { type: Object as PropType<IssueProject>, required: true },
  categories: { type: Array as PropType<CodeValue[]>, default: () => [] },
  getSuitCase: { type: Array as PropType<{ value: number; label: string }[]>, default: () => [] },
})

const [route, router] = [useRoute(), useRouter()]

const docStore = useDocs()
const createDocs = (payload: { form: FormData }) => docStore.createDocs(payload)
const updateDocs = (payload: { pk: number; form: FormData }) => docStore.updateDocs(payload)

const refFileForms = ref()
const refLinkForms = ref()
const refConfirmModal = ref()

const validated = ref(false)
const form = ref<Docs>({
  pk: undefined,
  issue_project: null,
  doc_type: props.typeNumber,
  category: null,
  lawsuit: null,
  execution_date: null,
  title: '',
  content: '',
  device: '',
  is_secret: false,
  password: '',
  is_blind: false,
  files: [],
  links: [],
})

const newFiles = ref<File[]>([])
const cngFiles = ref<
  {
    pk: number
    file: File
  }[]
>([])

const newLinks = ref<Link[]>([])
const newLinkPush = (payload: Link[]) => payload.forEach(link => newLinks.value.push(link))

const fileUpload = (file: File) => newFiles.value.push(file)

const fileChange = (payload: { pk: number; file: File }) => cngFiles.value.push(payload)

const filesUpdate = (payload: AFile[]) => {
  form.value.files = payload
  console.log({ ...form.value.files })
}

const linksUpdate = (payload: Link[]) => (form.value.links = payload)

const submitCheck = (event: Event) => {
  const el = event.currentTarget as HTMLFormElement
  if (!el.checkValidity()) {
    event.preventDefault()
    event.stopPropagation()

    validated.value = true
  } else {
    validated.value = false
    refLinkForms.value.newLinkPush()
    onSubmit({ ...form.value, newLinks: newLinks.value })
    refFileForms.value.checkRelease()
  } // refConfirmModal.value.callModal()
}

const onSubmit = async (payload: Docs & Attatches) => {
  const { pk, ...rest } = payload
  const getData: Record<string, any> = { ...rest }

  getData.issue_project = props.issueProject.pk
  getData.newFiles = newFiles.value
  getData.cngFiles = cngFiles.value

  const form = new FormData()

  for (const key in getData) {
    if (key === 'links' || key === 'files') {
      ;(getData[key] as any[]).forEach(val => form.append(key, JSON.stringify(val)))
    } else if (key === 'newLinks' || key === 'newFiles' || key === 'cngFiles') {
      if (key === 'cngFiles') {
        getData[key]?.forEach(val => {
          form.append('cngPks', val.pk as any)
          form.append('cngFiles', val.file as Blob)
        })
      } else (getData[key] as any[]).forEach(val => form.append(key, val as string | Blob))
    } else {
      const formValue = getData[key] === null ? '' : getData[key]
      form.append(key, formValue as string)
    }
  }

  if (pk) {
    await updateDocs({ pk, form })
    await router.replace({ name: `(문서) - 보기`, params: { docId: pk } })
  } else {
    await createDocs({ form })
    await router.replace({ name: `(문서)` })
  }
  newFiles.value = []
  cngFiles.value = []
}

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

onBeforeUpdate(() => dataSetup())
onBeforeMount(() => dataSetup())
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5 v-if="!docs">새 문서</h5>
      <h5 v-else>문서</h5>
    </CCol>

    <AddNewDoc v-if="route.name === '(문서) - 추가'" :proj-status="issueProject?.status" />
  </CRow>

  <CForm
    enctype="multipart/form-data"
    class="needs-validation"
    novalidate
    :validated="validated"
    @submit.prevent="submitCheck"
  >
    <CRow>
      <CCard :color="colorLight" class="mb-3">
        <CCardBody>
          <CRow v-if="issueProject?.sort !== '3'" class="mb-3">
            <CFormLabel class="col-form-label text-right col-2">유형</CFormLabel>
            <CCol class="col-sm-10 col-md-6 col-lg-4 col-xl-3">
              <CFormSelect v-model.number="form.doc_type" disabled required>
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

          <CRow v-if="issueProject?.sort !== '3' && form.doc_type === 2">
            <CCol sm="12" lg="6" class="mb-3">
              <CRow>
                <CFormLabel class="col-form-label text-right col-2 col-lg-4">사건번호</CFormLabel>
                <CCol class="col-sm-10 col-md-6 col-lg-8 col-xl-6">
                  <MultiSelect
                    v-model.number="form.lawsuit"
                    :options="getSuitCase"
                    :attrs="typeNumber === 2 ? { required: true } : {}"
                    placeholder="사건번호 선택"
                  />
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
              <CFormInput v-model="form.title" placeholder="문서 제목" required />
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

          <FileForms
            ref="refFileForms"
            :files="docs?.files ?? []"
            @files-update="filesUpdate"
            @file-upload="fileUpload"
            @file-change="fileChange"
          />

          <LinkForms
            ref="refLinkForms"
            :links="docs?.links ?? []"
            @links-update="linksUpdate"
            @new-link-push="newLinkPush"
          />
        </CCardBody>
      </CCard>
    </CRow>

    <CRow class="mb-5">
      <CCol>
        <v-btn type="submit" color="primary" variant="outlined" size="small"> 저장</v-btn>
        <v-btn color="light" size="small" @click="router.replace({ name: '(문서)' })">취소</v-btn>
      </CCol>
    </CRow>
  </CForm>

  <ConfirmModal ref="refConfirmModal">
    <!--    <template #header> {{ viewRoute }}</template>-->
    <!--    <template #default> {{ viewRoute }} 저장을 진행하시겠습니까?</template>-->
    <!--    <template #footer>-->
    <!--      <v-btn :color="btnClass" @click="modalAction">저장</v-btn>-->
    <!--    </template>-->
  </ConfirmModal>
</template>
