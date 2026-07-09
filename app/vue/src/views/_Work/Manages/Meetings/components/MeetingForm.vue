<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAccount } from '@/store/pinia/account'
import { useWork } from '@/store/pinia/work_project.ts'
import { useMeeting } from '@/store/pinia/work_meeting.ts'
import { useIssue } from '@/store/pinia/work_issue.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { timeFormat } from '@/utils/baseMixins.ts'
import { isValidate } from '@/utils/helper.ts'
import MdEditor from '@/components/MdEditor/Index.vue'
import FormModal from '@/components/Modals/FormModal.vue'
import DateTimePicker from '@/components/DatePicker/DateTimePicker.vue'
import IssueForm from '@/views/_Work/Manages/Issues/components/IssueForm.vue'

const route = useRoute()
const router = useRouter()
const accStore = useAccount()
const workStore = useWork()
const meetingStore = useMeeting()
const issueStore = useIssue()

const meeting = computed(() => meetingStore.meeting)
const allProjects = computed(() => workStore.getAllProjects)
const users = computed(() => accStore.usersList)
const categories = computed(() => meetingStore.categoryList)

const statusList = computed(() => issueStore.statusList)
const priorityList = computed(() => issueStore.priorityList)
const getIssues = computed(() => issueStore.getIssues)

const validated = ref(false)
const form = ref({
  pk: null as number | null,
  project: 6 as number,
  category: null as number | null,
  status: '1' as '1' | '2' | '3',
  is_confirmed: false,
  title: '',
  agenda: '',
  content: '',
  decisions: '',
  action_items: '',
  meeting_date: timeFormat(new Date(), 'min'),
  attendees: [] as number[],
  other_attendees: '',
})

const { can, PERM } = usePerms()
const canIssueRead = computed(() => can(PERM.ISSUE_READ))
const canIssueCreate = computed(() => can(PERM.ISSUE_CREATE))
const canIssueUpdate = computed(() => can(PERM.ISSUE_UPDATE))

const canMeetingCreate = computed(() => can(PERM.MEETING_CREATE))
const canMeetingUpdate = computed(() => can(PERM.MEETING_UPDATE))
const canMeetingConfirm = computed(() => can(PERM.MEETING_CONFIRM))

const fileInput = ref<HTMLInputElement | null>(null)
const newFiles = ref<{ file: File; description: string }[]>([])
const files_del = ref<string[]>([])

const loadFile = (event: Event) => {
  const el = event.target as HTMLInputElement
  if (el.files && el.files.length > 0) {
    newFiles.value.push(...Array.from(el.files).map(file => ({ file, description: '' })))
  }
}

const removeFile = (index: number) => {
  newFiles.value.splice(index, 1)
}

const onSubmit = async (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
  } else {
    const formData = new FormData()

    // Append form fields
    for (const key in form.value) {
      const val = (form.value as any)[key]
      if (key === 'attendees') {
        val.forEach((v: number) => formData.append('attendees', v.toString()))
      } else if (val !== null && val !== undefined && val !== '') {
        formData.append(key, val as string)
      }
    }

    // Append new files
    newFiles.value.forEach(f => {
      formData.append('new_files', f.file)
      formData.append('descriptions', f.description)
    })
    files_del.value?.forEach((dfn: string) => formData.append('files_del', dfn))

    if (form.value.pk) {
      await meetingStore.updateMeeting(form.value.pk, formData as any)
    } else {
      await meetingStore.createMeeting(formData as any)
    }
    router.back()
  }
}

const refIssueModal = ref()
const selectedIssue = ref<any>(null)
const modalKey = ref(0)

const callIssueModal = async (pk?: number) => {
  if (pk) {
    await issueStore.fetchIssue(pk)
    selectedIssue.value = issueStore.issue
  } else selectedIssue.value = null

  modalKey.value++
  refIssueModal.value.callModal()
}

