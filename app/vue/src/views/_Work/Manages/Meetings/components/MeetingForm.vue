<script lang="ts" setup>
import { computed, inject, onBeforeMount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAccount } from '@/store/pinia/account'
import { useWork } from '@/store/pinia/work_project.ts'
import { useMeeting } from '@/store/pinia/work_meeting.ts'
import { timeFormat } from '@/utils/baseMixins.ts'
import { isValidate, message } from '@/utils/helper.ts'
import DatePicker from '@/components/DatePicker/DatePicker.vue'

const route = useRoute()
const router = useRouter()
const accStore = useAccount()
const workStore = useWork()
const meetingStore = useMeeting()

const meeting = computed(() => meetingStore.meeting)
const issueProjects = computed(() => workStore.issueProjectList)
const users = computed(() => accStore.usersList)
const categories = computed(() => meetingStore.categoryList)

const validated = ref(false)
const form = ref({
  pk: null as number | null,
  project: null as number | null,
  company: 1, // Default company
  category: null as number | null,
  title: '',
  agenda: '',
  content: '',
  decisions: '',
  action_items: '',
  meeting_date: timeFormat(new Date()),
  attendees: [] as number[],
  other_attendees: '',
})

const newFiles = ref<{ file: File; description: string }[]>([])

const loadFile = (event: Event) => {
  const el = event.target as HTMLInputElement
  if (el.files) {
    for (let i = 0; i < el.files.length; i++) {
      newFiles.value.push({ file: el.files[i], description: '' })
    }
  }
}

const removeFile = (index: number) => {
  newFiles.value.splice(index, 1)
}

const onSubmit = (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
  } else {
    const payload = { ...form.value, newFiles: newFiles.value }
    if (form.value.pk) {
      meetingStore.updateMeeting(payload as any)
    } else {
      meetingStore.createMeeting(payload as any)
    }
    router.back()
  }
}

const fetchMeeting = async (pk: number) => {
  await meetingStore.fetchMeeting(pk)
  if (meeting.value) {
    form.value = {
      pk: meeting.value.pk,
      project: meeting.value.project,
      company: meeting.value.company,
      category: meeting.value.category,
      title: meeting.value.title,
      agenda: meeting.value.agenda,
      content: meeting.value.content,
      decisions: meeting.value.decisions,
      action_items: meeting.value.action_items,
      meeting_date: meeting.value.meeting_date ? timeFormat(meeting.value.meeting_date) : '',
      attendees: meeting.value.attendees,
      other_attendees: meeting.value.other_attendees,
    }
  }
}

onBeforeMount(async () => {
  await accStore.fetchUsersList()
  await workStore.fetchIssueProjectList({})
  if (route.params.projId) {
    const proj = workStore.issueProjectList.find(p => p.slug === route.params.projId)
    if (proj) form.value.project = proj.pk as number
    await meetingStore.fetchCategoryList(route.params.projId as string)
  } else {
    await meetingStore.fetchCategoryList()
  }

  if (route.params.meetingId) {
    await fetchMeeting(Number(route.params.meetingId))
  }
})

const userOptions = computed(() =>
  users.value.map(u => ({
    value: u.pk,
    title: u.username,
  })),
)
</script>

