<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { btnLight } from '@/utils/cssMixins.ts'
import { useAccount } from '@/store/pinia/account'
import { useMeeting } from '@/store/pinia/work_meeting.ts'
import { useWork } from '@/store/pinia/work_project.ts'
import { useIssue } from '@/store/pinia/work_issue.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { elapsedTime, timeFormat } from '@/utils/baseMixins.ts'
import { markdownRender } from '@/utils/helper.ts'
import { diffDate, getMeetingStatusColor } from '@/utils/baseMixins.ts'
import FileDisplay from '@/views/_Work/components/atomics/FileDisplay.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import FormModal from '@/components/Modals/FormModal.vue'
import IssueForm from '@/views/_Work/Manages/Issues/components/IssueForm.vue'

const route = useRoute()
const router = useRouter()
const accountStore = useAccount()
const meetingStore = useMeeting()
const workStore = useWork()
const issueStore = useIssue()

const meeting = computed(() => meetingStore.meeting)

const isCreator = computed(() => meeting.value?.creator.pk === accountStore.userInfo?.pk)
const isAttendee = computed(() =>
  meeting.value?.attendees_desc.some(user => user.pk === accountStore.userInfo?.pk),
)

const { can, PERM } = usePerms()
const canIssueCreate = computed(() => can(PERM.ISSUE_CREATE))
const canMeetingUpdate = computed(() => {
  if (meeting.value) {
    if (meeting.value.is_confirmed) return can(PERM.MEETING_EDIT_CONFIRMED)
    if (can(PERM.MEETING_UPDATE)) return true
    if (can(PERM.MEETING_OWN_UPDATE)) return isCreator.value || isAttendee.value
  }
  return false
})
const canMeetingDelete = computed(() => can(PERM.MEETING_DELETE))

const statusList = computed(() => issueStore.statusList)
const priorityList = computed(() => issueStore.priorityList)
const getIssues = computed(() => issueStore.getIssues)

const statusColor = computed(() => getMeetingStatusColor(meeting.value?.status ?? '4'))

const needConfirm = computed(() => {
  return (
    meeting.value?.status === '2' &&
    meeting.value?.meeting_date &&
    !meeting.value?.is_confirmed &&
    diffDate(meeting.value.meeting_date) > 5
  )
})

const confirmAlertColor = computed(() => {
  const meetingDate = meeting.value?.meeting_date

  if (!meetingDate) return ''

  const diff = diffDate(meetingDate)

  return diff > 10 ? 'danger' : 'warning'
})

const completedIssues = computed(() => meeting.value?.issues.filter(i => i.closed).length ?? 0)
const completedRatio = computed(() => {
  const total = meeting.value?.issues.length ?? 0
  return total === 0 ? 0 : Math.round((completedIssues.value / total) * 100)
})

const fetchMeeting = async (pk: number) => {
  await meetingStore.fetchMeeting(pk)
  if (meeting.value?.project_desc) {
    await workStore.fetchIssueProject(meeting.value.project_desc.slug)
    await issueStore.fetchAllIssueList(meeting.value.project_desc.slug)
  }
}

const refIssueModal = ref()

const createRelatedIssue = async (payload: any) => {
  if (meeting.value) {
    const { pk, ...getData } = payload
    const formData = new FormData()

    getData.meeting = meeting.value.pk

    for (const key in getData) {
      const val = getData[key]
      if (val === null || val === undefined) continue

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
          const projectSlug =
            meeting.value?.project_desc?.slug || workStore.issueProject?.slug || ''
          if (projectSlug) formData.append(key, projectSlug)
        } else {
          formData.append(key, val as string)
        }
      }
    }

    await issueStore.createIssue(formData)
    await meetingStore.fetchMeeting(meeting.value.pk)
    refIssueModal.value.close()
  }
}

const deleteMeeting = async () => {
  if (meeting.value) {
    const projId = (route.params.projId as string) || meeting.value.project_desc?.slug
    await meetingStore.deleteMeeting(meeting.value.pk, projId)
    if (projId) {
      await router.push({ name: '(회의)', params: { projId } })
    } else {
      await router.push({ name: '회의' })
    }
  }
}

