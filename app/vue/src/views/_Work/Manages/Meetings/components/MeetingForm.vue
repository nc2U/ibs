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
import type { Meeting } from '@/store/types/work_meeting.ts'
import type { IssueProject } from '@/store/types/work_project.ts'
import MdEditor from '@/components/MdEditor/Index.vue'
import FormModal from '@/components/Modals/FormModal.vue'
import DateTimePicker from '@/components/DatePicker/DateTimePicker.vue'
import IssueForm from '@/views/_Work/Manages/Issues/components/IssueForm.vue'
import IssueProjectSelector from '@/views/_Work/components/atomics/IssueProjectSelector.vue'

const route = useRoute()
const router = useRouter()
const accStore = useAccount()
const workStore = useWork()
const meetingStore = useMeeting()
const issueStore = useIssue()

const meeting = computed<Meeting | null>(() => meetingStore.meeting)
const myProjects = computed(() => workStore.getMyProjects)
const meetingProjects = computed(() => workStore.getMyProjects.filter(pjt => pjt.module?.meeting))
const users = computed(() => accStore.usersList)
const categories = computed(() => meetingStore.categoryList)

const statusList = computed(() => issueStore.statusList)
const priorityList = computed(() => issueStore.priorityList)
const getIssues = computed(() => issueStore.getIssues)

const validated = ref(false)
const form = ref({
  pk: null as number | null,
  project: null as number | null,
  category: null as number | null,
  status: '1' as '1' | '2' | '3',
  is_confirmed: false,
  title: '',
  agenda: '',
  content: '',
  decisions: '',
  action_items: '',
  meeting_date: timeFormat(new Date(), 'min'),
  location: '',
  attendees: [] as number[],
  other_attendees: '',
  links: [] as any[],
})

export interface InlineActionItem {
  id: string
  subject: string
  assigned_to: number | null
  due_date: string
  priority: number | null
}

const pendingActionItems = ref<InlineActionItem[]>([])

const addPendingActionItem = (
  subject = '',
  assigned_to: number | null = null,
  due_date = '',
  priority: number | null = null,
) => {
  const defaultPriority =
    priority ??
    (priorityList.value.find(p => p.name === '보통' || p.name === 'Normal')?.pk ||
      priorityList.value[0]?.pk ||
      null)
  pendingActionItems.value.push({
    id: `item-${Date.now()}-${Math.random().toString(36).substr(2, 6)}`,
    subject,
    assigned_to: assigned_to ?? (accStore.userInfo?.pk || null),
    due_date,
    priority: defaultPriority,
  })
}

const removePendingActionItem = (index: number) => {
  pendingActionItems.value.splice(index, 1)
}

const parseActionItemsFromText = () => {
  if (!form.value.action_items || !form.value.action_items.trim()) return

  const lines = form.value.action_items.split('\n')
  const newItems: InlineActionItem[] = []

  const userMapByName = new Map<string, number>()
  users.value.forEach(u => {
    if (u.pk !== undefined) {
      userMapByName.set(u.username.toLowerCase(), u.pk)
      if (u.profile?.name) {
        userMapByName.set(u.profile.name.toLowerCase(), u.pk)
      }
    }
  })

  const defaultPriority =
    priorityList.value.find(p => p.name === '보통' || p.name === 'Normal')?.pk ||
    priorityList.value[0]?.pk ||
    null

  lines.forEach(line => {
    let text = line.trim()
    if (!text) return

    // Strip markdown bullets / numbers
    text = text.replace(/^[-*+]\s*(\[[ xX]\])?\s*/, '')
    text = text.replace(/^\d+[\.\)]\s*/, '')
    text = text.trim()
    if (!text) return

    let assignedTo: number | null = null
    let dueDate = ''

    // 1. Assignee pattern: (담당: 홍길동), (담당자: 홍길동), @홍길동
    const assigneeMatch =
      text.match(/\((?:담당(?:자)?|담당자명)\s*:\s*([^/,\)]+)\)/i) ||
      text.match(/@([a-zA-Z0-9가-힣]+)/)
    if (assigneeMatch) {
      const name = assigneeMatch[1].trim()
      const foundPk = userMapByName.get(name.toLowerCase())
      if (foundPk) assignedTo = foundPk
    }

    // 2. Due date pattern: (기한: 2026-09-15), 2026-09-15, 2026.09.15
    const dateMatch =
      text.match(/(?:기한|마감|완료|일자)\s*:\s*(\d{4}[-.]\d{2}[-.]\d{2})/i) ||
      text.match(/(\d{4}[-.]\d{2}[-.]\d{2})/)
    if (dateMatch) {
      dueDate = dateMatch[1].replace(/\./g, '-')
    }

    // Clean subject
    let cleanSubject = text
      .replace(/\((?:담당(?:자)?|기한|마감|완료|일자)[^)]*\)/gi, '')
      .replace(/@([a-zA-Z0-9가-힣]+)/g, '')
      .trim()
      .replace(/^[-,:\s]+|[-,:\s]+$/g, '')

    if (cleanSubject) {
      const alreadyExists = pendingActionItems.value.some(
        item => item.subject.toLowerCase() === cleanSubject.toLowerCase(),
      )
      if (!alreadyExists) {
        newItems.push({
          id: `item-${Date.now()}-${Math.random().toString(36).substr(2, 6)}`,
          subject: cleanSubject,
          assigned_to: assignedTo,
          due_date: dueDate,
          priority: defaultPriority,
        })
      }
    }
  })

  if (newItems.length > 0) {
    pendingActionItems.value.push(...newItems)
  }
}

