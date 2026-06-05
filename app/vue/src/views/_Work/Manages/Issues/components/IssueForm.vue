<script lang="ts" setup>
import { computed, inject, onBeforeMount, type PropType, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useWork } from '@/store/pinia/work_project.ts'
import { useIssue } from '@/store/pinia/work_issue.ts'
import type { IssueProject, Member } from '@/store/types/work_project.ts'
import type { Issue, SimpleCategory } from '@/store/types/work_issue.ts'
import { isValidate } from '@/utils/helper.ts'
import { dateFormat } from '@/utils/baseMixins'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import FormModal from '@/components/Modals/FormModal.vue'
import Multiselect from '@vueform/multiselect'
import FormInIssueVersion from '@/views/_Work/Manages/Issues/components/FormInIssueVersion.vue'
import FormInIssueCategory from '@/views/_Work/Manages/Issues/components/FormInIssueCategory.vue'
import WatcherAdd from '@/views/_Work/Manages/Issues/components/aside/WatcherAdd.vue'
import MdEditor from '@/components/MdEditor/Index.vue'

const props = defineProps({
  issueProject: { type: Object as PropType<IssueProject>, default: null },
  issue: { type: Object as PropType<Issue>, default: null },
  allProjects: { type: Array as PropType<any[]>, default: () => [] },
  statusList: { type: Array as PropType<any[]>, default: () => [] },
  priorityList: { type: Array as PropType<any[]>, default: () => [] },
  getIssues: { type: Array as PropType<{ value: number; label: string }[]>, default: () => [] },
})

const emit = defineEmits(['on-submit', 'close-form'])

const validated = ref(false)
const userInfo = inject<any>('userInfo')
const workManager = inject<any>('workManager')

const form = ref({
  pk: null as number | null,
  project: '',
  tracker: null as number | null,
  is_private: false,
  subject: '',
  description: '',
  status: 1,
  parent: null as number | null,
  priority: 2,
  start_date: dateFormat(new Date()),
  due_date: null as string | null,
  assigned_to: null as number | null,
  fixed_version: null as number | null,
  category: null as number | null,
  expected_duration: '',
  done_ratio: 0,
  watchers: [] as number[],
  files: [] as any[],
})

const assignedToMe = () => (form.value.assigned_to = userInfo?.value.pk as number)

const comment = ref({
  content: '',
  is_private: false,
})

const newFiles = ref<{ file: File; description: string }[]>([])

const loadFile = (event: Event) => {
  const el = event.target as HTMLInputElement
  if (el.files) {
    newFiles.value.push(...Array.from(el.files).map(file => ({ file, description: '' })))
    el.value = ''
  }
}

const removeFile = (index: number) => {
  newFiles.value.splice(index, 1)
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
    const m = form.value.expected_duration === props.issue.expected_duration
    const n = form.value.fixed_version === props.issue.fixed_version?.pk
    const o = form.value.done_ratio === props.issue.done_ratio
    const p = !form.value.files?.map(f => f.del).some(f => f === true)
    const q = !newFiles.value.length
    const u = !comment.value.content

    const first = a && b && c && d && e && f && g && h && i && j && k
    const second = l && m && n && o && p && q && u
    return first && second
  } else return false
})

const route = useRoute()
const workStore = useWork()
const issueProject = computed<IssueProject | null>(() => workStore.issueProject)

watch(props, nVal => {
  if (nVal.issueProject) form.value.project = nVal?.issueProject.slug as string
})

const watcherList = ref<{ pk: number; username: string }[]>([])

const memberList = computed(() =>
  (
    (props.issueProject
      ? props.issueProject.all_members
      : [...new Map((workStore.memberList as Member[]).map(m => [m.user.pk, m])).values()]) as any
  ).map(m => m.user),
)

watch(
  () => memberList.value,
  nVal => (watcherList.value = nVal ?? []),
)

const issueStore = useIssue()
const trackers = computed(() =>
  props.issueProject ? props.issueProject.trackers : issueStore.trackerList,
)

const categories = computed(() => (props.issueProject?.categories as SimpleCategory[]) ?? [])
const default_version = ref<number | null>(null)
const versions = computed(() => props.issueProject?.versions ?? [])
watch(versions, nVal => {
  const def_vers = nVal.filter(v => v.is_default)
  if (!!def_vers.length) form.value.fixed_version = def_vers[0].pk ?? null
})

const durationOptions = [
  { value: '0', label: '당일처리' },
  { value: '1', label: '1일 이내' },
  { value: '3', label: '3일 이내' },
  { value: '5', label: '5일 이내' },
  { value: '10', label: '10일 이내' },
  { value: '30', label: '30일 이내' },
  { value: '90', label: '3개월 이내' },
  { value: '180', label: '6개월 이내' },
  { value: '365', label: '1년 이내' },
  { value: '366', label: '1년 이상' },
]

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
    emit('on-submit', {
      ...form.value,
      newFiles: newFiles.value,
      comment_content: comment.value.content,
    })
    validated.value = false
  }
}