const deleteFile = async (fileId: number) => {
  const form = new FormData()
  form.append('del_file', JSON.stringify(fileId))
  if (meeting.value) await meetingStore.patchMeeting(meeting.value?.pk, form)
}

const goList = () => {
  const projId = (route.params.projId as string) || meeting.value?.project_desc?.slug
  if (projId) {
    router.push({ name: '(회의)', params: { projId } })
  } else {
    router.push({ name: '회의' })
  }
}

const goEdit = () => {
  const projId = (route.params.projId as string) || meeting.value?.project_desc?.slug
  if (projId && meeting.value) {
    router.push({
      name: '(회의) - 수정',
      params: { projId, meetingId: meeting.value.pk },
    })
  }
}

const downloadPdf = () => {
  if (meeting.value) {
    meetingStore.generatePdf(meeting.value.pk)
  }
}

onBeforeMount(async () => {
  if (route.params.meetingId) {
    await fetchMeeting(Number(route.params.meetingId))
  }
  await issueStore.fetchStatusList()
  await issueStore.fetchPriorityList()
  await issueStore.fetchTrackerList()
  await workStore.fetchIssueProjectList({})
})

watch(
  () => route.params.meetingId,
  newId => {
    if (newId) fetchMeeting(Number(newId))
  },
)

const refConfirmModal = ref()
</script>