const { can, PERM } = usePerms()
const canIssueRead = computed(() => can(PERM.ISSUE_READ))
const canIssueCreate = computed(() => can(PERM.ISSUE_CREATE))
const canIssueUpdate = computed(() => can(PERM.ISSUE_UPDATE))

const canMeetingCreate = computed(() => can(PERM.MEETING_CREATE))
const canMeetingUpdate = computed(() => can(PERM.MEETING_UPDATE))
const canMeetingConfirm = computed(() => can(PERM.MEETING_CONFIRM))

const MAX_FILE_SIZE = 100 * 1024 * 1024 // 단일 파일 최대 100MB
const MAX_TOTAL_SIZE = 100 * 1024 * 1024 // 전체 첨부파일 합계 최대 100MB

const fileErrorMessage = ref('')
const fileInput = ref<HTMLInputElement | null>(null)
const newFiles = ref<{ file: File; description: string }[]>([])
const newLinks = ref<{ link: string; name: string }[]>([])
const files_del = ref<string[]>([])

const totalFileSize = computed(() => {
  return newFiles.value.reduce((acc, item) => acc + (item.file?.size || 0), 0)
})

const formatBytes = (bytes: number, decimals = 1) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
}

const loadFile = (event: Event, index?: number) => {
  const el = event.target as HTMLInputElement
  fileErrorMessage.value = ''

  if (el.files && el.files.length > 0) {
    const selectedFiles = Array.from(el.files)

    // 1. 단일 파일 용량 체크
    const overSizedFile = selectedFiles.find(file => file.size > MAX_FILE_SIZE)
    if (overSizedFile) {
      fileErrorMessage.value = `[${overSizedFile.name}] 파일 크기가 제한(${formatBytes(MAX_FILE_SIZE)})을 초과합니다.`
      el.value = ''
      return
    }

    // 2. 전체 총용량 체크
    const currentTotal =
      index !== undefined
        ? newFiles.value.reduce(
            (acc, item, idx) => acc + (idx === index ? 0 : item.file?.size || 0),
            0,
          )
        : totalFileSize.value

    const addedTotal = selectedFiles.reduce((sum, f) => sum + f.size, 0)
    if (currentTotal + addedTotal > MAX_TOTAL_SIZE) {
      fileErrorMessage.value = `총 첨부파일 용량이 제한(${formatBytes(MAX_TOTAL_SIZE)})을 초과하여 추가할 수 없습니다.`
      el.value = ''
      return
    }

    if (index !== undefined && newFiles.value[index]) {
      newFiles.value[index].file = selectedFiles[0]
    } else {
      newFiles.value.push(...selectedFiles.map(file => ({ file, description: '' })))
    }
  }
}

const removeFile = (index: number) => {
  newFiles.value.splice(index, 1)
  fileErrorMessage.value = ''
}

const addLink = () => {
  newLinks.value.push({ link: '', name: '' })
}

