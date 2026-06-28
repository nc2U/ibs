<script lang="ts" setup>
import { computed, onBeforeMount, type PropType, ref, watch } from 'vue'
import type { getProject, IssueProject } from '@/store/types/work_project.ts'
import type { CodeValue, Issue, IssueComment, IssueStatus } from '@/store/types/work_issue.ts'
import { useRoute, useRouter } from 'vue-router'
import { usePerms } from '@/composables/usePerms'
import { markdownRender } from '@/utils/helper.ts'
import { diffDate, elapsedTime, timeFormat } from '@/utils/baseMixins'
import { useIssue } from '@/store/pinia/work_issue.ts'
import { useLogging } from '@/store/pinia/work_logging.ts'
import IssueControl from './IssueControl.vue'
import IssueHistory from './IssueHistory.vue'
import IssueForm from './IssueForm.vue'
import IssueFiles from './issueFiles/Index.vue'
import SubIssues from './subIssues/Index.vue'
import SubSummary from './subIssues/Summary.vue'
import RelSummary from './relations/Summary.vue'
import Index from './relations/Index.vue'
import AddRelationForm from './relations/AddRelationForm.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

const props = defineProps({
  issueProject: { type: Object as PropType<IssueProject>, default: null },
  issue: { type: Object as PropType<Issue>, required: true },
  allProjects: { type: Array as PropType<getProject[]>, default: () => [] },
  issueCommentList: { type: Array as PropType<IssueComment[]>, default: () => [] },
  statusList: { type: Array as PropType<IssueStatus[]>, default: () => [] },
  priorityList: { type: Array as PropType<CodeValue[]>, default: () => [] },
})

const emit = defineEmits(['on-submit'])

const issueFormRef = ref()
const editForm = ref(false)

const { can, PERM } = usePerms()
const canCommentCreate = computed(
  () => props.issueProject?.status !== '9' && can(PERM.ISSUE_COMMENT_CREATE),
)

const isClosed = computed(() => props.issue?.closed)

const issueStore = useIssue()
const issueNums = computed(() => issueStore.issueNums ?? [])
const getIssues = computed(() => {
  const issues = issueStore.getIssues
  if (!props.issue) return issues
  return issues.filter(i => i.value !== props.issue?.pk)
})

const logStore = useLogging()
const issueLogList = computed(() => logStore.issueLogList)

const doneRatio = computed(() => {
  if (props.issue?.sub_issues.length) {
    return (
      props.issue.sub_issues.map(sub => sub.done_ratio).reduce((a, b) => a + b) /
      props.issue.sub_issues.length
    )
  } else return props.issue?.done_ratio
})

const onSubmit = (payload: any) => {
  emit('on-submit', payload)
  editForm.value = false
}

const scrollToId = (id: string) => {
  const el = document.getElementById(id)
  if (el) el.scrollIntoView({ behavior: 'smooth' })
}

const callEditForm = () => {
  editForm.value = !editForm.value
  setTimeout(() => {
    scrollToId('edit-form')
  }, 100)
}

const callComment = () => {
  editForm.value = true
  setTimeout(() => {
    scrollToId('edit-form')
    if (issueFormRef.value) issueFormRef.value.callComment()
  }, 100)
}

const callReply = (payload?: { id: number; user: string; content: string }) => {
  editForm.value = true
  setTimeout(() => {
    scrollToId('edit-form')
    if (issueFormRef.value) issueFormRef.value.callReply(payload)
  }, 100)
}

const goMeeting = () => {
  if (props.issue?.meeting_desc) {
    const meetingId = props.issue.meeting_desc.pk
    const projId = props.issueProject?.slug
    if (projId) {
      router.push({ name: '(회의) - 보기', params: { projId, meetingId } })
    } else {
      router.push({ name: '회의 - 보기', params: { meetingId } })
    }
  }
}