const removeProperty = (e: Event) => {
  const el = e.currentTarget as HTMLInputElement
  el.classList.remove('is-invalid')
}

const isAssigned = (pk: number) =>
  workStore.memberList.map(m => m.user.pk).includes(userInfo?.value.pk)

const cmtFocus = ref(false)
const callComment = () => (cmtFocus.value = true)
const callReply = (payload: any) => {
  comment.value.content = `> ${payload.user} [#note-${payload.id}](이력#note-${payload.id})  \n> ${payload.content}  \n\n`
  cmtFocus.value = true
}

const RefCategoryModal = ref()
const RefVersionModal = ref()
const refWatcherAdd = ref()

const createCategory = (payload: any) => issueStore.createCategory(payload)
const createVersion = (payload: any) => workStore.createVersion(payload)

onBeforeMount(() => {
  if (props.issueProject) {
    form.value.project = props.issueProject.slug as string
  }
  if (props.issue) {
    form.value.pk = props.issue.pk
    form.value.project = props.issue.project.slug
    form.value.tracker = props.issue.tracker.pk
    form.value.is_private = props.issue.is_private
    form.value.subject = props.issue.subject
    form.value.description = props.issue.description
    form.value.status = props.issue.status.pk
    form.value.parent = props.issue.parent
    form.value.priority = props.issue.priority.pk
    form.value.start_date = dateFormat(props.issue.start_date)
    form.value.due_date = props.issue.due_date ? dateFormat(props.issue.due_date) : null
    form.value.assigned_to = props.issue.assigned_to?.pk ?? null
    form.value.fixed_version = props.issue.fixed_version?.pk ?? null
    form.value.category = props.issue.category
    form.value.expected_duration = props.issue.expected_duration ?? ''
    form.value.done_ratio = props.issue.done_ratio
    form.value.files = props.issue.files
  } else if (route.query.parent) {
    form.value.parent = Number(route.query.parent)
    form.value.tracker = Number(route.query.tracker)
  }
})

defineExpose({ callComment, callReply })
</script>

