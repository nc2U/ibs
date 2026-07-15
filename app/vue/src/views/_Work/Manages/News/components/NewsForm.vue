<script lang="ts" setup>
import { computed, onBeforeMount, type PropType, ref } from 'vue'
import { colorLight } from '@/utils/cssMixins.ts'
import { useWork } from '@/store/pinia/work_project.ts'
import { usePerms } from '@/composables/usePerms'
import type { News } from '@/store/types/work_inform.ts'
import MdEditor from '@/components/MdEditor/Index.vue'
import FileModify from '@/components/FileControl/FileModify.vue'
import FileUpload from '@/components/FileControl/FileUpload.vue'

const props = defineProps({ news: { type: Object as PropType<News | null>, default: () => null } })

const emit = defineEmits(['on-submit', 'close-form'])

const validated = ref(false)
const form = ref({
  pk: null as number | null,
  project: null as number | null,
  title: '',
  summary: '',
  content: '',
  is_important: false,
  files: [] as any,
  newFiles: [] as File[],
  cngFiles: [] as { pk: number; file: File }[],
})

const { can, PERM } = usePerms()
const workStore = useWork()
const getNewsProjects = computed(() =>
  workStore.allProjects
    .filter(proj => proj.module?.news)
    .map(i => ({
      pk: i.pk as number,
      value: i.pk as number,
      label: i.name,
      depth: i.depth,
      parent_visible: i.parent_visible,
    })),
)

const RefNewFiles = ref()
const fileUpload = (newFiles: any[]) => (form.value.newFiles = newFiles)
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
  } else {
    RefNewFiles.value.getNewFiles()
    emit('on-submit', { ...form.value })
  }
}

onBeforeMount(() => {
  if (props.news) {
    form.value.pk = props.news.pk
    form.value.project = props.news?.project.pk as number
    form.value.title = props.news?.title as string
    form.value.summary = props.news?.summary as string
    form.value.content = props.news?.content as string
    form.value.is_important = props.news?.is_important
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
              <option v-for="proj in getNewsProjects" :value="proj.pk" :key="proj.pk">
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

          <CCol sm="6">
            <CFormInput v-model="form.title" placeholder="공지 제목" required />
          </CCol>
          <CCol sm="4" class="pt-2">
            <CFormCheck
              id="is_important"
              v-model="form.is_important"
              label="중요 공지 (상단 고정)"
            />
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
          <CCol md="10" lg="9" xl="8">
            <FileModify
              v-if="news && form.files.length"
              :files="form.files"
              @file-delete="fileDelete"
              @file-change="fileChange"
            />

            <FileUpload ref="RefNewFiles" @file-upload="fileUpload" />
          </CCol>
        </CRow>
      </CCardBody>
    </CCard>

    <CCol class="mt-4 mb-5 text-right">
      <v-btn type="submit" :color="news ? 'success' : 'primary'" :disabled="!can(PERM.NEWS_MANAGE)">
        저장
      </v-btn>
      <v-btn color="light" @click="emit('close-form')" flat>취소</v-btn>
    </CCol>
  </CForm>
</template>