// 지켜보기 / 관심끄기
const watchControl = (payload: { watchers: any[]; del_watcher?: number }) => {
  const form = new FormData()
  if (payload.watchers)
    payload.watchers.forEach(val => form.append('watchers', JSON.stringify(val)))
  else if (payload.del_watcher) form.append('del_watcher', JSON.stringify(payload.del_watcher))
  issueStore.patchIssue(props.issue?.pk as number, form)
}

// 하위 업무 관련 코드
const unlinkSubIssue = (del_child: number) =>
  issueStore.patchIssue(props.issue?.pk as number, { del_child })

// 연결된 업무 관련 코드
const addRIssue = ref(false)
const addFormCtl = (bool: boolean) => (addRIssue.value = bool)
const addRelIssue = (payload: any) => {
  issueStore.createIssueRelation(payload)
  addRIssue.value = false
}
const deleteRelation = (pk: number) => issueStore.deleteIssueRelation(pk, props.issue?.pk as number)

// issue comment 관련
const delSubmit = (pk: number) => issueStore.deleteIssueComment(pk, props.issue?.pk)

const refDelModal = ref()

const deleteIssue = () => {
  refDelModal.value.callModal(
    '업무 삭제',
    '정말로 이 업무를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.',
    'mdi-trash-can-outline',
    'danger',
  )
}

const confirmDelete = () => {
  issueStore.deleteIssue(props.issue?.pk as number)
  refDelModal.value.close()
  if (route.params.projId) {
    router.push({ name: '(업무)' })
  } else {
    router.push({ name: '업무' })
  }
}

const [route, router] = [useRoute(), useRouter()]
watch(route, async nVal => {
  if (nVal.query.edit) callEditForm()
})

