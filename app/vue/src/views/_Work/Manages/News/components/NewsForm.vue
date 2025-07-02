<script lang="ts" setup>
import { computed, ref } from 'vue'
import { btnLight, colorLight } from '@/utils/cssMixins.ts'
import { useWork } from '@/store/pinia/work_project.ts'
import MdEditor from '@/components/MdEditor/Index.vue'
import vueDropzone from 'dropzone-vue3'

const emit = defineEmits(['on-submit', 'close-form'])

const attach = ref(true)
const validated = ref(false)
const form = ref({
  project: '',
  title: '',
  summary: '',
  content: '',
  author: '',
  created: '',
  updated: '',
  files: [],
})

const dropzoneOptions = ref({
  url: 'https://httpbin.org/post',
  thumbnailWidth: 150,
  maxFilesize: 100,
  headers: { 'My-Awesome-Header': 'header value' },
})

const workStore = useWork()
const getAllProjects = computed(() => workStore.getAllProjects)

const range = (from: number, to: number): number[] =>
  from < to ? [from, ...range(from + 1, to)] : []

const newFileNum = ref(1)
const newFileRange = computed(() => range(0, newFileNum.value))
const ctlFileNum = (n: number) => {
  if (n + 1 >= newFileNum.value) newFileNum.value = newFileNum.value + 1
  else newFileNum.value = newFileNum.value - 1
}
const enableStore = (event: Event) => {
  const el = event.target as HTMLInputElement
  attach.value = !el.value
}
const fileChange = (event: Event, pk: number) => {
  enableStore(event)
  const el = event.target as HTMLInputElement
  if (el.files) {
    const file = el.files[0]
    emit('file-change', { pk, file })
  }
}

const fileUpload = (event: Event) => {
  enableStore(event)
  const el = event.target as HTMLInputElement
  if (el.files) {
    const file = el.files[0]
    emit('file-upload', file)
  }
}

const onSubmit = (event: Event) => {
  const e = event.currentTarget as HTMLSelectElement
  if (!e.checkValidity()) {
    event.preventDefault()
    event.stopPropagation()

    validated.value = true
  } else {
    emit('on-submit', { ...form.value })
  }
}
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>새 {{ ($route?.name as string).replace(/^\((.*)\)$/, '$1') }}</h5>
    </CCol>

    <CCol class="text-right">
      <span class="mr-2 form-text">
        <v-icon icon="mdi-plus-circle" color="success" size="15" />
        <router-link to="" class="ml-1">새 공지</router-link>
      </span>

      <span class="mr-2 form-text">
        <v-icon icon="mdi-star" color="secondary" size="15" />
        <router-link to="" class="ml-1" @click="">지켜보기</router-link>
      </span>
    </CCol>
  </CRow>

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
            <CFormSelect v-model="form.project" required>
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
            <!--            <CRow v-if="docs && (form.files as AFile[]).length">-->
            <!--              <CAlert :color="AlertSecondary">-->
            <!--                <small>{{ devideUri((form.files as AFile[])[0]?.file ?? ' ')[0] }}</small>-->
            <!--                <CCol-->
            <!--                  v-for="(file, i) in form.files as AFile[]"-->
            <!--                  :key="file.pk"-->
            <!--                  xs="12"-->
            <!--                  color="primary"-->
            <!--                >-->
            <!--                  <small>-->
            <!--                    현재 :-->
            <!--                    <a :href="file.file" target="_blank">-->
            <!--                      {{ devideUri(file.file ?? ' ')[1] }}-->
            <!--                    </a>-->
            <!--                    <span>-->
            <!--                      <CFormCheck-->
            <!--                        v-model="(form.files as AFile[])[i].del"-->
            <!--                        :id="`del-file-${file.pk}`"-->
            <!--                        @input="enableStore"-->
            <!--                        label="삭제"-->
            <!--                        inline-->
            <!--                        :disabled="(form.files as AFile[])[i].edit"-->
            <!--                        class="ml-4"-->
            <!--                      />-->
            <!--                      <CFormCheck-->
            <!--                        :id="`edit-file-${file.pk}`"-->
            <!--                        label="변경"-->
            <!--                        inline-->
            <!--                        @click="editFile(i)"-->
            <!--                      />-->
            <!--                    </span>-->
            <!--                    <CRow v-if="(form.files as AFile[])[i].edit">-->
            <!--                      <CCol>-->
            <!--                        <CInputGroup>-->
            <!--                          변경 : &nbsp;-->
            <!--                          <CFormInput-->
            <!--                            :id="`docs-file-${file.pk}`"-->
            <!--                            size="sm"-->
            <!--                            type="file"-->
            <!--                            @input="fileChange($event, file.pk as number)"-->
            <!--                          />-->
            <!--                        </CInputGroup>-->
            <!--                      </CCol>-->
            <!--                    </CRow>-->
            <!--                  </small>-->
            <!--                </CCol>-->
            <!--              </CAlert>-->
            <!--            </CRow>-->
            <vue-dropzone ref="myVueDropzone" id="dropzone" :options="dropzoneOptions" />

            <!--            <CRow class="mb-2">-->
            <!--              <CCol>-->
            <!--                <CInputGroup v-for="fNum in newFileRange" :key="`fn-${fNum}`" class="mb-2">-->
            <!--                  <CFormInput :id="`file-${fNum}`" type="file" @input="fileUpload" />-->
            <!--                  <CInputGroupText id="basic-addon2" @click="ctlFileNum(fNum)">-->
            <!--                    <v-icon-->
            <!--                      :icon="`mdi-${fNum + 1 < newFileNum ? 'minus' : 'plus'}-thick`"-->
            <!--                      :color="fNum + 1 < newFileNum ? 'error' : 'primary'"-->
            <!--                    />-->
            <!--                  </CInputGroupText>-->
            <!--                </CInputGroup>-->
            <!--              </CCol>-->
            <!--            </CRow>-->
          </CCol>
        </CRow>
      </CCardBody>
    </CCard>

    <v-btn type="submit" color="primary" size="small">저장</v-btn>
    <v-btn :color="btnLight" @click="emit('close-form')" size="small">취소</v-btn>
  </CForm>
</template>
