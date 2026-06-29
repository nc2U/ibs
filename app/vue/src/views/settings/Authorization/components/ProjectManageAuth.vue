<script lang="ts" setup>
import { ref, computed, onBeforeMount, watch, nextTick } from 'vue'
import { write_auth_manage } from '@/utils/pageAuth'
import { useProject } from '@/store/pinia/project'
import { bgLight } from '@/utils/cssMixins'
import Multiselect from '@vueform/multiselect'

const props = defineProps({ user: { type: Object, default: null } })

const emit = defineEmits(['get-allowed', 'get-assigned'])

const allowedProjects = ref<number[]>([])
const assignedProject = ref<number | null>(null)

const isInActive = computed(() => !props.user)

const project = useProject()
const getProjects = computed(() => project.getProjects)
const getAssigneds = computed(() =>
  getProjects.value.filter(p => allowedProjects.value.includes(p.value ?? 0)),
)

const getAllowed = () =>
  nextTick(() => {
    if (allowedProjects.value.length === 0) assignedProject.value = null
    else emit('get-allowed', allowedProjects.value)
  })
const getAssigned = () => nextTick(() => emit('get-assigned', assignedProject.value))

watch(
  () => props.user,
  newValue => {
    if (newValue && newValue?.staff_auth) {
      allowedProjects.value = newValue.staff_auth.allowed_projects
      assignedProject.value = newValue.staff_auth.default_project
    } else {
      allowedProjects.value = []
      assignedProject.value = null
    }
  },
)

onBeforeMount(() => project.fetchProjectList())
</script>

<template>
  <CCallout color="secondary" :class="bgLight" class="mt-1">
    <CRow>
      <CCol md="10" lg="8" xl="6">
        <CRow class="m-1">
          <CFormLabel class="col-md-4 col-form-label"> 허용 프로젝트</CFormLabel>
          <CCol>
            <Multiselect
              v-model="allowedProjects"
              :options="getProjects"
              placeholder="프로젝트"
              mode="tags"
              autocomplete="label"
              :classes="{ search: 'form-control multiselect-search' }"
              :add-option-on="['enter', 'tab']"
              searchable
              :disabled="isInActive || !write_auth_manage"
              @change="getAllowed"
            />
            <small class="form-text">
              사용자가 조회 및 관리할 수 있는 프로젝트들을 선택합니다.
            </small>
          </CCol>
        </CRow>
      </CCol>

      <CCol md="10" lg="8" xl="6">
        <CRow class="m-1">
          <CFormLabel class="col-md-4 col-form-label"> 담당 메인 프로젝트</CFormLabel>
          <CCol>
            <Multiselect
              v-model="assignedProject"
              :options="getAssigneds"
              placeholder="프로젝트"
              autocomplete="label"
              :classes="{ search: 'form-control multiselect-search' }"
              :add-option-on="['enter', 'tab']"
              searchable
              :disabled="isInActive || allowedProjects.length === 0"
              @change="getAssigned"
            />
            <small class="form-text">
              사용자의 각 화면에서 선택한 프로젝트를 기본 프로젝트로 보여줍니다.
            </small>
          </CCol>
        </CRow>
      </CCol>
    </CRow>
  </CCallout>
</template>
