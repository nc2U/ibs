<script lang="ts" setup>
import { computed, ref } from 'vue'
import { btnLight, colorLight } from '@/utils/cssMixins.ts'
import { useWork } from '@/store/pinia/work_project.ts'
import MdEditor from '@/components/MdEditor/Index.vue'

const emit = defineEmits(['close-form'])

const validated = ref(false)

const form = ref({
  project: '',
  title: '',
  summary: '',
  content: '',
  author: '',
  created: '',
  updated: '',
})

const workStore = useWork()
const getAllProjects = computed(() => workStore.getAllProjects)

const onsubmit = () => 1
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

  <CForm class="needs-validation mb-3" novalidate :validated="validated" @submit.prevent="onsubmit">
    <CCard :color="colorLight" class="mb-3">
      <CCardBody>
        <CRow v-if="!$route.params.projId" class="mb-2">
          <CFormLabel for="project" class="col-sm-2 col-form-label text-right required">
            프로젝트
          </CFormLabel>

          <CCol sm="8">
            <CFormSelect v-model="form.project">
              <option value="">---------</option>
              <option v-for="proj in getAllProjects" :key="proj.value">
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
            <CFormInput v-model="form.title" placeholder="공지 제목" />
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

        <CRow class="mb-2">
          <CFormLabel for="project" class="col-sm-2 col-form-label text-right">파일</CFormLabel>

          <CCol sm="10">
            <CFormInput type="file" />
          </CCol>
        </CRow>
      </CCardBody>
    </CCard>

    <v-btn color="primary" size="small">저장</v-btn>
    <v-btn :color="btnLight" @click="emit('close-form')" size="small">취소</v-btn>
  </CForm>
</template>