const removeLink = (index: number) => {
  newLinks.value.splice(index, 1)
}

const isSubmitting = ref(false)

const onSubmit = async (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
  } else {
    isSubmitting.value = true
    try {
      const formData = new FormData()

      // Ensure project is bound
      if (!form.value.project) {
        if (projId.value) {
          const found = meetingProjects.value.find(p => p.slug === projId.value)
          if (found) form.value.project = found.value as number
        } else if (meetingProjects.value.length > 0) {
          form.value.project = meetingProjects.value[0].value as number
        }
      }

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

      // Append existing links status (del / updates)
      form.value.links?.forEach(l => {
        formData.append('links', JSON.stringify(l))
      })

      // Append new links
      newLinks.value.forEach(l => {
        if (l.link && l.link.trim()) {
          formData.append('newLinks', l.link.trim())
          formData.append('newLinkNames', l.name)
        }
      })

      let meetingPk = form.value.pk
      let targetSlug = projId.value

      if (meetingPk) {
        const updated = await meetingStore.updateMeeting(meetingPk, formData as any)
        if (updated?.project_desc?.slug) targetSlug = updated.project_desc.slug
      } else {
        const created = await meetingStore.createMeeting(formData as any)
        if (created && created.pk) {
          meetingPk = created.pk
          if (created.project_desc?.slug) targetSlug = created.project_desc.slug
        }
      }

      // Process pending inline action items
      if (meetingPk && pendingActionItems.value.length > 0) {
        const projectVal =
          form.value.project ||
          (workStore.currentProject as IssueProject)?.slug ||
          targetSlug ||
          ''

        for (const item of pendingActionItems.value) {
          if (!item.subject?.trim()) continue
          const issueData = new FormData()
          issueData.append('subject', item.subject.trim())
          issueData.append('meeting', meetingPk.toString())
          if (projectVal) issueData.append('project', projectVal.toString())
          if (item.assigned_to) issueData.append('assigned_to', item.assigned_to.toString())
          if (item.due_date) issueData.append('due_date', item.due_date)
          if (item.priority) issueData.append('priority', item.priority.toString())
          await issueStore.createIssue(issueData)
        }
        pendingActionItems.value = []
      }

      if (targetSlug && meetingPk) {
        router.push({
          name: '(회의) - 보기',
          params: { projId: targetSlug, meetingId: meetingPk },
        })
      } else {
        router.back()
      }
    } finally {
      isSubmitting.value = false
    }
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

      if (key === 'watchers' || key === 'files' || key === 'links')
        val?.forEach((v: any) => formData.append(key, JSON.stringify(v)))
      else if (key === 'newFiles') {
        val.forEach((v: any) => {
          formData.append('new_files', v.file as string | Blob)
          formData.append('descriptions', v.description ?? '')
        })
      } else if (key === 'newLinks') {
        val.forEach((v: any) => {
          if (v.link && v.link.trim()) {
            formData.append('newLinks', v.link.trim())
            formData.append('newLinkNames', v.name ?? '')
          }
        })
      } else {
        if (key === 'project' && !val) {
          const projectSlug = (workStore.currentProject as IssueProject)?.slug || ''
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
      location: meeting.value.location ?? '',
      attendees: meeting.value.attendees,
      other_attendees: meeting.value.other_attendees,
      links: meeting.value.links ? JSON.parse(JSON.stringify(meeting.value.links)) : [],
    }
    if (meeting.value.project_desc)
      await issueStore.fetchAllIssueList(meeting.value.project_desc.slug)
  }
}

