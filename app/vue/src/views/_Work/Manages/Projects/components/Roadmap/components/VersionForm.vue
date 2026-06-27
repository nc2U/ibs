<script lang="ts" setup>
import { ref, computed, onBeforeMount } from 'vue'
import { useRoute } from 'vue-router'
import { isValidate } from '@/utils/helper'
import { usePerms } from '@/composables/usePerms.ts'
import { colorLight } from '@/utils/cssMixins'
import { useWork } from '@/store/pinia/work_project.ts'
import DatePicker from '@/components/DatePicker/DatePicker.vue'

const emit = defineEmits(['on-submit'])

// 권한 설정 추가
const { can, PERM } = usePerms()
const canManageVersions = computed(() => can(PERM.PROJECT_VERSION))

const validated = ref(false)

const form = ref({
  pk: null as number | null,
  project: '',
  name: '',
  description: '',
  status: '1' as '1' | '2' | '3',
  effective_date: null as string | null,
  sharing: '0' as '0' | '1' | '2' | '3' | '4',
  is_default: false,
})

const formsCheck = computed(() => {
  if (!canManageVersions.value) return true

  if (version.value) {
    const v = version.value
    return (
      v.name === form.value.name &&
      v.description === form.value.description &&
      v.status === form.value.status &&
      v.effective_date === form.value.effective_date &&
      v.sharing === form.value.sharing &&
      v.is_default === form.value.is_default
    )
  }
  return false
})

const route = useRoute()

const workStore = useWork()
const version = computed(() => workStore.version)

const onSubmit = (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
  } else {
    const is_back = !!route.query.back
    emit('on-submit', { ...form.value }, is_back)
  }
}

const setupForm = () => {
  if (version.value) {
    form.value.pk = version.value.pk as number
    form.value.project = version.value.project?.slug as string
    form.value.name = version.value.name
    form.value.description = version.value.description
    form.value.status = version.value.status
    form.value.effective_date = version.value.effective_date
    form.value.sharing = version.value.sharing
    form.value.is_default = !!version.value.is_default
  }
}

const resetForm = () => {
  form.value.pk = null
  form.value.project = ''
  form.value.name = ''
  form.value.status = '1'
  form.value.description = ''
  form.value.effective_date = null
  form.value.sharing = '0'
  form.value.is_default = false
}

onBeforeMount(async () => {
  if (route.params.verId) {
    await workStore.fetchVersion(Number(route.params.verId))
    setupForm()
  } else resetForm()
})
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5><span v-if="route.name === '(추진현황) - 추가'">새</span> 단계</h5>
    </CCol>

    <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="onSubmit">
      <CCard :color="colorLight" class="mb-3">
        <CCardBody>
          <CRow class="mb-3">
            <CFormLabel for="name" class="col-sm-2 col-form-label text-right required">
              이름
            </CFormLabel>

            <CCol sm="10" lg="6">
              <CFormInput v-model="form.name" placeholder="새 단계 이름" required />
            </CCol>
          </CRow>

          <CRow class="mb-3">
            <CFormLabel for="name" class="col-sm-2 col-form-label text-right"> 설명</CFormLabel>

            <CCol sm="10" lg="6">
              <CFormInput v-model="form.description" placeholder="새 단계에 대한 설명" />
            </CCol>
          </CRow>

          <CRow class="mb-3">
            <CFormLabel for="name" class="col-sm-2 col-form-label text-right"> 상태</CFormLabel>

            <CCol sm="10" lg="6">
              <CFormSelect v-model="form.status">
                <option value="1">진행</option>
                <option value="2">잠김</option>
                <option value="3">닫힘</option>
              </CFormSelect>
            </CCol>
          </CRow>

          <CRow class="mb-3">
            <CFormLabel for="name" class="col-sm-2 col-form-label text-right"> 날짜</CFormLabel>

            <CCol sm="6">
              <DatePicker v-model="form.effective_date" placeholder="단계 완료 기한" />
            </CCol>
          </CRow>

          <CRow class="mb-3">
            <CFormLabel for="name" class="col-sm-2 col-form-label text-right"> 공유</CFormLabel>

            <CCol sm="6">
              <CFormSelect v-model="form.sharing">
                <option value="0">공유 없음</option>
                <option value="1">하위 프로젝트</option>
                <option value="2">상위 및 하위 프로젝트</option>
                <option value="3">최상위 및 모든 하위 프로젝트</option>
                <option value="4">모든 프로젝트</option>
              </CFormSelect>
            </CCol>
          </CRow>

          <CRow class="mb-3">
            <CFormLabel for="name" class="col-sm-2 col-form-label text-right">
              기본 단계
            </CFormLabel>

            <CCol sm="6" class="pt-2">
              <CFormCheck v-model="form.is_default" />
            </CCol>
          </CRow>
        </CCardBody>
      </CCard>

      <v-btn type="submit" :color="version ? 'success' : 'primary'" :disabled="formsCheck">
        저장
      </v-btn>
    </CForm>
  </CRow>
</template>
