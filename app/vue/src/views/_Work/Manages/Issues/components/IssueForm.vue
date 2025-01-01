<script lang="ts" setup>
import { ref, onBeforeMount, type PropType, computed, watch, inject, type ComputedRef } from 'vue'
import type { CodeValue, Issue, IssueFile, IssueProject, IssueStatus } from '@/store/types/work'
import type { User } from '@/store/types/accounts'
import { isValidate } from '@/utils/helper'
import { useRoute } from 'vue-router'
import { useWork } from '@/store/pinia/work'
import { dateFormat } from '@/utils/baseMixins'
import { colorLight } from '@/utils/cssMixins'
import Multiselect from '@vueform/multiselect'
import MdEditor from '@/components/MdEditor/Index.vue'
import DatePicker from '@/components/DatePicker/index.vue'
import FormModal from '@/components/Modals/FormModal.vue'
import IProjectSelect from '@/views/_Work/components/IProjectSelect.vue'
import WatcherAdd from '@/views/_Work/Manages/Issues/components/aside/WatcherAdd.vue'
import FormInIssueCategory from '@/views/_Work/Manages/Issues/components/FormInIssueCategory.vue'
import FormInIssueVersion from '@/views/_Work/Manages/Issues/components/FormInIssueVersion.vue'

const props = defineProps({
  issueProject: { type: Object as PropType<IssueProject>, default: null },
  issue: { type: Object as PropType<Issue>, default: null },
  allProjects: { type: Array as PropType<IssueProject[]>, default: () => [] },
  statusList: { type: Array as PropType<IssueStatus[]>, default: () => [] },
  priorityList: { type: Array as PropType<CodeValue[]>, default: () => [] },
  getIssues: { type: Array as PropType<{ value: number; label: string }[]>, default: () => [] },
})

const emit = defineEmits(['on-submit', 'close-form'])

const RefCategoryModal = ref()
const RefVersionModal = ref()
const refWatcherAdd = ref()

const validated = ref(false)
const editDetails = ref(true)

const form = ref({
  pk: null as number | null,
  project: '',
  is_private: false,
  tracker: null as number | null,
  subject: '',
  description: '',
  status: 1 as number | null,
  parent: null as number | null,
  priority: 2 as number | null,
  start_date: dateFormat(new Date()) as string | null,
  assigned_to: null as number | null,
  due_date: null as string | null,
  category: null as number | null,
  estimated_hours: null as number | string | null,
  fixed_version: null as number | null,
  done_ratio: 0,
  watchers: [] as number[],
  files: [] as IssueFile[],
})

watch(
  () => form.value.project,
  async nVal => {
    if (nVal) {
      await workStore.fetchIssueProject(nVal)
      watcherList.value = workStore.issueProject?.all_members?.map(m => m.user) ?? []
    } else watcherList.value = memberList.value ?? []
  },
)

const assigned = ref(0)
watch(
  () => form.value.assigned_to,
  () => (assigned.value += 1),
)

watch(
  () => form.value.category,
  nVal => {
    if (assigned.value < 2) {
      if (nVal)
        form.value.assigned_to =
          categories.value.filter(c => c.pk === nVal)[0].assigned_to?.pk ?? null
      else form.value.assigned_to = null
    }
  },
)

watch(
  () => form.value.status,
  nVal => {
    if (nVal === 5) form.value.done_ratio = 100
  },
)

watch(
  () => form.value.done_ratio,
  nVal => {
    if (nVal === 100) form.value.status = 5
  },
)

const statuses = computed(() =>
  props.issue ? props.statusList : props.statusList.filter(s => s.pk === 1),
)

const assignedToMe = () => (form.value.assigned_to = userInfo?.value.pk as number)

const timeEntry = ref({
  issue: null as number | null,
  spent_on: '',
  hours: null as number | string | null,
  activity: null as number | null,
  comment: '',
})

const comment = ref({
  content: '',
  is_private: false,
})

const fileEdit = ref(false)
const newFiles = ref<{ file: File; description: string }[]>([])

