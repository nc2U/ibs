<script lang="ts" setup>
import { computed, inject, onBeforeMount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMeeting } from '@/store/pinia/work_meeting.ts'
import { useWork } from '@/store/pinia/work_project.ts'
import { timeFormat } from '@/utils/baseMixins.ts'
import { markdownRender } from '@/utils/helper.ts'
import type { Meeting } from '@/store/types/work_meeting.ts'
import FileDisplay from '@/views/_Work/components/atomics/FileDisplay.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

const route = useRoute()
const router = useRouter()
const meetingStore = useMeeting()
const workStore = useWork()

const meeting = computed(() => meetingStore.meeting)

const statusColor = computed(() => {
  if (meeting.value?.status === '1') return 'primary'
  if (meeting.value?.status === '2') return 'success'
  if (meeting.value?.status === '3') return 'danger'
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
}

const deleteMeeting = async () => {
  if (meeting.value) {
    await meetingStore.deleteMeeting(meeting.value.pk, route.params.projId as string)
    router.push({ name: route.params.projId ? '(회의)' : '회의' })
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

onBeforeMount(() => {
  if (route.params.meetingId) {
    fetchMeeting(Number(route.params.meetingId))
  }
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
    <CRow class="mb-4">
      <CCol>
        <h4>
          <v-icon icon="mdi-account-group" class="mr-2" />
          {{ meeting.title }}
          <v-badge
            :color="statusColor"
            :content="statusText"
            inline
            rounded="1"
            class="ml-2"
          />
        </h4>
      </CCol>
      <CCol class="text-right">
        <v-btn color="info" size="small" variant="outlined" class="mr-2" @click="goEdit">
          수정
        </v-btn>
        <v-btn color="danger" size="small" variant="outlined" @click="refConfirmModal.callModal()">
          삭제
        </v-btn>
      </CCol>
    </CRow>

    <CTable small striped borderless class="mb-4 border-top">
      <CTableBody>
        <CTableRow>
          <CTableHeaderCell style="width: 15%">프로젝트</CTableHeaderCell>
          <CTableDataCell style="width: 35%">
            {{ meeting.project_desc?.name || '회사 본사' }}
          </CTableDataCell>
          <CTableHeaderCell style="width: 15%">회의 일시</CTableHeaderCell>
          <CTableDataCell style="width: 35%">
            {{ meeting.meeting_date ? timeFormat(meeting.meeting_date) : '-' }}
          </CTableDataCell>
        </CTableRow>
        <CTableRow>
          <CTableHeaderCell>카테고리</CTableHeaderCell>
          <CTableDataCell>{{ meeting.category_desc?.name || '-' }}</CTableDataCell>
          <CTableHeaderCell>상태</CTableHeaderCell>
          <CTableDataCell>
            <v-chip :color="statusColor" size="x-small" variant="flat">
              {{ statusText }}
            </v-chip>
          </CTableDataCell>
        </CTableRow>
        <CTableRow>
          <CTableHeaderCell>작성자</CTableHeaderCell>
          <CTableDataCell>{{ meeting.creator.username }}</CTableDataCell>
          <CTableHeaderCell></CTableHeaderCell>
          <CTableDataCell></CTableDataCell>
        </CTableRow>
        <CTableRow>
          <CTableHeaderCell>참석자</CTableHeaderCell>
          <CTableDataCell colspan="3">
            <v-chip
              v-for="user in meeting.attendees_desc"
              :key="user.pk"
              size="x-small"
              color="primary"
              class="mr-1"
            >
              {{ user.username }}
            </v-chip>
            <span v-if="meeting.other_attendees" class="text-muted ml-2">
              (기타: {{ meeting.other_attendees }})
            </span>
          </CTableDataCell>
        </CTableRow>
      </CTableBody>
    </CTable>

    <div v-if="meeting.agenda" class="mb-4 p-3 border rounded bg-light">
      <h6 class="text-primary mb-2">
        <v-icon icon="mdi-bullseye-arrow" size="small" /> 회의 아젠다
      </h6>
      <div v-html="markdownRender(meeting.agenda)" class="markdown-body" />
    </div>

    <div v-if="meeting.content" class="mb-4 p-3 border rounded">
      <h6 class="text-primary mb-2"><v-icon icon="mdi-text-box-outline" size="small" /> 회의 내용</h6>
      <div v-html="markdownRender(meeting.content)" class="markdown-body" />
    </div>

    <div v-if="meeting.decisions" class="mb-4 p-3 border rounded border-success bg-light-success">
      <h6 class="text-success mb-2"><v-icon icon="mdi-check-circle" size="small" /> 주요 결정 사항</h6>
      <div v-html="markdownRender(meeting.decisions)" class="markdown-body text-success" />
    </div>

    <div v-if="meeting.action_items" class="mb-4 p-3 border rounded border-warning">
      <h6 class="text-warning mb-2">
        <v-icon icon="mdi-clipboard-list-outline" size="small" /> 후속 조치 사항
      </h6>
      <div v-html="markdownRender(meeting.action_items)" class="markdown-body text-warning" />
    </div>

    <div v-if="meeting.files.length" class="mb-4">
      <h6 class="mb-2"><v-icon icon="mdi-paperclip" size="small" /> 첨부 파일</h6>
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
  </div>

  <ConfirmModal ref="refConfirmModal">
    이 회의록을 정말 삭제하시겠습니까?
    <template #footer>
      <v-btn color="danger" size="small" @click="deleteMeeting">삭제</v-btn>
    </template>
  </ConfirmModal>
</template>

<style scoped>
.markdown-body {
  word-break: break-all;
}
.bg-light-success {
  background-color: #f0fdf4;
}
</style>
