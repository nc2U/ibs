<script lang="ts" setup>
import { computed, onBeforeMount, type PropType, ref } from 'vue'
import { btnLight, colorLight } from '@/utils/cssMixins.ts'
import { useWork } from '@/store/pinia/work_project.ts'
import type { News } from '@/store/types/work_inform.ts'
import MdEditor from '@/components/MdEditor/Index.vue'
import FileModify from '@/components/FileControl/FileModify.vue'
import FileUpload from '@/components/FileControl/FileUpload.vue'

const props = defineProps({ news: { type: Object as PropType<News | null>, default: () => null } })
const emit = defineEmits(['on-submit', 'close-form'])

const attach = ref(true)
const validated = ref(false)
const form = ref({
  pk: null as number | null,
  project: null as number | null,
  title: '',
  summary: '',
  content: '',
  files: [] as any,
  newFiles: [] as File[],
  cngFiles: [] as { pk: number; file: File }[],
})

const workStore = useWork()
const getAllProjects = computed(() => workStore.getAllProjects)

const fileUpload = (file: File) => form.value.newFiles.push(file)
const fileChange = (payload: { pk: number; file: File }) => form.value.cngFiles.push(payload)
const fileDelete = (payload: { pk: number; del: boolean }): void => {
  const file = form.value.files.find((f: any) => f.pk === payload.pk)
  if (file) file.del = payload.del
}

const onSubmit = (event: Event) => {
  const e = event.currentTarget as HTMLSelectElement
  if (!e.checkValidity()) {
    event.preventDefault()
    event.stopPropagation()

    validated.value = true
  } else emit('on-submit', { ...form.value })
}

onBeforeMount(() => {
  if (props.news) {
    form.value.pk = props.news.pk
    form.value.project = props.news?.project.pk as number
    form.value.title = props.news?.title as string
    form.value.summary = props.news?.summary as string
    form.value.content = props.news?.content as string
    form.value.files = props.news.files
  }
})
</script>

<template>
  <CForm
    class="needs-validation mb-4"
    enctype="multipart/form-data"
    novalidate
    :validated="validated"
    @submit.prevent="onSubmit"
  >
    <CCard :color="colorLight" class="mb-3">
      <CCardBody>
        <CRow v-if="!$route.params.projId" class="mb-2">
          <CFormLabel for="project" class="col-sm-2 col-form-label text-right required">
            프로젝트
          </CFormLabel>

          <CCol sm="8">
            <CFormSelect v-model="form.project" :required="!$route.params.projId">
              <option value="">---------</option>
              <option v-for="proj in getAllProjects" :value="proj.value" :key="proj.value">
                <span v-if="!!proj.depth && proj.parent_visible">
                  {{ '&nbsp;'.repeat(proj.depth) }} »
                </span>
                {{ proj.label }}
              </option>
            </CFormSelect>
          </CCol>
        </CRow>

        <CRow class="mb-2">
          <CFormLabel for="project" class="col-sm-2 col-form-label text-right required">
            제목
          </CFormLabel>

          <CCol sm="8">
            <CFormInput v-model="form.title" placeholder="공지 제목" required />
          </CCol>
        </CRow>

        <CRow class="mb-2">
          <CFormLabel for="project" class="col-sm-2 col-form-label text-right"> 요약</CFormLabel>

          <CCol sm="10">
            <CFormTextarea v-model="form.summary" placeholder="공지 요약" />
          </CCol>
        </CRow>

        <CRow class="mb-2">
          <CFormLabel for="project" class="col-sm-2 col-form-label text-right"> 내용</CFormLabel>

          <CCol sm="10">
            <MdEditor v-model="form.content" placeholder="공지 내용" />
          </CCol>
        </CRow>

        <CRow>
          <CFormLabel for="title" class="col-md-2 col-form-label text-right">파일</CFormLabel>
          <CCol md="10" lg="8" xl="6">
            <FileModify
              v-if="form.files.length"
              :files="form.files"
              @file-delete="fileDelete"
              @file-change="fileChange"
            />

            <FileUpload @file-upload="fileUpload" />
          </CCol>
        </CRow>
      </CCardBody>
    </CCard>

    <v-btn type="submit" :color="news ? 'success' : 'primary'" size="small">저장</v-btn>
    <v-btn :color="btnLight" @click="emit('close-form')" size="small">취소</v-btn>
  </CForm>
</template>
