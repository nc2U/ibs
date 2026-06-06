<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMeeting } from '@/store/pinia/work_meeting.ts'
import { useWork } from '@/store/pinia/work_project.ts'
import { useIssue } from '@/store/pinia/work_issue.ts'
import { elapsedTime, timeFormat } from '@/utils/baseMixins.ts'
import { markdownRender } from '@/utils/helper.ts'
import FileDisplay from '@/views/_Work/components/atomics/FileDisplay.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import FormModal from '@/components/Modals/FormModal.vue'
import IssueForm from '@/views/_Work/Manages/Issues/components/IssueForm.vue'

const route = useRoute()
const router = useRouter()
const meetingStore = useMeeting()
const workStore = useWork()
const issueStore = useIssue()

const meeting = computed(() => meetingStore.meeting)

const statusList = computed(() => issueStore.statusList)
const priorityList = computed(() => issueStore.priorityList)
const getIssues = computed(() => issueStore.getIssues)

const statusColor = computed(() => {
  if (meeting.value?.status === '1') return 'info'
  if (meeting.value?.status === '2') return 'success'
  if (meeting.value?.status === '3') return 'secondary'
  return 'secondary'
})

const statusText = computed(() => {
  if (meeting.value?.status === '1') return '준비중'
  if (meeting.value?.status === '2') return '완료됨'
  if (meeting.value?.status === '3') return '취소됨'
  return '-'
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
    await meetingStore.deleteMeeting(meeting.value.pk, route.params.projId as string)
    await router.push({ name: route.params.projId ? '(회의)' : '회의' })
  }
}

const goList = () => {
  if (route.params.projId) {
    router.push({ name: '(회의)', params: { projId: route.params.projId } })
  } else {
    router.push({ name: '회의' })
  }
}