<template>
  <CForm
    class="needs-validation p-3"
    novalidate
    :validated="validated"
    @submit.prevent="onSubmit"
  >
    <CRow class="mb-3">
      <CCol>
        <h4>
          <v-icon icon="mdi-account-group" class="mr-2" />
          회의록 {{ form.pk ? '수정' : '작성' }}
        </h4>
      </CCol>
    </CRow>

    <CRow class="mb-3">
      <CCol md="6">
        <CFormLabel for="project">프로젝트</CFormLabel>
        <CFormSelect v-model="form.project" id="project" :disabled="!!route.params.projId">
          <option :value="null">회사 본사</option>
          <option v-for="proj in issueProjects" :key="proj.pk" :value="proj.pk">
            {{ proj.name }}
          </option>
        </CFormSelect>
      </CCol>
      <CCol md="6">
        <CFormLabel for="meeting_date">회의 일시</CFormLabel>
        <DatePicker v-model="form.meeting_date" id="meeting_date" placeholder="회의 일시 선택" />
      </CCol>
    </CRow>

    <CRow class="mb-3">
      <CCol md="6">
        <CFormLabel for="category">카테고리</CFormLabel>
        <CFormSelect v-model="form.category" id="category">
          <option :value="null">---------</option>
          <option v-for="cat in categories" :key="cat.pk" :value="cat.pk">
            {{ cat.name }}
          </option>
        </CFormSelect>
      </CCol>
      <CCol md="6">
        <CFormLabel for="title">회의 제목</CFormLabel>
        <CFormInput v-model="form.title" id="title" required placeholder="회의 제목을 입력하세요" />
        <CFormFeedback invalid>제목을 입력해 주세요.</CFormFeedback>
      </CCol>
    </CRow>

    <CRow class="mb-3">
      <CCol md="12">
        <CFormLabel>참석자 (내부 구성원)</CFormLabel>
        <v-select
          v-model="form.attendees"
          :items="userOptions"
          multiple
          chips
          closable-chips
          density="compact"
          variant="outlined"
          placeholder="참석자를 선택하세요"
        />
      </CCol>
    </CRow>

    <CRow class="mb-3">
      <CCol md="12">
        <CFormLabel for="other_attendees">기타 참석자 (외부 인원)</CFormLabel>
        <CFormInput
          v-model="form.other_attendees"
          id="other_attendees"
          placeholder="외부 참석자 이름을 입력하세요 (쉼표로 구분)"
        />
      </CCol>
    </CRow>

    <CRow class="mb-3">
      <CCol>
        <CFormLabel for="agenda">회의 아젠다</CFormLabel>
        <CFormTextarea v-model="form.agenda" id="agenda" rows="3" placeholder="논의할 주요 의제" />
      </CCol>
    </CRow>

    <CRow class="mb-3">
      <CCol>
        <CFormLabel for="content">회의 내용</CFormLabel>
        <CFormTextarea v-model="form.content" id="content" rows="6" placeholder="회의 진행 내용" />
      </CCol>
    </CRow>

    <CRow class="mb-3">
      <CCol md="6">
        <CFormLabel for="decisions">주요 결정 사항</CFormLabel>
        <CFormTextarea
          v-model="form.decisions"
          id="decisions"
          rows="4"
          placeholder="확정된 합의 내용"
        />
      </CCol>
      <CCol md="6">
        <CFormLabel for="action_items">후속 조치 사항</CFormLabel>
        <CFormTextarea
          v-model="form.action_items"
          id="action_items"
          rows="4"
          placeholder="누가, 언제까지, 무엇을 할 것인가?"
        />
      </CCol>
    </CRow>

    <CRow class="mb-4">
      <CCol>
        <CFormLabel>첨부 파일</CFormLabel>
        <CFormInput type="file" multiple @change="loadFile" />
        <div v-if="newFiles.length" class="mt-2">
          <CBadge
            v-for="(f, i) in newFiles"
            :key="i"
            color="secondary"
            class="mr-2 mb-2 p-2"
            style="cursor: pointer"
            @click="removeFile(i)"
          >
            {{ f.file.name }} <v-icon icon="mdi-close" size="12" />
          </CBadge>
        </div>
      </CCol>
    </CRow>

    <CRow>
      <CCol class="text-right">
        <v-btn color="grey-lighten-1" class="mr-2" @click="router.back()">취소</v-btn>
        <v-btn type="submit" color="primary">{{ form.pk ? '수정' : '저장' }}</v-btn>
      </CCol>
    </CRow>
  </CForm>
</template>