const loadFile = (data: Event) => {
  const el = data.target as HTMLInputElement
  if (el.files && el.files[0]) newFiles.value.push({ file: el.files[0], description: '' })
}

const removeFile = (n: number) => {
  if (n - 1 === 0) {
    const file_form = document.getElementById(`file-${n}`) as HTMLInputElement
    file_form.value = ''
  } else {
    const file_row = document.getElementById(`row-fn-${n}`)
    if (file_row !== null) file_row?.parentNode?.removeChild(file_row)
  }
  newFiles.value.splice(n - 1, 1)
}

const formsCheck = computed(() => {
  if (props.issue) {
    const a = form.value.project === props.issue.project.slug
    const b = form.value.is_private === props.issue.is_private
    const c = form.value.tracker === props.issue.tracker.pk
    const d = form.value.subject === props.issue.subject
    const e = form.value.description === props.issue.description
    const f = form.value.status === props.issue.status.pk
    const g = form.value.parent === props.issue.parent
    const h = form.value.priority === props.issue.priority.pk
    const i = form.value.start_date === props.issue.start_date
    const j = form.value.assigned_to === props.issue.assigned_to?.pk
    const k = form.value.due_date === props.issue.due_date
    const l = form.value.category === props.issue.category
    const m = form.value.estimated_hours === numToTime(props.issue.estimated_hours)
    const n = form.value.fixed_version === props.issue.fixed_version?.pk
    const o = form.value.done_ratio === props.issue.done_ratio
    const p = !form.value.files?.map(f => f.del).some(f => f === true)
    const q = !newFiles.value.length
    const r = !timeEntry.value.hours
    const s = !timeEntry.value.activity
    const t = !timeEntry.value.comment
    const u = !comment.value.content

    const first = a && b && c && d && e && f && g && h && i && j && k
    const second = l && m && n && o && p && q && r && s && t && u
    return first && second
  } else return false
})

const route = useRoute()
const workStore = useWork()
const my_perms = computed(() => workStore.issueProject?.my_perms)

watch(props, nVal => {
  if (nVal.issueProject) form.value.project = nVal?.issueProject.slug as string
})

const watcherList = ref<{ pk: number; username: string }[]>([])

const memberList = computed(() =>
  (props.issueProject
    ? props.issueProject.all_members
    : [...new Map(workStore.memberList.map(m => [m.user.pk, m])).values()]
  )?.map(m => m.user),
)

watch(
  () => memberList.value,
  nVal => (watcherList.value = nVal ?? []),
)

const trackers = computed(() =>
  workStore.issueProject ? workStore.issueProject.trackers : workStore.trackerList,
)

const categories = computed(() => workStore.issueProject?.categories ?? [])
const default_version = ref<number | null>(null)
const versions = computed(() => workStore.issueProject?.versions ?? [])
watch(versions, nVal => {
  const def_vers = nVal.filter(v => v.is_default)
  if (!!def_vers.length) form.value.fixed_version = def_vers[0].pk ?? null
})

const activities = computed(() =>
  props.issueProject.activities ? props.issueProject.activities : [],
)

const watcherAddSubmit = (payload: { pk: number; username: string }[]) => {
  form.value.watchers = [...new Set([...form.value.watchers, ...payload.map(p => p.pk)])]
  payload.forEach(p => {
    if (!watcherList.value.map(w => w.pk).includes(p.pk))
      watcherList.value.push({ pk: p.pk, username: p.username })
  })
}

const onSubmit = (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
  } else {
    let noSubmit = false
    if (!!timeEntry.value.hours) {
      const time_entry_hours = timeToNum(timeEntry.value.hours, false)
      if (time_entry_hours) timeEntry.value.hours = time_entry_hours
      else noSubmit = true
    }

    if (!!form.value.estimated_hours) {
      const estimated_hours = timeToNum(form.value.estimated_hours, true)
      if (estimated_hours) form.value.estimated_hours = estimated_hours
      else noSubmit = true
    }

    if (noSubmit) return
    else {
      emit('on-submit', {
        ...form.value,
        ...timeEntry.value,
        newFiles: newFiles.value,
        comment_content: comment.value.content,
      })
      validated.value = false
    }
  }
}

