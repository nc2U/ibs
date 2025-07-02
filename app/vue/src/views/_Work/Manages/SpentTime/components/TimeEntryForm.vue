<script lang="ts" setup>
import { ref, computed, onBeforeMount, type PropType, watch } from 'vue'
import { useRoute } from 'vue-router'
import { isValidate } from '@/utils/helper'
import { useWork } from '@/store/pinia/work_project.ts'
import { useIssue } from '@/store/pinia/work_issue.ts'
import { btnLight, colorLight } from '@/utils/cssMixins'
import { dateFormat } from '@/utils/baseMixins'
import type { getProject, IssueProject } from '@/store/types/work_project.ts'
import DatePicker from '@/components/DatePicker/index.vue'
import Multiselect from '@vueform/multiselect'
import type { TimeEntry } from '@/store/types/work_issue.ts'

defineProps({
  allProjects: { type: Array as PropType<getProject[]>, default: () => [] },
})

const validated = ref(false)

const form = ref({
  pk: null as number | null,
  project: '',
  issue: null as number | null,
  user: null as number | null,
  spent_on: dateFormat(new Date()),
  hours: '',
  comment: '',
  activity: null as number | null,
})

watch(
  () => form.value.project,
  nVal => {
    if (nVal) {
      workStore.fetchIssueProject(nVal)
      issueStore.fetchAllIssueList(nVal)
    }
  },
)

const emit = defineEmits(['on-submit', 'close-form'])

const formCheck = computed(() => {
  if (timeEntry.value) {
    const a = form.value.project === issueProject.value?.slug
    const b = form.value.issue === timeEntry.value.issue.pk
    const c = form.value.user === timeEntry.value?.user.pk
    const d = form.value.spent_on === timeEntry.value.spent_on
    const e = form.value.hours === timeEntry.value.hours
    const f = form.value.activity === timeEntry.value.activity.pk
    const g = form.value.comment === timeEntry.value.comment
    return a && b && c && d && e && f && g
  } else return false
})

const onSubmit = (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
  } else emit('on-submit', { ...form.value })
}

const closeForm = () => emit('close-form')

const workStore = useWork()
const issueProject = computed<IssueProject | null>(() => workStore.issueProject)
const memberList = computed(() =>
  issueProject.value ? issueProject.value.all_members : workStore.memberList,
)

const issueStore = useIssue()
const getIssues = computed(() => issueStore.getIssues)
const timeEntry = computed<TimeEntry | null>(() => issueStore.timeEntry)
const activityList = computed(() => issueStore.activityList)

const activities = computed(() =>
  issueProject.value ? issueProject.value.activities : activityList.value,
)

const route = useRoute()

const dataSetup = () => {
  if (timeEntry.value) {
    form.value.pk = timeEntry.value?.pk as number
    form.value.issue = timeEntry.value.issue.pk
    form.value.user = timeEntry.value.user.pk
    form.value.spent_on = timeEntry.value.spent_on
    form.value.hours = timeEntry.value.hours
    form.value.activity = timeEntry.value.activity.pk
    form.value.comment = timeEntry.value.comment
  }
  if (issueProject.value) form.value.project = issueProject.value?.slug as string
}

watch(timeEntry, nVal => {
  if (nVal) dataSetup()
})

onBeforeMount(() => {
  if (route.params.projId) {
    workStore.fetchIssueProject(route.params.projId as string)
    form.value.project = route.params.projId as string
    issueStore.fetchIssueList({ status__closed: '', project: form.value.project })
    issueStore.fetchAllIssueList(route.params.projId as string)
  } else issueStore.fetchAllIssueList()
  if (route.params.timeId) issueStore.fetchTimeEntry(Number(route.params.timeId))
  else issueStore.timeEntry = null

  if (route.query.issue_id) form.value.issue = Number(route.query.issue_id)

  workStore.fetchMemberList()
  issueStore.fetchActivityList()
  dataSetup()
})
</script>

<template>
  <CCol>
    <h5>소요시간</h5>
  </CCol>

  <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="onSubmit">
    <CRow class="py-2">
      <CCard :color="colorLight" class="mb-2">
        <CCardBody>
          <CRow class="mb-3">
            <CFormLabel
              v-show="!route.params.projId || timeEntry"
              for="project"
              class="col-sm-2 col-form-label text-right required"
            >
              프로젝트
            </CFormLabel>

            <CCol v-show="!route.params.projId || timeEntry" sm="4">
              <CFormSelect v-model="form.project" id="project" required>
                <option value="">---------</option>
                <option v-for="proj in allProjects" :value="proj.slug" :key="proj.slug">
                  <span v-if="proj.depth === 2"> &nbsp;&nbsp;» </span>
                  <span v-if="proj.depth === 3"> &nbsp;&nbsp;&nbsp;&nbsp;» </span>
                  <span v-if="proj.depth === 4"> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;» </span>
                  <span v-if="proj.depth === 5">
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;»
                  </span>
                  {{ proj.label }}
                </option>
              </CFormSelect>
            </CCol>

            <CFormLabel for="issue" class="col-sm-2 col-form-label text-right required">
              업무
            </CFormLabel>
            <CCol sm="4">
              <Multiselect
                v-model="form.issue"
                :options="getIssues"
                id="issue"
                placeholder="업무 선택"
                :classes="{
                  search: 'form-control multiselect-search',
                  tagsSearch: 'form-control',
                }"
                searchable
                required
              />
            </CCol>
          </CRow>

          <CRow v-if="timeEntry" class="mb-3">
            <CFormLabel for="user" class="col-sm-2 col-form-label text-right required">
              사용자
            </CFormLabel>
            <CCol sm="4">
              <CFormSelect v-model.number="form.user" id="user" required>
                <option value="">---------</option>
                <option v-for="mem in memberList" :value="mem.user.pk" :key="mem.user.pk">
                  {{ mem.user.username }}
                </option>
              </CFormSelect>
            </CCol>
          </CRow>

          <CRow class="mb-3">
            <CFormLabel for="spent_on" class="col-sm-2 col-form-label text-right required">
              작업일자
            </CFormLabel>
            <CCol sm="4">
              <DatePicker v-model="form.spent_on" id="spent_on" required />
            </CCol>
          </CRow>

          <CRow class="mb-3">
            <CFormLabel for="hours" class="col-sm-2 col-form-label text-right required">
              시간
            </CFormLabel>
            <CCol sm="4">
              <CFormInput
                v-model="form.hours"
                id="hours"
                maxlength="10"
                placeholder="소요시간"
                required
              />
            </CCol>

            <CFormLabel for="activity" class="col-sm-2 col-form-label text-right required">
              작업종류
            </CFormLabel>
            <CCol sm="4">
              <CFormSelect v-model.number="form.activity" id="activity" required>
                <option value="">---------</option>
                <option v-for="act in activities" :value="act.pk" :key="act.pk">
                  {{ act.name }}
                </option>
              </CFormSelect>
            </CCol>
          </CRow>

          <CRow class="mb-3">
            <CFormLabel for="comment" class="col-sm-2 col-form-label text-right"> 설명</CFormLabel>
            <CCol sm="10">
              <CFormInput
                v-model="form.comment"
                id="comment"
                maxlength="255"
                placeholder="소요시간에 대한 설명"
              />
            </CCol>
          </CRow>
        </CCardBody>
      </CCard>

      <CCol>
        <v-btn type="submit" :color="timeEntry ? 'success' : 'primary'" :disabled="formCheck">
          확인
        </v-btn>
        <v-btn type="button" :color="btnLight" @click="closeForm">취소</v-btn>
      </CCol>
    </CRow>
  </CForm>
</template>