onBeforeMount(async () => {
  await logStore.fetchIssueLogList({ issue: props.issue?.pk })
  if (route.query.edit) callEditForm()
})
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>
        <span>{{ issue?.tracker.name }} #{{ issue?.pk }}</span>
        <v-badge
          :color="isClosed ? 'success' : 'info'"
          :content="isClosed ? '완료됨' : '진행중'"
          inline
          rounded="1"
          class="ml-2"
        />
        <v-badge v-if="issue.is_private" color="danger" content="비공개" inline rounded="1" />
      </h5>
    </CCol>

    <IssueControl
      :proj-status="issueProject?.status"
      :watchers="issue.watchers"
      :issue="issue"
      @call-edit-form="callEditForm"
      @watch-control="watchControl"
      @call-delete-issue="deleteIssue"
    />
  </CRow>

  <CCard class="mb-3 shadow-sm card-yellow">
    <CCardBody>
      <CRow>
        <CCol>
          <span class="sub-title">{{ issue.subject }}</span>
        </CCol>

        <CCol class="text-right form-text">
          <span v-if="issue.pk === issueNums[0]">« 뒤로</span>
          <router-link
            v-else
            :to="{
              name: '(업무) - 보기',
              params: {
                issueId: issueNums[issueNums.indexOf(issue.pk) - 1],
              },
            }"
            >« 뒤로
          </router-link>
          <span class="mx-2">|</span>
          <router-link :to="{ name: '(업무)' }">
            {{ issueNums.indexOf(issue.pk) + 1 }}/{{ issueNums.length }}
          </router-link>
          <span class="mx-2">|</span>
          <span v-if="issue.pk === issueNums[issueNums.length - 1]">다음 »</span>
          <router-link
            v-else
            :to="{
              name: '(업무) - 보기',
              params: {
                issueId: issueNums[issueNums.indexOf(issue.pk) + 1],
              },
            }"
          >
            다음 »
          </router-link>
        </CCol>
      </CRow>

      <CRow>
        <CCol>
          <p class="mt-1 form-text">
            <router-link :to="{ name: '사용자 - 보기', params: { userId: issue.creator.pk } }">
              {{ issue.creator.username }}
            </router-link>
            이(가)
            <span>
              <router-link
                :to="{
                  name: '(실행기록)',
                  params: { projId: issueProject?.slug },
                  query: { from: issue?.created.substring(0, 10) },
                }"
              >
                {{ elapsedTime(issue.created) }}
              </router-link>
              <v-tooltip activator="parent" location="top">
                {{ timeFormat(issue.created) }}
              </v-tooltip>
            </span>
            전에 추가함.
            <span>
              <router-link
                :to="{
                  name: '(실행기록)',
                  params: { projId: issueProject?.slug ?? '' },
                  query: { from: issue.updated.substring(0, 10) },
                }"
              >
                {{ elapsedTime(issue.updated) }}
              </router-link>
              <v-tooltip activator="parent" location="top">
                {{ timeFormat(issue?.updated as string) }}
              </v-tooltip>
            </span>
            전에 수정됨.
          </p>
        </CCol>
      </CRow>

      <CRow>
        <CCol md="6">
          <CRow>
            <CCol class="title">상태 :</CCol>
            <CCol>{{ issue?.status.name }}</CCol>
          </CRow>
          <CRow>
            <CCol class="title">우선순위 :</CCol>
            <CCol>{{ issue?.priority.name }}</CCol>
          </CRow>
          <CRow>
            <CCol class="title">담당자 :</CCol>
            <CCol>
              <router-link
                v-if="issue.assigned_to"
                :to="{ name: '사용자 - 보기', params: { userId: issue?.assigned_to?.pk ?? 0 } }"
              >
                {{ issue?.assigned_to?.username }}
              </router-link>
            </CCol>
          </CRow>

          <CRow v-if="issueProject?.categories?.length">
            <CCol class="title">범주 :</CCol>
            <CCol>{{ issue.category }}</CCol>
          </CRow>

          <CRow v-if="issue.fixed_version">
            <CCol class="title">목표단계 :</CCol>
            <CCol>
              <router-link
                :to="{ name: '(로드맵) - 보기', params: { verId: issue.fixed_version.pk } }"
              >
                {{ issue.fixed_version?.name }}
              </router-link>
              <span v-if="issue.fixed_version.description">
                ({{ issue.fixed_version.description }})
              </span>
            </CCol>
          </CRow>
        </CCol>

        <CCol md="6">
          <CRow>
            <CCol class="title">시작일자 :</CCol>
            <CCol>{{ issue?.start_date }}</CCol>
          </CRow>
          <CRow>
            <CCol class="title">완료기한 :</CCol>
            <CCol
              :class="{
                'text-danger': !isClosed && !!issue.due_date && diffDate(issue.due_date) > 0,
              }"
            >
              {{ issue?.due_date }}
              <span v-if="!isClosed && !!issue?.due_date && diffDate(issue.due_date) > 0">
                ({{ Math.floor(diffDate(issue.due_date as string)) }} 일 지연)
              </span>
            </CCol>
          </CRow>
          <CRow>
            <CCol class="title">진척도 :</CCol>
            <CCol>
              <div>
                <CProgress
                  color="green-lighten-3"
                  :value="doneRatio ?? 0"
                  style="width: 110px; float: left; margin-top: 2px"
                  height="16"
                />
                <span class="ml-2 pt-0">{{ (doneRatio ?? 0).toFixed(2) }}%</span>
              </div>
            </CCol>
          </CRow>
          <CRow>
            <CCol class="title">예상 처리기간:</CCol>
            <CCol>
              {{ issue?.expected_duration_display }}
            </CCol>
          </CRow>
        </CCol>
      </CRow>

      <v-divider />

      <CRow class="mb-2">
        <CCol class="title">설명</CCol>
        <CCol v-if="canCommentCreate" class="text-right form-text">
          <v-icon icon="mdi-comment-text-outline" size="sm" color="grey" class="mr-2" />
          <router-link to="" @click="callComment">댓글달기</router-link>
        </CCol>
      </CRow>

      <CRow class="pl-4">
        <CCol v-html="markdownRender(issue.description)" />
      </CRow>

      <v-divider v-if="issueProject?.status !== '9' || issue.files.length" />

      <IssueFiles
        v-if="issue.files?.length"
        :proj-status="issueProject?.status"
        :issue-pk="issue.pk"
        :issue-files="issue.files"
      />

      <CRow v-if="issueProject?.status !== '9'" class="mb-2">
        <CCol class="col-10">
          <span class="title mr-2">하위 업무</span>
          <SubSummary
            v-if="issue.sub_issues.length"
            :issue-pk="issue.pk"
            :sub-issues="issue.sub_issues"
          />
        </CCol>
        <CCol v-if="can(PERM.ISSUE_SUB_MANAGE)" class="text-right form-text">
          <router-link
            :to="{ name: '(업무) - 추가', query: { parent: issue.pk, tracker: issue.tracker.pk } }"
          >
            추가
          </router-link>
        </CCol>
      </CRow>

      <SubIssues
        v-if="issue.sub_issues.length"
        :sub-issues="issue.sub_issues"
        @unlink-sub-issue="unlinkSubIssue"
      />

      <v-divider v-if="issueProject?.status !== '9'" />

      <CRow v-if="issueProject?.status !== '9'" class="mb-2">
        <CCol class="col-10">
          <span class="title mr-2">연결된 업무</span>
          <RelSummary
            v-if="issue?.outgoing_relations.length || issue?.incoming_relation"
            :issue-pk="issue.pk"
            :rel-issue-tos="[]"
          />
        </CCol>
        <CCol v-if="can(PERM.ISSUE_REL_MANAGE)" class="text-right form-text">
          <router-link to="" @click="addRIssue = !addRIssue">추가</router-link>
        </CCol>
      </CRow>

      <!-- Outgoing relations -->
      <template v-for="rel in issue.outgoing_relations" :key="rel.pk">
        <Index :rel="rel" type="선행업무" @delete-relation="deleteRelation(rel.pk as number)" />
      </template>

      <!-- Incoming (reverse) relation -->
      <Index
        v-if="issue?.incoming_relation"
        :rel="issue.incoming_relation"
        type="후행업무"
        @delete-relation="deleteRelation(issue.incoming_relation.pk as number)"
      />

      <AddRelationForm
        v-if="addRIssue"
        :issue-pk="issue.pk"
        :get-issues="getIssues"
        class="mt-4"
        @add-rel-issue="addRelIssue"
        @add-form-ctl="addFormCtl"
      />

      <v-divider v-if="issue.meeting_desc" />

      <CRow v-if="issue.meeting_desc">
        <CCol>
          <span class="title mr-2">관련 회의</span>
          <a href="javascript:void(0)" @click="goMeeting">
            {{ issue.meeting_desc?.title }}
          </a>
        </CCol>
      </CRow>
    </CCardBody>
  </CCard>

  <IssueHistory
    v-if="issueLogList.length"
    :issue-log-list="issueLogList"
    :issue-comment-list="issueCommentList"
    @call-reply="callReply"
    @del-submit="delSubmit"
  />

  <div>
    <IssueControl
      :proj-status="issueProject?.status"
      :watchers="issue.watchers"
      :issue="issue"
      @call-edit-form="callEditForm"
      @watch-control="watchControl"
      @call-delete-issue="deleteIssue"
    />
  </div>

  <div v-if="editForm">
    <IssueForm
      ref="issueFormRef"
      :issue-project="issueProject"
      :issue="issue"
      :all-projects="allProjects"
      :status-list="statusList"
      :priority-list="priorityList"
      :get-issues="getIssues"
      @on-submit="onSubmit"
      @close-form="() => (editForm = false)"
    />
  </div>

  <ConfirmModal ref="refDelModal">
    <template #footer>
      <v-btn size="small" color="warning" @click="confirmDelete">삭제</v-btn>
    </template>
  </ConfirmModal>
</template>