const createRelatedIssue = async (payload: any) => {
  if (form.value.pk) {
    const { pk, ...getData } = payload
    const formData = new FormData()

    formData.append('meeting', form.value.pk.toString())

    for (const key in getData) {
      const val = getData[key]
      if (val === null || val === undefined) continue // Skip null/undefined values

      // Skip empty strings for foreign key/numeric fields to prevent backend 500 errors
      const fkFields = [
        'project',
        'tracker',
        'status',
        'priority',
        'category',
        'fixed_version',
        'parent',
        'assigned_to',
      ]
      if (fkFields.includes(key) && val === '') continue

      if (key === 'watchers' || key === 'files')
        val?.forEach((v: number | string) => formData.append(key, JSON.stringify(v)))
      else if (key === 'newFiles') {
        val.forEach((v: any) => {
          formData.append('new_files', v.file as string | Blob)
          formData.append('descriptions', v.description ?? '')
        })
      } else {
        if (key === 'project' && !val) {
          const projectSlug = workStore.issueProject?.slug || ''
          if (projectSlug) formData.append(key, projectSlug)
        } else formData.append(key, val as string)
      }
    }

    if (pk) await issueStore.updateIssue(pk, formData)
    else await issueStore.createIssue(formData)

    await meetingStore.fetchMeeting(form.value.pk) // Refresh meeting to get updated issues list
    refIssueModal.value.close()
  }
}

const fetchMeeting = async (pk: number) => {
  await meetingStore.fetchMeeting(pk)
  if (meeting.value) {
    form.value = {
      pk: meeting.value.pk,
      project: meeting.value.project,
      category: meeting.value.category,
      status: meeting.value.status,
      is_confirmed: meeting.value.is_confirmed,
      title: meeting.value.title,
      agenda: meeting.value.agenda,
      content: meeting.value.content,
      decisions: meeting.value.decisions,
      action_items: meeting.value.action_items,
      meeting_date: meeting.value.meeting_date ? timeFormat(meeting.value.meeting_date, 'min') : '',
      attendees: meeting.value.attendees,
      other_attendees: meeting.value.other_attendees,
    }
    if (meeting.value.project_desc)
      await issueStore.fetchAllIssueList(meeting.value.project_desc.slug)
  }
}

onBeforeMount(async () => {
  await accStore.fetchUsersList()
  await workStore.fetchAllIssueProjectList()
  await issueStore.fetchStatusList()
  await issueStore.fetchPriorityList()
  await issueStore.fetchTrackerList()
  if (route.params.projId) {
    const proj = workStore.visibleProjectsFlat.find(p => p.slug === route.params.projId)
    if (proj) {
      form.value.project = proj.pk as number
      await issueStore.fetchAllIssueList(proj.slug)
    }
    await meetingStore.fetchCategoryList(route.params.projId as string)
  } else await meetingStore.fetchCategoryList()

  if (route.params.meetingId) await fetchMeeting(Number(route.params.meetingId))
})

watch(
  () => form.value.project,
  async newProjPk => {
    if (newProjPk) {
      const proj = workStore.visibleProjectsFlat.find(p => p.pk === newProjPk)
      if (proj) await issueStore.fetchAllIssueList(proj.slug)
    }
  },
)

const userOptions = computed(() =>
  users.value.map(u => ({
    value: u.pk,
    title: u.username,
  })),
)

const refCategoryModal = ref()
const categoryForm = ref({
  project: form.value.project,
  name: '',
  color: '',
  order: 1,
})

const callCategoryModal = () => {
  categoryForm.value.project = form.value.project as number
  categoryForm.value.name = ''
  categoryForm.value.color = '#fffdbd'
  categoryForm.value.order = (categories.value.length || 0) + 1
  refCategoryModal.value.callModal()
}

const onCategorySubmit = (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
  } else {
    meetingStore.createCategory(categoryForm.value as any)
    refCategoryModal.value.close()
  }
}

const onConfirmToggle = async () => {
  if (form.value.pk) await meetingStore.confirmMeeting(form.value.pk)
}
</script>