const removeProperty = (e: Event) => {
  const el = e.currentTarget as HTMLInputElement
  el.removeAttribute('required')
}

const createCategory = (payload: any) => {
  payload.project = workStore.issueProject?.slug ?? ''
  workStore.createCategory(payload).then(res => (form.value.category = res))
}

const createVersion = (payload: any) => {
  payload.project = workStore.issueProject?.slug ?? ''
  workStore.createVersion(payload).then(res => (form.value.fixed_version = res))
}

const closeForm = () => emit('close-form')

const userInfo = inject<ComputedRef<User>>('userInfo')
const workManager = inject('workManager')

const cmtFocus = ref(false) // 댓글 폼 포커스
const callComment = () => {
  cmtFocus.value = true
  // 댓글 폼 불러오기
  comment.value.content =
    userInfo?.value.username +
    '의 댓글: \n' +
    form.value.description
      .split('\n')
      .map(line => ` > ${line}`)
      .join('') +
    '  \n\n'
}

const callReply = (payload: { id: number; user: string; content: string }) => {
  console.log(`#${route.path}#note-${payload.id}`)
  // 댓글 폼 불러오기
  comment.value.content =
    payload.user +
    `의 댓글 ([#note-${payload.id}](#${route.path}#note-${payload.id})): \n` +
    payload.content
      .split('\n')
      .map(line => ` > ${line}`)
      .join('') +
    '  \n\n'
}

defineExpose({ callComment, callReply })

const numToTime = (n: number | null) => {
  if (!n) return ''
  else {
    const hours = Math.floor(n)
    const minutes = Math.round((n - hours) * 60)
    const str = minutes >= 10 ? '' : '0'
    return `${hours}:${str}${minutes}`
  }
}

const timeToNum = (n: number | string | null, estimated: boolean) => {
  const timeNum = Number(n)

  if (!!timeNum) {
    return Math.floor(timeNum) < 1000 ? n : 999.99
  } else {
    const regex = /^(0|[1-9]\d*):(0[0-9]|[1-5][0-9])$/
    const timeStr = String(n)

    if (regex.test(timeStr)) {
      const time = timeStr.split(':')
      return (
        (Number(time[0]) < 999 ? Number(time[0]) : 999) + Number((Number(time[1]) / 60).toFixed(2))
      )
    } else {
      validated.value = true
      if (estimated) {
        form.value.estimated_hours = ''
        document.getElementById('estimated_hours')?.setAttribute('required', 'true')
        return null
      } else {
        timeEntry.value.hours = ''
        document.getElementById('hours')?.setAttribute('required', 'true')
        return null
      }
    }
  }
}

const isAssigned = (projPk: number) =>
  userInfo?.value.assigned_projects.map(p => p.pk).includes(projPk)

onBeforeMount(() => {
  watcherList.value = memberList.value ?? []
  if (props.issue) {
    editDetails.value = false

    form.value.pk = props.issue.pk
    form.value.project = props.issue.project.slug
    form.value.is_private = props.issue.is_private
    form.value.tracker = props.issue.tracker.pk
    form.value.subject = props.issue.subject
    form.value.description = props.issue.description
    form.value.status = props.issue.status.pk
    form.value.parent = props.issue.parent
    form.value.priority = props.issue.priority.pk
    form.value.start_date = props.issue.start_date
    form.value.assigned_to = props.issue.assigned_to?.pk ?? null
    form.value.due_date = props.issue.due_date
    form.value.category = props.issue.category
    form.value.estimated_hours = numToTime(props.issue.estimated_hours)
    form.value.fixed_version = props.issue.fixed_version?.pk ?? null
    form.value.done_ratio = props.issue.done_ratio
    form.value.files = props.issue.files
    workStore.fetchIssueList({ status__closed: '', project: props.issue.project.slug })
  } else form.value.fixed_version = default_version.value
  if (route.params.projId) form.value.project = route.params.projId as string
  if (route.query.tracker) form.value.tracker = Number(route.query.tracker)
  if (route.query.parent) form.value.parent = Number(route.query.parent)
})
</script>