watch(
  () => form.value.project,
  async newProjPk => {
    if (newProjPk) {
      const proj = meetingProjects.value.find(p => p.value === newProjPk)
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

interface MeetingTemplate {
  name: string
  titlePrefix: string
  agenda: string
  actionItems: string
}

const meetingTemplates: MeetingTemplate[] = [
  {
    name: '주간 업무/공정',
    titlePrefix: '[주간업무] ',
    agenda: '1. 전주 실적 점검 및 이슈 공유\n2. 금주 주요 추진 계획\n3. 부서/파트 간 협조 요청 사항',
    actionItems: '- [ ] 조치 1 (담당: / 기한: )\n- [ ] 조치 2 (담당: / 기한: )',
  },
  {
    name: '설계/인허가 협의',
    titlePrefix: '[인허가협의] ',
    agenda: '1. 인허가 진행 현황 점검\n2. 설계 변경 요건 및 관련 법규 검토\n3. 관공서 보완 요청 조치 방안',
    actionItems: '- [ ] 보완 도서 및 서류 제출 (담당: / 기한: )\n- [ ] 유관 부서/기관 협의 (담당: / 기한: )',
  },
  {
    name: '시공/품질/안전 점검',
    titlePrefix: '[안전품질] ',
    agenda: '1. 안전 점검 결과 및 지적 사항 공유\n2. 품질 시험 및 감리 지적 조치 계획\n3. 위험 공종 작업 계획 심의',
    actionItems: '- [ ] 안전 위험 요소 시정 조치 및 사진 보고 (담당: / 기한: )\n- [ ] 자재 시험 성적서 확인 (담당: / 기한: )',
  },
  {
    name: '사업비/예산 심의',
    titlePrefix: '[예산심의] ',
    agenda: '1. 사업비 집행 실적 분석\n2. 신규 발주/계약 품의 검토\n3. 자금 흐름(Cash Flow) 점검 및 자금 조달안',
    actionItems: '- [ ] 기안/품의서 상신 (담당: / 기한: )\n- [ ] 정산 보고서 작성 (담당: / 기한: )',
  },
]

const applyMeetingTemplate = (tmpl: MeetingTemplate) => {
  const dateStr = new Date().toLocaleDateString('ko-KR', { month: 'numeric', day: 'numeric' })
  if (!form.value.title || form.value.title.startsWith('[')) {
    form.value.title = `${tmpl.titlePrefix}${dateStr} 회의`
  }
  if (!form.value.agenda) {
    form.value.agenda = tmpl.agenda
  }
  if (!form.value.action_items) {
    form.value.action_items = tmpl.actionItems
  }
}

const projId = computed(() => route.params.projId as string | undefined)
watch(projId, newVal => {
  if (newVal)
    form.value.project = meetingProjects.value.find(p => p.slug === newVal)?.value as number
})

watch(
  meetingProjects,
  projects => {
    if (!form.value.project && projects.length > 0) {
      const target = projId.value
        ? projects.find(p => p.slug === projId.value)
        : projects.find(p => p.slug === workStore.currentProject?.slug) || projects[0]
      if (target) form.value.project = target.value as number
    }
  },
  { immediate: true },
)

onBeforeMount(async () => {
  await accStore.fetchUsersList()
  await workStore.fetchAllProjectList()
  await issueStore.fetchStatusList()
  await issueStore.fetchPriorityList()
  await issueStore.fetchTrackerList()
  if (projId.value) {
    const proj = meetingProjects.value.find(p => p.slug === projId.value)
    if (proj) {
      form.value.project = proj.value as number
      await issueStore.fetchAllIssueList(proj.slug)
    }
    await meetingStore.fetchCategoryList(projId.value as string)
  } else {
    if (!form.value.project && meetingProjects.value.length > 0) {
      const current = meetingProjects.value.find(p => p.slug === workStore.currentProject?.slug)
      form.value.project = current ? (current.value as number) : (meetingProjects.value[0]?.value as number)
    }
    await meetingStore.fetchCategoryList()
  }

  if (route.params.meetingId) await fetchMeeting(Number(route.params.meetingId))
})
</script>

<template>
  <CCard>
    <CCardHeader>{{ !form?.pk ? '새 회의록' : '회의록 수정' }}</CCardHeader>
    <CCardBody>
      <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="onSubmit">
        <CRow class="mb-3">
          <!-- Main Content Column -->
          <CCol md="8">
            <!-- Quick Meeting Template Banner -->
            <CRow v-if="!form.pk" class="mb-3">
              <CFormLabel class="col-sm-2 col-form-label text-right pt-0">
                <span class="text-primary font-weight-bold">회의 템플릿</span>
              </CFormLabel>
              <CCol sm="10">
                <div class="p-2 border rounded bg-light d-flex flex-wrap align-items-center">
                  <span class="text-muted small mr-2">
                    <v-icon icon="mdi-magic-staff" size="14" color="primary" class="mr-1" />
                    자주 쓰는 양식 자동 채우기:
                  </span>
                  <v-chip
                    v-for="tmpl in meetingTemplates"
                    :key="tmpl.name"
                    size="small"
                    variant="elevated"
                    color="primary"
                    class="mr-2 my-1 cursor-pointer"
                    @click="applyMeetingTemplate(tmpl)"
                  >
                    {{ tmpl.name }}
                  </v-chip>
                </div>
              </CCol>
            </CRow>

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

            <!-- File Upload Section -->
            <CRow class="mb-0">
              <CFormLabel class="col-sm-2 col-form-label text-right">파일</CFormLabel>
              <CCol sm="10">
                <div
                  class="d-flex align-items-center justify-content-between text-muted small mb-2"
                >
                  <span>
                    <v-icon icon="mdi-paperclip" size="14" class="mr-1" />
                    첨부파일 용량 (최대 {{ formatBytes(MAX_TOTAL_SIZE) }})
                  </span>
                  <span :class="{ 'text-danger font-weight-bold': totalFileSize > MAX_TOTAL_SIZE }">
                    {{ formatBytes(totalFileSize) }} / {{ formatBytes(MAX_TOTAL_SIZE) }}
                  </span>
                </div>

                <div v-if="fileErrorMessage" class="text-danger small mb-2">
                  <v-icon icon="mdi-alert-circle" size="14" class="mr-1" />
                  {{ fileErrorMessage }}
                  <span class="ml-2 font-weight-bold text-body">
                    💡 대용량 파일은 아래 [외부 클라우드 링크] 섹션에 공유 링크(OneDrive, Google
                    Drive 등)를 직접 추가하여 공유할 수 있습니다.
                  </span>
                </div>

                <div v-if="meeting?.files?.length" class="mb-2">
                  <CTable small striped hover>
                    <CTableBody>
                      <CTableRow v-for="(file, index) in meeting.files" :key="file.pk">
                        <CTableDataCell class="cursor-not-allowed">
                          {{ file.file_name }} ({{ formatBytes(file.file_size || 0) }})
                          <CFormCheck
                            label="삭제"
                            v-model="files_del"
                            :value="`${file.pk}`"
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
                  v-else-if="!newFiles.length"
                  class="text-muted small p-2 text-center border rounded border-dashed mb-2"
                >
                  등록된 파일이 없습니다.
                </div>
              </CCol>
            </CRow>

            <CRow v-for="(f, i) in newFiles" :key="i" class="mb-2">
              <CFormLabel :for="`file-${i + 1}`" class="col-sm-2 col-form-label text-right">
              </CFormLabel>
              <CCol sm="5">
                <CFormInput type="text" :value="f.file.name" disabled />
                <div class="text-muted extra-small mt-1">용량: {{ formatBytes(f.file.size) }}</div>
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
                <v-btn
                  color="info"
                  size="x-small"
                  @click="(fileInput as HTMLInputElement)?.click()"
                >
                  <v-icon icon="mdi-paperclip" size="small" class="mr-1" />
                  첨부 파일 추가
                </v-btn>
              </CCol>
            </CRow>

            <!-- 외부 클라우드 링크 섹션 -->
            <CRow class="mb-2">
              <CFormLabel class="col-sm-2 col-form-label text-right">외부 링크</CFormLabel>
              <CCol sm="10">
                <div v-if="form.links?.length" class="mb-2">
                  <CTable small striped hover>
                    <CTableBody>
                      <CTableRow v-for="(linkItem, index) in form.links" :key="linkItem.pk">
                        <CTableDataCell>
                          <a :href="linkItem.link" target="_blank" rel="noopener noreferrer">
                            <v-icon icon="mdi-link-variant" size="14" class="mr-1" />
                            {{ linkItem.name ? linkItem.name : linkItem.link }}
                          </a>
                          <CFormCheck
                            label="삭제"
                            v-model="linkItem.del"
                            inline
                            class="ml-2"
                            :id="`meeting-link-del-${index}`"
                          />
                        </CTableDataCell>
                      </CTableRow>
                    </CTableBody>
                  </CTable>
                </div>
              </CCol>
            </CRow>

            <CRow v-for="(l, i) in newLinks" :key="`link-${i}`" class="mb-2">
              <CFormLabel :for="`link-${i}`" class="col-sm-2 col-form-label text-right">
              </CFormLabel>
              <CCol sm="5">
                <CFormInput
                  v-model="newLinks[i].link"
                  :id="`link-${i}`"
                  type="url"
                  placeholder="https://..."
                  required
                />
                <CFormFeedback invalid>URL 링크를 입력하세요.</CFormFeedback>
              </CCol>
              <CCol sm="5">
                <CInputGroup>
                  <CFormInput
                    v-model="newLinks[i].name"
                    placeholder="파일명 또는 링크 이름 (필수)"
                    required
                  />
                  <CInputGroupText @click="removeLink(i)" style="cursor: pointer">
                    <v-icon icon="mdi-trash-can-outline" size="16" />
                  </CInputGroupText>
                </CInputGroup>
                <CFormFeedback invalid>파일명 또는 링크 이름을 입력하세요.</CFormFeedback>
              </CCol>
            </CRow>

            <CRow class="mb-3">
              <CCol :sm="{ span: 10, offset: 2 }" class="text-right">
                <v-btn color="info" size="x-small" @click="addLink">
                  <v-icon icon="mdi-link-plus" size="small" class="mr-1" />
                  외부 링크 추가
                </v-btn>
              </CCol>
            </CRow>

            <!-- Related Issues & Inline Action Items Section -->
            <CRow class="mb-3">
              <CFormLabel class="col-sm-2 col-form-label text-right">
                <span class="text-primary font-weight-bold">후속 조치 업무</span>
              </CFormLabel>
              <CCol sm="10">
                <div class="d-flex align-items-center justify-content-between mb-2">
                  <span class="text-muted small">
                    <v-icon
                      icon="mdi-clipboard-check-outline"
                      size="small"
                      class="mr-1"
                      color="primary"
                    />
                    회의록 저장 시 등록된 업무가 해당 회의와 연동되어 일괄 생성됩니다.
                  </span>
                  <div class="d-flex gap-2">
                    <v-btn
                      v-if="form.action_items"
                      color="secondary"
                      size="x-small"
                      variant="tonal"
                      @click="parseActionItemsFromText"
                    >
                      <v-icon icon="mdi-magic-staff" size="14" class="mr-1" />
                      후속 조치에서 자동 추출
                    </v-btn>
                    <v-btn color="primary" size="x-small" @click="addPendingActionItem()">
                      <v-icon icon="mdi-plus" size="14" class="mr-1" />
                      업무 추가
                    </v-btn>
                  </div>
                </div>

                <!-- 1. Existing linked issues (when editing an existing meeting) -->
                <div v-if="form.pk && meeting?.issues?.length" class="mb-3">
                  <div class="small fw-bold text-muted mb-1">
                    <v-icon icon="mdi-link-variant" size="14" class="mr-1" />
                    이미 등록된 관련 업무 ({{ meeting.issues.length }}건)
                  </div>
                  <CTable small striped borderless class="border-bottom">
                    <CTableBody>
                      <CTableRow v-for="issue in meeting.issues" :key="issue.pk">
                        <CTableDataCell style="width: 55%">
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
                          <v-chip
                            size="x-small"
                            label
                            :color="issue.closed ? 'success' : 'primary'"
                          >
                            {{ issue.status }}
                          </v-chip>
                        </CTableDataCell>
                        <CTableDataCell style="width: 20%" class="text-right">
                          <span v-if="issue.assigned_to" class="small text-muted">
                            <v-icon icon="mdi-account-outline" size="12" class="mr-1" />
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
                            <v-icon icon="mdi-pencil" size="14" />
                          </v-btn>
                        </CTableDataCell>
                      </CTableRow>
                    </CTableBody>
                  </CTable>
                </div>

                <!-- 2. Pending Action Items Table -->
                <div v-if="pendingActionItems.length > 0" class="mb-2">
                  <div class="small fw-bold text-primary mb-1">
                    <v-icon icon="mdi-playlist-plus" size="14" class="mr-1" />
                    새로 등록할 후속 조치 업무 ({{ pendingActionItems.length }}건)
                  </div>
                  <CTable small bordered hover responsive class="align-middle mb-1 bg-white">
                    <CTableHead color="light">
                      <CTableRow class="text-center small">
                        <CTableHeaderCell style="width: 45%">업무 제목 (필수)</CTableHeaderCell>
                        <CTableHeaderCell style="width: 22%">담당자</CTableHeaderCell>
                        <CTableHeaderCell style="width: 18%">완료 기한</CTableHeaderCell>
                        <CTableHeaderCell style="width: 10%">우선순위</CTableHeaderCell>
                        <CTableHeaderCell style="width: 5%">삭제</CTableHeaderCell>
                      </CTableRow>
                    </CTableHead>
                    <CTableBody>
                      <CTableRow v-for="(item, idx) in pendingActionItems" :key="item.id">
                        <CTableDataCell>
                          <CFormInput
                            v-model="item.subject"
                            size="sm"
                            placeholder="업무 제목 입력"
                            required
                          />
                        </CTableDataCell>
                        <CTableDataCell>
                          <CFormSelect v-model="item.assigned_to" size="sm">
                            <option :value="null">미지정</option>
                            <option v-for="u in users" :key="u.pk" :value="u.pk">
                              {{ u.username }}
                            </option>
                          </CFormSelect>
                        </CTableDataCell>
                        <CTableDataCell>
                          <CFormInput v-model="item.due_date" type="date" size="sm" />
                        </CTableDataCell>
                        <CTableDataCell>
                          <CFormSelect v-model="item.priority" size="sm">
                            <option v-for="p in priorityList" :key="p.pk" :value="p.pk">
                              {{ p.name }}
                            </option>
                          </CFormSelect>
                        </CTableDataCell>
                        <CTableDataCell class="text-center">
                          <v-btn
                            icon
                            size="x-small"
                            variant="text"
                            color="danger"
                            @click="removePendingActionItem(idx)"
                          >
                            <v-icon icon="mdi-trash-can-outline" size="14" />
                          </v-btn>
                        </CTableDataCell>
                      </CTableRow>
                    </CTableBody>
                  </CTable>
                </div>

                <!-- Empty state when no issues and no pending action items -->
                <div
                  v-if="!pendingActionItems.length && (!form.pk || !meeting?.issues?.length)"
                  class="text-muted small p-3 text-center border rounded border-dashed bg-more-light"
                >
                  <v-icon icon="mdi-information-outline" size="small" class="mr-1" />
                  연결된 후속 조치 업무가 없습니다. 상단의 <strong>[후속 조치에서 자동 추출]</strong> 또는
                  <strong>[업무 추가]</strong> 버튼을 눌러 후속 조치를 업무로 등록하세요.
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
                <IssueProjectSelector
                  v-model="form.project"
                  :issue-project-list="meetingProjects"
                  required
                  :disabled="!!projId"
                />
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
              <CFormLabel for="location" class="col-sm-4 col-form-label text-right">
                회의장소
              </CFormLabel>
              <CCol sm="8">
                <CFormInput
                  v-model="form.location"
                  id="location"
                  placeholder="회의 장소 또는 링크"
                />
              </CCol>
            </CRow>

            <CRow class="mb-3">
              <CFormLabel for="category" class="col-sm-4 col-form-label text-right required">
                카테고리
              </CFormLabel>
              <CCol sm="8">
                <CInputGroup>
                  <CFormSelect v-model="form.category" id="category" required>
                    <option value="">---------</option>
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

            <CRow v-if="meeting?.pk && canMeetingConfirm" class="mt-5">
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
              :disabled="(form.pk ? !canMeetingUpdate : !canMeetingCreate) || isSubmitting"
              :loading="isSubmitting"
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
        :current-project="workStore.allReadableProjectsFlat.find(p => p.pk === form.project)"
        :my-projects="myProjects"
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
    <template #header> 회의록 카테고리 추가</template>
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
            <IssueProjectSelector
              v-model="categoryForm.project"
              :issue-project-list="meetingProjects"
              id="cat-project"
              disabled
            />
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
            <v-btn type="submit" color="primary" size="small"> 저장</v-btn>
            <v-btn color="light" size="small" @click="refCategoryModal.close()" flat> 취소</v-btn>
          </CCol>
        </CRow>
      </CForm>
    </template>
  </FormModal>
</template>