<template>
  <CCard>
    <CCardHeader>{{ !form?.pk ? '새 회의록' : '회의록 수정' }}</CCardHeader>
    <CCardBody>
      <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="onSubmit">
        <CRow class="mb-3">
          <!-- Main Content Column -->
          <CCol md="8">
            <CRow class="mb-3">
              <CFormLabel for="title" class="col-sm-2 col-form-label text-right required">
                회의 제목
              </CFormLabel>
              <CCol sm="10">
                <CFormInput
                  v-model="form.title"
                  id="title"
                  required
                  placeholder="회의 제목을 입력하세요"
                />
                <CFormFeedback invalid>제목을 입력해 주세요.</CFormFeedback>
              </CCol>
            </CRow>

            <CRow class="mb-3">
              <CFormLabel for="agenda" class="col-sm-2 col-form-label text-right">
                회의 의제
              </CFormLabel>
              <CCol sm="10">
                <CFormTextarea
                  v-model="form.agenda"
                  id="agenda"
                  rows="3"
                  placeholder="논의할 주요 의제를 입력하세요"
                />
              </CCol>
            </CRow>

            <CRow class="mb-3">
              <CFormLabel for="content" class="col-sm-2 col-form-label text-right">
                회의 내용
              </CFormLabel>
              <CCol sm="10">
                <MdEditor
                  v-model="form.content"
                  placeholder="회의 진행 내용을 입력하세요"
                  style="height: 400px"
                />
              </CCol>
            </CRow>

            <CRow class="mb-3">
              <CFormLabel for="decisions" class="col-sm-2 col-form-label text-right">
                주요 결정 사항
              </CFormLabel>
              <CCol sm="10">
                <CFormTextarea
                  v-model="form.decisions"
                  id="decisions"
                  rows="4"
                  placeholder="확정된 합의 내용을 입력하세요"
                />
              </CCol>
            </CRow>

            <CRow class="mb-3">
              <CFormLabel for="action_items" class="col-sm-2 col-form-label text-right">
                후속 조치 사항
              </CFormLabel>
              <CCol sm="10">
                <CFormTextarea
                  v-model="form.action_items"
                  id="action_items"
                  rows="4"
                  placeholder="누가, 언제까지, 무엇을 할 것인가?"
                />
              </CCol>
            </CRow>

            <!-- Existing Files Section -->
            <CRow class="mb-0">
              <CFormLabel class="col-sm-2 col-form-label text-right">파일</CFormLabel>
              <CCol sm="10">
                <div v-if="meeting?.files?.length" class="mb-2">
                  <CTable small striped hover>
                    <CTableBody>
                      <CTableRow v-for="(file, index) in meeting.files" :key="file.pk">
                        <CTableDataCell class="cursor-not-allowed">
                          {{ file.file_name }} {{ file.pk }}
                          <CFormCheck
                            label="삭제"
                            v-model="files_del"
                            :value="file.pk"
                            inline
                            class="ml-2"
                            :id="`del-${index}`"
                          />
                        </CTableDataCell>
                      </CTableRow>
                    </CTableBody>
                  </CTable>
                </div>
                <div
                  v-else
                  class="text-muted small p-2 text-center border rounded border-dashed mb-2"
                >
                  등록된 파일이 없습니다.
                </div>
              </CCol>
            </CRow>

            <!-- File Upload Section (matches IssueForm style) -->
            <CRow v-for="(f, i) in newFiles" :key="i" class="mb-2">
              <CFormLabel :for="`file-${i + 1}`" class="col-sm-2 col-form-label text-right">
              </CFormLabel>
              <CCol sm="5">
                <CFormInput type="file" @change="(e: any) => loadFile(e)" disabled />
                <span class="small text-muted">{{ f.file.name }}</span>
              </CCol>
              <CCol sm="5">
                <CInputGroup>
                  <CFormInput v-model="f.description" placeholder="부가적인 설명" />
                  <CInputGroupText @click="removeFile(i)" style="cursor: pointer">
                    <v-icon icon="mdi-trash-can-outline" size="16" />
                  </CInputGroupText>
                </CInputGroup>
              </CCol>
            </CRow>
            <CRow class="mb-3">
              <CCol :sm="{ span: 10, offset: 2 }" class="text-right">
                <input
                  type="file"
                  ref="fileInput"
                  @change="loadFile"
                  multiple
                  style="display: none"
                />
                <v-btn color="info" size="x-small" @click="fileInput?.click()">
                  <v-icon icon="mdi-paperclip" size="small" class="mr-1" /> 첨부 파일 추가
                </v-btn>
              </CCol>
            </CRow>

            <!-- Related Issues Section -->
            <CRow class="mb-3">
              <CFormLabel class="col-sm-2 col-form-label text-right">관련 업무</CFormLabel>
              <CCol sm="10">
                <v-divider class="mt-0 mb-2" />
                <div v-if="form.pk">
                  <div v-if="meeting?.issues?.length" class="mb-2">
                    <CTable small striped borderless class="border-bottom">
                      <CTableBody>
                        <CTableRow v-for="issue in meeting.issues" :key="issue.pk">
                          <CTableDataCell style="width: 60%">
                            <v-icon
                              icon="mdi-checkbox-marked-circle-outline"
                              size="small"
                              class="mr-1"
                              color="success"
                            />
                            <a
                              v-if="canIssueRead"
                              href="javascript:void(0)"
                              @click="callIssueModal(issue.pk)"
                            >
                              {{ issue.subject }}
                            </a>
                            <span v-else>{{ issue.subject }}</span>
                          </CTableDataCell>
                          <CTableDataCell style="width: 15%" class="text-center">
                            <v-chip size="x-small" label>{{ issue.status }}</v-chip>
                          </CTableDataCell>
                          <CTableDataCell style="width: 15%" class="text-right">
                            <span v-if="issue.assigned_to" class="small text-muted">
                              {{ issue.assigned_to.username }}
                            </span>
                          </CTableDataCell>
                          <CTableDataCell style="width: 10%" class="text-right">
                            <v-btn
                              v-if="canIssueUpdate"
                              icon
                              size="x-small"
                              variant="text"
                              color="success"
                              @click="callIssueModal(issue.pk)"
                            >
                              <v-icon icon="mdi-pencil" />
                            </v-btn>
                          </CTableDataCell>
                        </CTableRow>
                      </CTableBody>
                    </CTable>
                  </div>
                  <div
                    v-else
                    class="text-muted small p-2 text-center border rounded border-dashed mb-2"
                  >
                    연결된 업무가 없습니다.
                  </div>
                  <CCol v-if="canIssueCreate" class="text-right">
                    <v-btn color="info" size="x-small" @click="callIssueModal()">
                      <v-icon icon="mdi-plus" size="small" class="mr-1" /> 관련 업무 추가
                    </v-btn>
                  </CCol>
                </div>
                <div
                  v-else
                  class="text-muted small p-3 text-center border rounded border-dashed bg-more-light"
                >
                  <v-icon icon="mdi-information-outline" size="small" class="mr-1" />
                  회의 관련 업무 등록은 회의록을 먼저 <strong>저장</strong>한 후 가능합니다.
                </div>
              </CCol>
            </CRow>
          </CCol>

          <!-- Sidebar Column (Meta Info) -->
          <CCol md="4" class="bg-more-light p-4">
            <CRow class="mb-3">
              <CFormLabel for="project" class="col-sm-4 col-form-label text-right required">
                프로젝트
              </CFormLabel>
              <CCol sm="8">
                <CFormSelect
                  v-model="form.project"
                  id="project"
                  required
                  :disabled="!!route.params.projId"
                >
                  <option value="">---------</option>
                  <option v-for="proj in allProjects" :key="proj.pk" :value="proj.pk">
                    <span v-if="!!proj.depth && proj.parent_visible">
                      {{ '&nbsp;'.repeat(proj.depth) }} »
                    </span>
                    {{ proj.label }}
                  </option>
                </CFormSelect>
                <CFormFeedback invalid>프로젝트를 선택해 주세요.</CFormFeedback>
              </CCol>
            </CRow>

            <CRow class="mb-3">
              <CFormLabel for="meeting_date" class="col-sm-4 col-form-label text-right required">
                회의일시
              </CFormLabel>
              <CCol sm="8">
                <DateTimePicker
                  v-model="form.meeting_date"
                  id="meeting_date"
                  required
                  placeholder="회의 일시 선택"
                />
              </CCol>
            </CRow>

            <CRow class="mb-3">
              <CFormLabel for="category" class="col-sm-4 col-form-label text-right">
                카테고리
              </CFormLabel>
              <CCol sm="8">
                <CInputGroup>
                  <CFormSelect v-model="form.category" id="category">
                    <option :value="null">---------</option>
                    <option v-for="cat in categories" :key="cat.pk" :value="cat.pk">
                      {{ cat.name }}
                    </option>
                  </CFormSelect>
                  <CInputGroupText @click="callCategoryModal" style="cursor: pointer">
                    <v-icon icon="mdi-plus-circle" color="success" size="18" />
                  </CInputGroupText>
                </CInputGroup>
              </CCol>
            </CRow>

            <CRow class="mb-3 mt-3">
              <CFormLabel for="status" class="col-sm-4 col-form-label text-right required">
                상태
              </CFormLabel>
              <CCol sm="8">
                <CFormSelect v-model="form.status" id="status" required>
                  <option value="1">준비</option>
                  <option value="2">종료</option>
                  <option value="3">취소</option>
                </CFormSelect>
              </CCol>
            </CRow>

            <CRow class="mb-3">
              <CFormLabel class="col-sm-4 col-form-label text-right">참석자</CFormLabel>
              <CCol sm="8">
                <v-autocomplete
                  v-model="form.attendees"
                  :items="userOptions"
                  multiple
                  chips
                  closable-chips
                  density="compact"
                  variant="outlined"
                  placeholder="참석자 검색 및 선택"
                  hide-details
                />
              </CCol>
            </CRow>

            <CRow class="mb-3">
              <CFormLabel for="other_attendees" class="col-sm-4 col-form-label text-right">
                기타참석
              </CFormLabel>
              <CCol sm="8">
                <CFormInput
                  v-model="form.other_attendees"
                  id="other_attendees"
                  placeholder="외부 참석자"
                />
              </CCol>
            </CRow>

            <CRow v-if="canMeetingConfirm" class="mt-5">
              <CFormLabel for="is_confirmed" class="col-sm-4 col-form-label text-right">
                확정 여부
              </CFormLabel>
              <CCol sm="8" class="pt-2">
                <CFormSwitch
                  v-model="form.is_confirmed"
                  id="is_confirmed"
                  label="최종 승인 - 확정"
                  :disabled="form.status !== '2'"
                  @change="onConfirmToggle"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mt-4">
          <CCol class="text-right">
            <v-btn
              type="submit"
              :color="form.pk ? 'success' : 'primary'"
              :disabled="form.pk ? !canMeetingUpdate : !canMeetingCreate"
            >
              {{ form.pk ? '확인' : '저장' }}
            </v-btn>
            <v-btn color="light" @click="router.back()" flat>취소</v-btn>
          </CCol>
        </CRow>
      </CForm>
    </CCardBody>
  </CCard>

  <FormModal ref="refIssueModal" size="xl">
    <template #header>
      {{ !selectedIssue ? '회의 관련 업무 생성' : '회의 관련 업무 수정' }}
    </template>
    <template #default>
      <IssueForm
        :key="modalKey"
        :issue="selectedIssue"
        :issue-project="workStore.visibleProjectsFlat.find(p => p.pk === form.project)"
        :all-projects="allProjects"
        :status-list="statusList"
        :priority-list="priorityList"
        :get-issues="getIssues"
        :btn-size="'small'"
        @on-submit="createRelatedIssue"
        @close-form="refIssueModal.close()"
      />
    </template>
  </FormModal>

  <FormModal ref="refCategoryModal">
    <template #header> 회의록 카테고리 추가 </template>
    <template #default>
      <CForm
        class="needs-validation p-4"
        novalidate
        :validated="validated"
        @submit.prevent="onCategorySubmit"
      >
        <CRow class="mb-3">
          <CFormLabel for="cat-project" class="col-sm-3 col-form-label">프로젝트</CFormLabel>
          <CCol sm="9">
            <CFormSelect v-model="categoryForm.project" id="cat-project" disabled>
              <option v-for="proj in allProjects" :key="proj.pk" :value="proj.pk">
                {{ proj.label }}
              </option>
            </CFormSelect>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CFormLabel for="cat-name" class="col-sm-3 col-form-label">카테고리명</CFormLabel>
          <CCol sm="9">
            <CFormInput
              v-model="categoryForm.name"
              id="cat-name"
              placeholder="카테고리명을 입력하세요."
              required
            />
            <CFormFeedback invalid>카테고리명을 입력해 주세요.</CFormFeedback>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CFormLabel for="cat-color" class="col-sm-3 col-form-label">색상</CFormLabel>
          <CCol sm="9">
            <CFormInput v-model="categoryForm.color" type="color" id="cat-color" class="w-100" />
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CFormLabel for="cat-order" class="col-sm-3 col-form-label">정렬</CFormLabel>
          <CCol sm="9">
            <CFormInput v-model="categoryForm.order" id="cat-order" type="number" min="0" />
          </CCol>
        </CRow>

        <CRow>
          <CCol class="text-right">
            <v-btn type="submit" color="primary" size="small"> 저장 </v-btn>
            <v-btn color="light" size="small" @click="refCategoryModal.close()" flat> 취소 </v-btn>
          </CCol>
        </CRow>
      </CForm>
    </template>
  </FormModal>
</template>