const goEdit = () => {
  if (route.params.projId) {
    router.push({
      name: '(회의) - 수정',
      params: { projId: route.params.projId, meetingId: route.params.meetingId },
    })
  } else {
    router.push({
      name: '회의 - 수정',
      params: { meetingId: route.params.meetingId },
    })
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
          <v-badge :color="statusColor" :content="statusText" inline rounded="1" class="ml-2" />
        </h5>
      </CCol>
      <CCol class="text-right">
        <v-btn color="info" size="small" variant="outlined" class="mr-2" @click="goEdit">
          수정
        </v-btn>
        <v-btn
          color="danger"
          size="small"
          variant="outlined"
          class="mr-2"
          @click="refConfirmModal.callModal()"
        >
          삭제
        </v-btn>
        <v-btn color="secondary" size="small" variant="outlined" @click="goList"> 목록으로 </v-btn>
      </CCol>
    </CRow>

    <CCard color="yellow-lighten-5" class="mb-4 shadow-sm">
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
                  {{ statusText }}
                </v-chip>
              </CCol>
            </CRow>
          </CCol>

          <CCol md="6">
            <CRow class="mb-2">
              <CCol class="title" sm="4">회의 일시 :</CCol>
              <CCol sm="8">
                {{ meeting.meeting_date ? timeFormat(meeting.meeting_date) : '-' }}
              </CCol>
            </CRow>
            <CRow class="mb-2">
              <CCol class="title" sm="4">참석자 :</CCol>
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
          </CCol>
        </CRow>

        <v-divider class="my-4" />

        <div v-if="meeting.agenda" class="mb-5">
          <h6 class="title mb-2 text-black">
            <v-icon icon="mdi-bullseye-arrow" color="text-primary" size="small" class="mr-1" /> 회의
            아젠다
          </h6>
          <div
            class="markdown-content bg-white p-3 border rounded"
            v-html="markdownRender(meeting.agenda)"
          />
        </div>

        <div v-if="meeting.content" class="mb-5">
          <h6 class="title mb-2 text-black">
            <v-icon icon="mdi-text-box-outline" color="text-primary" size="small" class="mr-1" />
            회의 내용
          </h6>
          <div
            class="markdown-content bg-white p-3 border rounded"
            v-html="markdownRender(meeting.content)"
          />
        </div>

        <CRow>
          <CCol md="6" v-if="meeting.decisions">
            <div class="mb-4">
              <h6 class="title mb-2 text-black">
                <v-icon color="text-success" icon="mdi-check-circle" size="small" class="mr-1" />
                주요 결정 사항
              </h6>
              <div
                class="markdown-content bg-light-success p-3 border border-success rounded text-success"
                v-html="markdownRender(meeting.decisions)"
              />
            </div>
          </CCol>
          <CCol md="6" v-if="meeting.action_items">
            <div class="mb-4">
              <h6 class="title mb-2 text-black">
                <v-icon
                  icon="mdi-clipboard-list-outline"
                  color="text-warning"
                  size="small"
                  class="mr-1"
                />
                후속 조치 사항
              </h6>
              <div
                class="markdown-content bg-light-warning p-3 border border-warning rounded text-warning"
                v-html="markdownRender(meeting.action_items)"
              />
            </div>
          </CCol>
        </CRow>

        <div class="mb-5">
          <CRow class="mb-2">
            <CCol>
              <h6 class="title text-black">
                <v-icon
                  icon="mdi-checkbox-marked-circle-outline"
                  color="success"
                  size="small"
                  class="mr-1"
                />
                관련 업무
              </h6>
            </CCol>
            <CCol class="text-right">
              <v-btn color="info" size="x-small" @click="refIssueModal.callModal()">
                <v-icon icon="mdi-plus" size="12" class="mr-1" /> 관련 업무 추가
              </v-btn>
            </CCol>
          </CRow>
          <v-divider class="mt-0 mb-3" />

          <div v-if="meeting.issues?.length">
            <CTable small striped hover class="border-bottom">
              <CTableHead>
                <CTableRow class="text-center bg-light">
                  <CTableHeaderCell style="width: 10%">번호</CTableHeaderCell>
                  <CTableHeaderCell style="width: 60%">제목</CTableHeaderCell>
                  <CTableHeaderCell style="width: 15%">상태</CTableHeaderCell>
                  <CTableHeaderCell style="width: 15%">담당자</CTableHeaderCell>
                </CTableRow>
              </CTableHead>
              <CTableBody>
                <CTableRow v-for="issue in meeting.issues" :key="issue.pk">
                  <CTableDataCell class="text-center small">{{ issue.pk }}</CTableDataCell>
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
                    <v-chip size="x-small" label :color="issue.closed ? 'success' : 'primary'">{{
                      issue.status
                    }}</v-chip>
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

        <v-divider v-if="meeting.files.length" class="my-4" />

        <div v-if="meeting.files.length">
          <h6 class="title mb-3">
            <v-icon icon="mdi-paperclip" size="small" class="mr-1" /> 첨부 파일
          </h6>
          <CRow>
            <FileDisplay
              v-for="file in meeting.files"
              :key="file.pk"
              :file="{
                ...file,
                creator: meeting.attendees_desc.find(u => u.pk === file.creator) || meeting.creator,
              }"
            />
          </CRow>
        </div>
      </CCardBody>
    </CCard>
  </div>

  <ConfirmModal ref="refConfirmModal">
    이 회의록을 정말 삭제하시겠습니까?
    <template #footer>
      <v-btn color="danger" size="small" @click="deleteMeeting">삭제</v-btn>
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

<style lang="scss" scoped>
.title {
  font-weight: bold;
}
.sub-title {
  font-size: 1.25rem;
  font-weight: bold;
  color: #0f192a;
}
.markdown-content {
  line-height: 1.6;
  :deep(p) {
    margin-bottom: 0.5rem;
  }
  :deep(ul),
  :deep(ol) {
    padding-left: 1.5rem;
    margin-bottom: 0.5rem;
  }
  :deep(pre) {
    background-color: #f1f5f9;
    padding: 0.75rem;
    border-radius: 4px;
  }
}
.bg-light-success {
  background-color: #f0fdf4 !important;
}
.bg-light-warning {
  background-color: #fffbeb !important;
}
.border-dashed {
  border-style: dashed !important;
}
</style>