<template>
  <CCard id="edit-form">
    <CCardHeader>{{ !issue?.pk ? '새 업무' : '업무 수정' }}</CCardHeader>
    <CCardBody>
      <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="onSubmit">
        <div v-if="!issue || isAssigned(issue.project.pk)">
          <CRow class="mb-3">
            <CCol md="8">
              <CRow class="mb-3">
                <CFormLabel for="issue-project" class="col-sm-2 col-form-label text-right">
                  유형
                </CFormLabel>
                <CCol sm="4">
                  <CFormSelect v-model="form.tracker" id="tracker" required>
                    <option value="">---------</option>
                    <option v-for="tracker in trackers" :value="tracker.pk" :key="tracker.pk">
                      {{ tracker.name }}
                    </option>
                  </CFormSelect>
                </CCol>
                <CCol sm="6" class="pt-2">
                  <CFormCheck v-model="form.is_private" id="is_private" label="비공개" />
                </CCol>
              </CRow>

              <CRow class="mb-3">
                <CFormLabel for="subject" class="col-sm-2 col-form-label text-right">
                  제목
                </CFormLabel>
                <CCol sm="10">
                  <CFormInput
                    v-model="form.subject"
                    id="subject"
                    required
                    placeholder="업무 제목을 입력하세요"
                  />
                </CCol>
              </CRow>

              <CRow class="mb-3">
                <CFormLabel for="description" class="col-sm-2 col-form-label text-right">
                  설명
                </CFormLabel>
                <CCol sm="10">
                  <MdEditor
                    v-model="form.description"
                    placeholder="업무 내용을 입력하세요(마크다운 문법 지원)"
                    style="height: 350px"
                  />
                </CCol>
              </CRow>

              <CRow v-if="!issue" class="mt-3">
                <div v-for="(f, i) in newFiles.length + 1" :key="i">
                  <CRow :id="`row-fn-${i + 1}`" class="mb-2">
                    <CFormLabel :for="`file-${i + 1}`" class="col-sm-2 col-form-label text-right">
                      <span v-if="i === 0">파일</span>
                    </CFormLabel>
                    <CCol sm="5">
                      <CFormInput :id="`file-${i + 1}`" type="file" @change="loadFile" multiple />
                    </CCol>
                    <CCol v-if="newFiles[i]?.file" sm="5">
                      <CInputGroup>
                        <CFormInput v-model="newFiles[i].description" placeholder="부가적인 설명" />
                        <CInputGroupText @click="removeFile(i)" style="cursor: pointer">
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
              </CRow>
            </CCol>

            <CCol md="4" class="bg-more-light p-4">
              <CRow class="mb-3">
                <CFormLabel for="issue-project" class="col-sm-4 col-form-label text-right">
                  프로젝트
                </CFormLabel>
                <CCol sm="8">
                  <CFormSelect
                    v-model="form.project"
                    id="issue-project"
                    required
                    :disabled="!!props.issueProject || !!issue"
                  >
                    <option value="">---------</option>
                    <option v-for="proj in allProjects" :key="proj.pk" :value="proj.slug">
                      {{ proj.name }}
                    </option>
                  </CFormSelect>
                </CCol>
              </CRow>

              <CRow class="mb-3">
                <CFormLabel for="status" class="col-sm-4 col-form-label text-right">
                  상태
                </CFormLabel>
                <CCol sm="8">
                  <CFormSelect v-model="form.status" id="status" required>
                    <option v-for="status in statusList" :value="status.pk" :key="status.pk">
                      {{ status.name }}
                    </option>
                  </CFormSelect>
                </CCol>
              </CRow>

              <CRow class="mb-3 mt-3">
                <CFormLabel for="priority" class="col-sm-4 col-form-label text-right">
                  우선순위
                </CFormLabel>
                <CCol sm="8">
                  <CFormSelect v-model="form.priority" id="priority" required>
                    <option v-for="pri in priorityList" :value="pri.pk" :key="pri.pk">
                      {{ pri.name }}
                    </option>
                  </CFormSelect>
                </CCol>
              </CRow>

              <CRow class="mb-3">
                <CFormLabel for="assigned_to" class="col-sm-4 col-form-label text-right">
                  담당자
                </CFormLabel>
                <CCol sm="8">
                  <CInputGroup>
                    <CFormSelect v-model="form.assigned_to" id="assigned_to">
                      <option :value="null">---------</option>
                      <option v-for="member in memberList" :value="member.pk" :key="member.pk">
                        {{ member.username }}
                      </option>
                    </CFormSelect>
                    <CInputGroupText class="pointer" @click="assignedToMe">
                      « 나에게
                    </CInputGroupText>
                  </CInputGroup>
                </CCol>
              </CRow>

              <CRow class="mb-3">
                <CFormLabel for="parent" class="col-sm-4 col-form-label text-right">
                  상위업무
                </CFormLabel>
                <CCol sm="8">
                  <Multiselect
                    v-model="form.parent"
                    id="parent"
                    :options="getIssues"
                    placeholder="상위업무"
                    searchable
                    class="multiselect-blue"
                  />
                </CCol>
              </CRow>

              <CRow class="mb-3">
                <CFormLabel for="fixed_version" class="col-sm-4 col-form-label text-right">
                  목표단계
                </CFormLabel>
                <CCol sm="8">
                  <CInputGroup>
                    <CFormSelect v-model="form.fixed_version" id="fixed_version">
                      <option :value="null">---------</option>
                      <option v-for="ver in versions" :value="ver.pk" :key="ver.pk">
                        {{ ver.name }}
                      </option>
                    </CFormSelect>
                    <CInputGroupText
                      v-if="workManager"
                      class="pointer"
                      @click="RefVersionModal.callModal()"
                    >
                      <v-icon icon="mdi-plus-circle" color="success" size="sm" />
                    </CInputGroupText>
                  </CInputGroup>
                </CCol>
              </CRow>

              <CRow class="mb-3">
                <CFormLabel for="category" class="col-sm-4 col-form-label text-right">
                  범주
                </CFormLabel>
                <CCol sm="8">
                  <CInputGroup>
                    <CFormSelect v-model="form.category" id="category">
                      <option :value="null">---------</option>
                      <option v-for="cate in categories" :value="cate.pk" :key="cate.pk">
                        {{ cate.name }}
                      </option>
                    </CFormSelect>
                    <CInputGroupText
                      v-if="workManager"
                      class="pointer"
                      @click="RefCategoryModal.callModal()"
                    >
                      <v-icon icon="mdi-plus-circle" color="success" size="sm" />
                    </CInputGroupText>
                  </CInputGroup>
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
                <CFormLabel for="expected_duration" class="col-sm-4 col-form-label text-right">
                  예상 처리기간
                </CFormLabel>
                <CCol sm="8">
                  <CFormSelect v-model="form.expected_duration" id="expected_duration">
                    <option value="">---------</option>
                    <option v-for="dur in durationOptions" :value="dur.value" :key="dur.value">
                      {{ dur.label }}
                    </option>
                  </CFormSelect>
                </CCol>
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

        <div v-if="issue">
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
        </div>

        <CRow>
          <CCol class="text-right">
            <v-btn type="submit" color="primary" variant="flat" :disabled="formsCheck">
              확인
            </v-btn>
            <v-btn color="secondary" variant="flat" class="ml-2" @click="emit('close-form')">
              취소
            </v-btn>
          </CCol>
        </CRow>
      </CForm>
    </CCardBody>
  </CCard>

  <FormModal ref="RefCategoryModal">
    <template #header>새 업무 범주</template>
    <template #default>
      <FormInIssueCategory
        :issue-project="issueProject"
        @close="RefCategoryModal.close()"
        @create-category="createCategory"
      />
    </template>
  </FormModal>

  <FormModal ref="RefVersionModal">
    <template #header>새 단계</template>
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