<template>
  <div v-if="meeting" class="p-3">
    <CRow class="mb-2">
      <CCol>
        <h5>
          <v-icon icon="mdi-account-group" class="mr-2" />
          <span>회의록 #{{ meeting.pk }}</span>
          <v-badge
            :color="statusColor"
            :content="meeting.status_display"
            inline
            rounded="1"
            class="ml-2"
          />
        </h5>
      </CCol>

      <CCol class="text-right">
        <v-btn color="primary" size="small" class="ml-2" @click="downloadPdf">
          <v-icon icon="mdi-file-pdf-box" size="small" class="mr-1" /> PDF 출력
        </v-btn>
      </CCol>
    </CRow>

    <CCard class="mb-4 shadow-sm card-white">
      <CCardBody>
        <CRow class="mb-3">
          <CCol>
            <span class="sub-title">{{ meeting.title }}</span>
          </CCol>
        </CRow>

        <CRow>
          <CCol>
            <p class="mt-1 form-text text-muted">
              <strong>{{ meeting.creator.username }}</strong> 이(가)
              <span>
                {{ elapsedTime(meeting.created) }}
                <v-tooltip activator="parent" location="top">
                  {{ timeFormat(meeting.created) }}
                </v-tooltip>
              </span>
              전에 추가함.
              <span v-if="meeting.updater">
                <span class="mx-1">/</span>
                <strong>{{ meeting.updater.username }}</strong> 이(가)
                {{ elapsedTime(meeting.updated) }}
                <v-tooltip activator="parent" location="top">
                  {{ timeFormat(meeting.updated) }}
                </v-tooltip>
                전에 마지막으로 수정함.
              </span>
            </p>
          </CCol>
        </CRow>

        <v-divider class="my-3" />

        <CRow>
          <CCol md="6">
            <CRow class="mb-2">
              <CCol class="title" sm="4">프로젝트 :</CCol>
              <CCol sm="8">{{ meeting.project_desc?.name || '회사 본사' }}</CCol>
            </CRow>
            <CRow class="mb-2">
              <CCol class="title" sm="4">카테고리 :</CCol>
              <CCol sm="8">{{ meeting.category_desc?.name || '-' }}</CCol>
            </CRow>
            <CRow class="mb-2">
              <CCol class="title" sm="4">회의 상태 :</CCol>
              <CCol sm="8">
                <v-chip :color="statusColor" size="x-small" variant="flat" class="px-2">
                  {{ meeting.status_display }}
                </v-chip>

                <v-chip
                  v-if="needConfirm"
                  :color="confirmAlertColor"
                  size="x-small"
                  variant="flat"
                  class="ml-1"
                >
                  확정 필요
                </v-chip>
                <v-chip
                  v-if="meeting.is_confirmed"
                  color="success"
                  size="x-small"
                  variant="flat"
                  class="ml-1"
                >
                  확정
                </v-chip>
              </CCol>
            </CRow>
          </CCol>

          <CCol md="6">
            <CRow class="mb-2">
              <CCol class="title" sm="4">회의 일시 :</CCol>
              <CCol sm="8">
                {{ meeting.meeting_date ? timeFormat(meeting.meeting_date, 'min') : '-' }}
              </CCol>
            </CRow>
            <CRow class="mb-2">
              <CCol class="title" sm="4">참 석 자 :</CCol>
              <CCol sm="8">
                <v-chip
                  v-for="user in meeting.attendees_desc"
                  :key="user.pk"
                  size="x-small"
                  color="primary"
                  class="mr-1 mb-1"
                >
                  {{ user.username }}
                </v-chip>
                <div v-if="meeting.other_attendees" class="text-muted small mt-1">
                  (외부: {{ meeting.other_attendees }})
                </div>
              </CCol>
            </CRow>
            <CRow class="mb-2" v-if="meeting.issues?.length">
              <CCol class="title" sm="4">관련 업무 :</CCol>
              <CCol sm="8">
                완료 {{ completedIssues }}건 / 전체 {{ meeting.issues.length }}건 ({{
                  completedRatio
                }}% 완료)
                <div style="width: 182px">
                  <v-progress-linear
                    :model-value="completedRatio"
                    height="6"
                    :color="completedRatio === 100 ? 'success' : 'primary'"
                  />
                </div>
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <v-divider class="my-4" />

        <div v-if="meeting.agenda" class="mb-5">
          <h6 class="title mb-2">
            <v-icon icon="mdi-bullseye-arrow" color="text-primary" size="small" class="mr-1" />
            회의 의제
          </h6>
          <div
            class="markdown-content p-3 border rounded"
            v-html="markdownRender(meeting.agenda)"
          />
        </div>

        <div v-if="meeting.content" class="mb-5">
          <h6 class="title mb-2">
            <v-icon icon="mdi-text-box-outline" color="text-primary" size="small" class="mr-1" />
            회의 내용
          </h6>
          <div
            class="markdown-content p-3 border rounded"
            v-html="markdownRender(meeting.content)"
          />
        </div>

        <CRow>
          <CCol md="6" v-if="meeting.decisions">
            <CCallout color="success" class="mb-4 border-start-4">
              <div class="d-flex align-items-center mb-2">
                <v-icon color="success" icon="mdi-check-circle" size="small" class="mr-1" />
                <span class="fw-bold text-success">주요 결정 사항</span>
              </div>
              <div
                class="markdown-content bg-transparent"
                v-html="markdownRender(meeting.decisions)"
              ></div>
            </CCallout>
          </CCol>
          <CCol md="6" v-if="meeting.action_items">
            <CCallout color="warning" class="mb-4 border-start-4">
              <div class="d-flex align-items-center mb-2">
                <v-icon
                  icon="mdi-clipboard-list-outline"
                  color="warning"
                  size="small"
                  class="mr-1"
                />
                <span class="fw-bold text-warning">후속 조치 사항</span>
              </div>
              <div
                class="markdown-content bg-transparent"
                v-html="markdownRender(meeting.action_items)"
              ></div>
            </CCallout>
          </CCol>
        </CRow>

        <div v-if="meeting.files.length" class="my-5">
          <h6 class="title mb-3">
            <v-icon icon="mdi-paperclip" color="blue-grey-lighten-1" size="small" class="mr-1" />
            첨부 파일 ({{ meeting.files.length }}건)
          </h6>
          <CRow>
            <FileDisplay
              v-for="file in meeting.files"
              :key="file.pk"
              :file="{
                ...file,
                creator: meeting.attendees_desc.find(u => u.pk === file.creator) || meeting.creator,
              }"
              @delete-file="deleteFile(file.pk)"
            />
          </CRow>
        </div>

        <v-divider class="my-5" />

        <div class="my-4">
          <CRow class="mb-2">
            <CCol>
              <h6 class="title">
                <v-icon
                  icon="mdi-checkbox-marked-circle-outline"
                  color="success"
                  size="small"
                  class="mr-1"
                />
                관련 업무
                {{ meeting.issues?.length ? `(${meeting.issues.length}건)` : '' }}
              </h6>
            </CCol>
            <CCol class="text-right">
              <v-btn
                v-if="canIssueCreate"
                color="info"
                size="x-small"
                @click="refIssueModal.callModal()"
              >
                <v-icon icon="mdi-plus" size="12" class="mr-1" /> 관련 업무 추가
              </v-btn>
            </CCol>
          </CRow>
          <v-divider class="mt-0 mb-3" />

          <div v-if="meeting.issues?.length">
            <CTable small striped hover class="border-bottom">
              <CTableHead>
                <CTableRow class="text-center">
                  <CTableHeaderCell style="width: 10%">번호</CTableHeaderCell>
                  <CTableHeaderCell style="width: 60%">제목</CTableHeaderCell>
                  <CTableHeaderCell style="width: 15%">상태</CTableHeaderCell>
                  <CTableHeaderCell style="width: 15%">담당자</CTableHeaderCell>
                </CTableRow>
              </CTableHead>
              <CTableBody>
                <CTableRow v-for="issue in meeting.issues" :key="issue.pk">
                  <CTableDataCell class="text-center small">
                    {{ issue.pk }}
                  </CTableDataCell>
                  <CTableDataCell>
                    <router-link
                      :to="{
                        name: '(업무) - 보기',
                        params: { projId: issue.project, issueId: issue.pk },
                      }"
                    >
                      {{ issue.subject }}
                    </router-link>
                  </CTableDataCell>
                  <CTableDataCell class="text-center">
                    <v-chip size="x-small" label :color="issue.closed ? 'success' : 'primary'">
                      {{ issue.status }}
                    </v-chip>
                  </CTableDataCell>
                  <CTableDataCell class="text-center small">
                    {{ issue.assigned_to?.username || '-' }}
                  </CTableDataCell>
                </CTableRow>
              </CTableBody>
            </CTable>
          </div>
          <div v-else class="text-muted small p-3 text-center border rounded border-dashed">
            연결된 업무가 없습니다. 우측 상단의 '업무 추가' 버튼을 눌러 새 업무를 등록하세요.
          </div>
        </div>
      </CCardBody>
    </CCard>

    <CRow class="mb-2">
      <CCol class="text-right">
        <v-btn v-if="canMeetingUpdate" color="success" class="ml-2" @click="goEdit"> 수정 </v-btn>
        <v-btn v-if="canMeetingDelete" color="warning" @click="refConfirmModal.callModal()">
          삭제
        </v-btn>
        <v-btn color="light" @click="goList" flat> 목록으로 </v-btn>
      </CCol>
    </CRow>
  </div>

  <ConfirmModal ref="refConfirmModal">
    이 회의록을 정말 삭제하시겠습니까?
    <template #footer>
      <v-btn color="warning" size="small" @click="deleteMeeting">삭제</v-btn>
    </template>
  </ConfirmModal>

  <FormModal ref="refIssueModal" size="xl">
    <template #header>회의 관련 업무 생성</template>
    <template #default>
      <IssueForm
        :issue-project="workStore.issueProject ?? undefined"
        :all-projects="workStore.getAllProjects"
        :status-list="statusList"
        :priority-list="priorityList"
        :get-issues="getIssues"
        :btn-size="'small'"
        @on-submit="createRelatedIssue"
        @close-form="refIssueModal.close()"
      />
    </template>
  </FormModal>
</template>