<template>
  <CRow class="py-2">
    <CCol id="edit-form">
      <h5>
        {{ !issue ? '새 업무만들기' : '편집' }}
      </h5>
    </CCol>

    <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="onSubmit">
      <CCard :color="colorLight" class="mb-2">
        <CCardBody>
          <div v-if="!issue || isAssigned(issue.project.pk)">
            <div v-if="issue">
              <h6>속성 변경</h6>
              <v-divider class="mt-0" />
            </div>

            <CRow v-show="!issueProject || issue" class="mb-3">
              <CFormLabel for="project" class="col-sm-2 col-form-label text-right required">
                프로젝트
              </CFormLabel>

              <CCol sm="4">
                <IProjectSelect
                  v-model="form.project"
                  :all-projects="allProjects"
                  :required="true"
                />
              </CCol>

              <CCol style="padding-top: 8px">
                <CFormCheck
                  v-if="workManager"
                  v-model="form.is_private"
                  id="is_private"
                  label="비공개"
                />
              </CCol>
            </CRow>

            <CRow class="mb-3">
              <CFormLabel for="tracker" class="col-sm-2 col-form-label text-right required">
                유형
              </CFormLabel>
              <CCol sm="4">
                <CFormSelect v-model.number="form.tracker" id="tracker" required>
                  <option value="">---------</option>
                  <option v-for="tr in trackers" :value="tr.pk" :key="tr.pk">
                    {{ tr.name }}
                  </option>
                </CFormSelect>
              </CCol>
              <CCol v-if="form.tracker" sm="4" class="pt-2 text-primary">
                {{ trackers?.filter(t => t.pk === form.tracker).map(t => t.description)[0] ?? '' }}
              </CCol>

              <CCol v-if="issueProject && !issue" style="padding-top: 8px">
                <CFormCheck
                  v-if="workManager"
                  v-model="form.is_private"
                  id="is_private"
                  label="비공개"
                />
              </CCol>
            </CRow>

            <CRow class="mb-3">
              <CFormLabel for="subject" class="col-sm-2 col-form-label text-right required">
                제목
              </CFormLabel>
              <CCol sm="10">
                <CFormInput
                  v-model="form.subject"
                  maxlength="100"
                  id="subject"
                  placeholder="업무 제목"
                  required
                />
              </CCol>
            </CRow>

            <CRow class="mb-3">
              <CFormLabel for="description" class="col-sm-2 col-form-label text-right">
                설명
              </CFormLabel>
              <CCol v-if="!editDetails" sm="10" style="padding-top: 6px">
                <v-icon icon="mdi-pencil" size="sm" color="amber" />
                <router-link to="" @click="() => (editDetails = true)">편집</router-link>
              </CCol>

              <CCol v-else sm="10" id="description">
                <MdEditor v-model="form.description" placeholder="업무 내용 설명" />
              </CCol>
            </CRow>

            <CRow>
              <CCol sm="6">
                <CRow class="mb-3">
                  <CFormLabel for="status" class="col-sm-4 col-form-label text-right required">
                    상태
                  </CFormLabel>
                  <CCol sm="8">
                    <CFormSelect v-model.number="form.status" id="status" required>
                      <option value="">---------</option>
                      <option v-for="status in statuses" :value="status.pk" :key="status.pk">
                        {{ status.name }}
                      </option>
                    </CFormSelect>
                  </CCol>
                </CRow>

                <CRow class="mb-3">
                  <CFormLabel for="priority" class="col-sm-4 col-form-label text-right required">
                    우선순위
                  </CFormLabel>
                  <CCol sm="8">
                    <CFormSelect v-model.number="form.priority" id="priority" required>
                      <option value="">---------</option>
                      <option v-for="pr in priorityList" :value="pr.pk" :key="pr.pk">
                        {{ pr.name }}
                      </option>
                    </CFormSelect>
                  </CCol>
                </CRow>

                <CRow class="mb-3">
                  <CFormLabel for="assigned_to" class="col-sm-4 col-form-label text-right">
                    담당자
                  </CFormLabel>
                  <CCol sm="6">
                    <CFormSelect v-model.number="form.assigned_to" id="assigned_to">
                      <option value="">---------</option>
                      <option :value="userInfo?.pk">&lt;&lt; 나 &gt;&gt;</option>
                      <option v-for="user in memberList" :value="user.pk" :key="user.pk">
                        {{ user.username }}
                      </option>
                    </CFormSelect>
                  </CCol>
                  <CCol style="padding-top: 6px">
                    <a
                      v-if="form.assigned_to !== userInfo?.pk"
                      href="javascript:void(0)"
                      @click="assignedToMe"
                    >
                      나에게 할당
                    </a>
                  </CCol>
                </CRow>

                <CRow v-if="categories?.length" class="mb-3">
                  <CFormLabel for="category" class="col-sm-4 col-form-label text-right">
                    범주
                  </CFormLabel>
                  <CCol sm="6">
                    <CFormSelect v-model.number="form.category" id="category">
                      <option value="">---------</option>
                      <option v-for="cate in categories" :value="cate.pk" :key="cate.pk">
                        {{ cate.name }}
                        <span v-if="cate.assigned_to">{{ cate.assigned_to.username }}</span>
                      </option>
                    </CFormSelect>
                  </CCol>
                  <CCol style="padding-top: 6px">
                    <span>
                      <v-icon
                        icon="mdi-plus-circle"
                        color="success"
                        class="pointer"
                        @click="RefCategoryModal.callModal()"
                      />
                      <v-tooltip location="top" activator="parent">새 업무 범주</v-tooltip>
                    </span>
                  </CCol>
                </CRow>

                <CRow v-if="versions?.length" class="mb-3">
                  <CFormLabel for="fixed_version" class="col-sm-4 col-form-label text-right">
                    목표버전
                  </CFormLabel>
                  <CCol :sm="workManager ? 6 : 8">
                    <CFormSelect v-model.number="form.fixed_version" id="fixed_version">
                      <option value="">---------</option>
                      <option v-for="ver in versions" :value="ver.pk" :key="ver.pk">
                        {{ ver.name }}
                      </option>
                    </CFormSelect>
                  </CCol>
                  <CCol v-if="workManager" style="padding-top: 6px">
                    <span>
                      <v-icon
                        icon="mdi-plus-circle"
                        color="success"
                        class="pointer"
                        @click="RefVersionModal.callModal()"
                      />
                      <v-tooltip location="top" activator="parent">새 버전</v-tooltip>
                    </span>
                  </CCol>
                </CRow>
              </CCol>

              <CCol sm="6">
                <CRow class="mb-3">
                  <CFormLabel for="parent" class="col-sm-4 col-form-label text-right">
                    상위 업무
                  </CFormLabel>
                  <CCol sm="8">
                    <Multiselect
                      v-model="form.parent"
                      :options="getIssues"
                      id="parent"
                      placeholder="상위 업무 선택"
                      :classes="{
                        search: 'form-control multiselect-search',
                        tagsSearch: 'form-control',
                      }"
                      searchable
                    />
                  </CCol>
                </CRow>

                <CRow class="mb-3">
                  <CFormLabel for="start_date" class="col-sm-4 col-form-label text-right">
                    시작일자
                  </CFormLabel>
                  <CCol sm="8">
                    <DatePicker v-model="form.start_date" id="start_date" required />
                  </CCol>
                </CRow>

                <CRow class="mb-3">
                  <CFormLabel for="due_date" class="col-sm-4 col-form-label text-right">
                    완료기한
                  </CFormLabel>
                  <CCol sm="8">
                    <DatePicker v-model="form.due_date" id="due_date" />
                  </CCol>
                </CRow>

                <CRow class="mb-3">
                  <CFormLabel for="estimated_hours" class="col-sm-4 col-form-label text-right">
                    추정시간
                  </CFormLabel>
                  <CCol sm="6">
                    <CFormInput
                      v-model="form.estimated_hours"
                      id="estimated_hours"
                      maxlength="6"
                      type="text"
                      class="form-control"
                      placeholder="1시간 30분 (1.5 or 1:30)"
                      @input="removeProperty"
                      feedbackInvalid="999 이하의 정수, 실수 또는 '12:59' 과 같이 시간 형식을 입력하세요."
                    />
                  </CCol>
                  <CCol style="padding-top: 6px">시간</CCol>
                </CRow>

                <CRow class="mb-3">
                  <CFormLabel for="done_ratio" class="col-sm-4 col-form-label text-right">
                    진척도
                  </CFormLabel>
                  <CCol sm="8">
                    <v-slider
                      v-model.number="form.done_ratio"
                      :min="0"
                      :max="100"
                      step="5"
                      color="blue-grey-lighten-1"
                      thumb-label
                      class="align-center"
                      hide-details
                    >
                      <template v-slot:append>
                        <v-text-field
                          v-model="form.done_ratio"
                          density="compact"
                          style="width: 90px"
                          type="number"
                          hide-details
                          single-line
                        />
                      </template>
                    </v-slider>
                  </CCol>
                </CRow>
              </CCol>
            </CRow>
          </div>

          <div v-if="!issue">
            <div v-for="n in newFiles.length + 1" :key="n">
              <CRow :id="`row-fn-${n}`" class="mb-2">
                <CFormLabel :for="`file-${n}`" class="col-sm-2 col-form-label text-right">
                  <span v-if="n === 1">파일</span>
                </CFormLabel>
                <CCol sm="4">
                  <CFormInput :id="`file-${n}`" type="file" @change="loadFile" />
                </CCol>
                <CCol v-if="newFiles[n - 1]?.file" sm="6">
                  <CInputGroup>
                    <CFormInput v-model="newFiles[n - 1].description" placeholder="부가적인 설명" />
                    <CInputGroupText
                      v-if="newFiles.length === n"
                      @click="removeFile(n)"
                      :disabled="true"
                    >
                      <v-icon icon="mdi-trash-can-outline" size="16" />
                    </CInputGroupText>
                  </CInputGroup>
                </CCol>
              </CRow>
            </div>

            <CRow v-if="workManager" class="mb-3">
              <CFormLabel for="watcher" class="col-sm-2 col-form-label text-right">
                업무 관람자
              </CFormLabel>
              <CCol sm="10" style="padding-top: 8px">
                <span v-for="user in watcherList" :key="user.pk" class="mr-3">
                  <input
                    v-model="form.watchers"
                    :id="`user-${user.pk}`"
                    :value="user.pk"
                    type="checkbox"
                    class="form-check-input"
                  />
                  <label :for="`user-${user.pk}`" class="form-label form-check-label ml-2">
                    {{ user.username }}
                  </label>
                </span>
              </CCol>
              <CCol class="col-sm-2"></CCol>
              <CCol class="form-text">
                <v-icon icon="mdi-plus-circle" color="success" size="sm" class="mr-2" />
                <router-link to="" @click="refWatcherAdd.callModal()">
                  추가할 업무 관람자 검색
                </router-link>
              </CCol>
            </CRow>
          </div>

          <div v-else>
            <div v-if="!issue || isAssigned(issue.project.pk)">
              <h6>작업시간 기록</h6>
              <v-divider class="mt-0" />
              <CRow class="mb-3">
                <CFormLabel for="hours" class="col-sm-2 col-form-label text-right">
                  소요시간
                </CFormLabel>
                <div class="col-sm-3">
                  <CFormInput
                    v-model="timeEntry.hours"
                    maxlength="6"
                    id="hours"
                    placeholder="1시간 30분 (1.5 or 1:30)"
                    @input="removeProperty"
                    feedbackInvalid="999 이하의 정수, 실수 또는 '12:59' 과 같이 시간 형식을 입력하세요."
                  />
                </div>
                <div class="col-sm-1" style="padding-top: 6px">시간</div>

                <CFormLabel for="issue-project" class="col-sm-2 col-form-label text-right">
                  작업종류
                </CFormLabel>
                <CCol sm="4">
                  <CFormSelect v-model="timeEntry.activity" :required="!!timeEntry.hours">
                    <option value="">---------</option>
                    <option v-for="act in activities" :value="act.pk" :key="act.pk">
                      {{ act.name }}
                    </option>
                  </CFormSelect>
                </CCol>
              </CRow>

              <CRow class="mb-3">
                <CFormLabel for="issue-project" class="col-sm-2 col-form-label text-right">
                  설명
                </CFormLabel>
                <CCol sm="10">
                  <CFormInput v-model="timeEntry.comment" placeholder="작업 내용 요약" />
                </CCol>
              </CRow>
            </div>

            <CRow class="mb-3">
              <CCol>
                <h6>댓글</h6>
                <v-divider class="mt-0" />
                <MdEditor
                  v-model="comment.content"
                  :auto-focus="cmtFocus"
                  style="height: 180px"
                  class="mb-1"
                  placeholder="Comment"
                />
                <CFormCheck v-model="comment.is_private" id="private_comment" label="비공개 댓글" />
              </CCol>
            </CRow>

            <CRow>
              <CCol>
                <h6>파일</h6>

                <CRow v-if="fileEdit" class="mb-2">
                  <CCol>
                    <CRow v-for="(file, i) in issue.files" :key="file.pk">
                      <CCol class="cursor-not-allowed col-sm-4">
                        <v-icon icon="mdi-paperclip" size="sm" color="grey" class="mr-2" />
                        <span :class="{ del: form.files[i].del }"> {{ file.file_name }} </span>
                      </CCol>

                      <CCol>
                        <CFormCheck
                          v-model="form.files[i].del"
                          :id="`file-del-${file.pk}`"
                          label="삭제"
                        />
                      </CCol>
                    </CRow>
                  </CCol>
                </CRow>

                <v-divider class="mt-0" />

                <div v-for="n in newFiles.length + 1" :key="n">
                  <CRow :id="`row-fn-${n}`" class="mb-2">
                    <CCol sm="4">
                      <CFormInput :id="`file-${n}`" type="file" @change="loadFile" />
                    </CCol>
                    <CCol v-if="newFiles[n - 1]?.file" sm="4">
                      <CInputGroup>
                        <CFormInput
                          v-model="newFiles[n - 1].description"
                          placeholder="부가적인 설명"
                        />
                        <CInputGroupText
                          v-if="newFiles.length === n"
                          @click="removeFile(n)"
                          :disabled="true"
                        >
                          <v-icon icon="mdi-trash-can-outline" size="16" />
                        </CInputGroupText>
                      </CInputGroup>
                    </CCol>
                    <CCol v-if="form.files?.length && n === 1" class="text-right">
                      <router-link to="" @click="fileEdit = !fileEdit">첨부파일 편집</router-link>
                    </CCol>
                  </CRow>
                </div>
              </CCol>
            </CRow>
          </div>
        </CCardBody>
      </CCard>

      <CButton type="submit" :color="issue ? 'success' : 'primary'" :disabled="formsCheck">
        확인
      </CButton>
      <CButton type="button" color="light" @click="closeForm">취소</CButton>
    </CForm>
  </CRow>

  <FormModal ref="RefCategoryModal">
    <template #header>새 업무 범주</template>
    <template #default>
      <FormInIssueCategory
        :member-list="memberList"
        @close="RefCategoryModal.close()"
        @create-category="createCategory"
      />
    </template>
  </FormModal>

  <FormModal ref="RefVersionModal">
    <template #header>새 버전</template>
    <template #default>
      <FormInIssueVersion @close="RefVersionModal.close()" @create-version="createVersion" />
    </template>
  </FormModal>

  <WatcherAdd
    ref="refWatcherAdd"
    :watchers="issue?.watchers"
    @watcher-add-submit="watcherAddSubmit"
  />
</template>

<style lang="scss" scoped>
.del {
  color: #888;
  text-decoration: line-through;
}
</style>
