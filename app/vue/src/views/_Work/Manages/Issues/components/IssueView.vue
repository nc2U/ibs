<script lang="ts" setup>
import { computed, type ComputedRef, inject, onBeforeMount, type PropType, ref, watch } from 'vue'
import type {
  CodeValue,
  Issue,
  IssueComment,
  IssueProject,
  IssueStatus,
  SubIssue,
  TimeEntry,
} from '@/store/types/work'
import { diffDate, elapsedTime, timeFormat } from '@/utils/baseMixins'
import { useWork } from '@/store/pinia/work'
import { useRoute, useRouter } from 'vue-router'
import { VueMarkdownIt } from '@f3ve/vue-markdown-it'
import IssueControl from './IssueControl.vue'
import IssueHistory from './IssueHistory.vue'
import IssueForm from '@/views/_Work/Manages/Issues/components/IssueForm.vue'
import IssueFiles from './issueFiles/Index.vue'
import SubIssues from './subIssues/Index.vue'
import SubSummary from './subIssues/Summary.vue'
import Relations from './relations/Index.vue'
import RelSummary from './relations/Summary.vue'
import AddRelationForm from './relations/AddRelationForm.vue'

const props = defineProps({
  issueProject: { type: Object as PropType<IssueProject>, default: null },
  issue: { type: Object as PropType<Issue>, required: true },
  allProjects: { type: Array as PropType<IssueProject[]>, default: () => [] },
  issueCommentList: { type: Array as PropType<IssueComment[]>, default: () => [] },
  timeEntryList: { type: Array as PropType<TimeEntry[]>, default: () => [] },

  statusList: { type: Array as PropType<IssueStatus[]>, default: () => [] },
  priorityList: { type: Array as PropType<CodeValue[]>, default: () => [] },
})

const emit = defineEmits(['on-submit'])

const issueFormRef = ref()
const editForm = ref(false)

const workManager = inject<ComputedRef<boolean>>('workManager')

const isClosed = computed(() => props.issue?.closed)

const workStore = useWork()
const issueNums = computed(() => workStore.issueNums)
const issueLogList = computed(() => workStore.issueLogList)
const my_perms = computed(() => workStore.issueProject?.my_perms)
const getIssues = computed(() => workStore.getIssues.filter(i => i.value !== props.issue.pk))

const doneRatio = computed(() => {
  if (props.issue?.sub_issues.length) {
    return (
      props.issue.sub_issues.map(sub => sub.done_ratio).reduce((a, b) => a + b) /
      props.issue.sub_issues.length
    )
  } else return props.issue?.done_ratio
})

const estimatedHours = computed(
  () =>
    props.issue.sub_issues.map(s => Number(s.estimated_hours ?? 0)).reduce((a, b) => a + b) +
    (props.issue?.estimated_hours ?? 0),
)

const numToTime = (n: number | null) => {
  const hours = Math.floor(n ?? 0)
  const minutes = Math.round(((n ?? 0) - hours) * 60)
  const str = minutes >= 10 ? '' : '0'
  return `${hours}:${str}${minutes}`
}

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
  editForm.value = !editForm.value

  setTimeout(() => {
    scrollToId('edit-form')
    issueFormRef.value.callComment()
  }, 100)
}

const callReply = (payload?: { id: number; user: string; content: string }) => {
  editForm.value = !editForm.value

  setTimeout(() => {
    scrollToId('edit-form')
    issueFormRef.value.callReply(payload)
  }, 100)
}

// 지켜보기 / 관심끄기
const watchControl = (payload: any) => {
  const form = new FormData()
  if (payload.watchers)
    payload.watchers.forEach(val => form.append('watchers', JSON.stringify(val)))
  else if (payload.del_watcher) form.append('del_watcher', JSON.stringify(payload.del_watcher))
  workStore.patchIssue(props.issue?.pk, form)
}

// file 관련 코드
const fileControl = (payload: FormData) => workStore.patchIssue(props.issue?.pk, payload)

// 하위 업무 관련 코드
const unlinkSubIssue = (del_child: number) => workStore.patchIssue(props.issue?.pk, { del_child })

// 연결된 업무 관련 코드
const addRIssue = ref(false)
const addFormCtl = (bool: boolean) => (addRIssue.value = bool)
const addRelIssue = (payload: any) => workStore.createIssueRelation(payload)
const deleteRelation = (pk: number) => workStore.deleteIssueRelation(pk, props.issue?.pk)

// issue comment 관련
const delSubmit = (pk: number) => workStore.deleteIssueComment(pk, props.issue.pk)

const [route, router] = [useRoute(), useRouter()]
watch(route, async nVal => {
  if (nVal.query.edit) callEditForm()
})

onBeforeMount(async () => {
  await workStore.fetchIssueLogList({ issue: props.issue.pk })
  if (route.query.edit) callEditForm()
})
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>
        <span>{{ issue?.tracker.name }} #{{ issue?.pk }}</span>
        <v-badge
          :color="isClosed ? 'success' : 'primary'"
          :content="isClosed ? '완료됨' : '진행중'"
          inline
          rounded="1"
          class="ml-2"
        />
        <v-badge v-if="issue.is_private" color="danger" content="비공개" inline rounded="1" />
      </h5>
    </CCol>

    <IssueControl
      :proj-status="issueProject.status"
      :watchers="issue.watchers"
      @call-edit-form="callEditForm"
      @go-time-entry="
        () => router.push({ name: '(소요시간) - 추가', query: { issue_id: issue.pk } })
      "
      @watch-control="watchControl"
    />
  </CRow>

  <CCard color="yellow-lighten-5 mb-3">
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
            >다음 »
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
                  name: '(작업내역)',
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
                  name: '(작업내역)',
                  params: { projId: issueProject.slug ?? '' },
                  query: { from: issue.updated.substring(0, 10) },
                }"
              >
                {{ elapsedTime(issue.updated) }}
              </router-link>
              <v-tooltip activator="parent" location="top">
                {{ timeFormat(issue?.updated) }}
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

          <CRow v-if="issueProject.categories?.length">
            <CCol class="title">범주 :</CCol>
            <CCol>{{ issue.category }}</CCol>
          </CRow>

          <CRow v-if="issue.fixed_version">
            <CCol class="title">목표버전 :</CCol>
            <CCol>
              <router-link
                :to="{ name: '(로드맵) - 보기', params: { verId: issue.fixed_version.pk } }"
              >
                {{ issue.fixed_version.name }}
              </router-link>
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
              <span v-if="!isClosed && !!issue.due_date && diffDate(issue.due_date) > 0">
                ({{ Math.floor(diffDate(issue.due_date)) }} 일 지연)
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
                <span class="ml-2 pt-0">{{ doneRatio ?? 0 }}%</span>
              </div>
            </CCol>
          </CRow>
          <CRow>
            <CCol class="title">추정시간:</CCol>
            <CCol v-if="issue?.sub_issues.length">
              (합계 : {{ numToTime(estimatedHours) }} 시간)
            </CCol>
            <CCol v-else-if="issue?.estimated_hours">
              {{ numToTime(issue?.estimated_hours) }} 시간
            </CCol>
          </CRow>
          <CRow v-if="issue?.spent_time">
            <CCol class="title">소요시간:</CCol>
            <CCol>
              <router-link :to="{ name: '(소요시간)', query: { issue_id: issue.pk } }">
                {{ numToTime(issue?.spent_time) }} 시간
              </router-link>
            </CCol>
          </CRow>
        </CCol>
      </CRow>

      <v-divider />

      <CRow class="mb-2">
        <CCol class="title">설명</CCol>
        <CCol
          v-if="issueProject.status !== '9' && (workManager || my_perms?.issue_comment_create)"
          class="text-right form-text"
        >
          <v-icon icon="mdi-comment-text-outline" size="sm" color="grey" class="mr-2" />
          <router-link to="" @click="callComment">댓글달기</router-link>
        </CCol>
      </CRow>

      <CRow>
        <CCol class="pl-4">
          <VueMarkdownIt :source="issue?.description" />
        </CCol>
      </CRow>

      <v-divider v-if="issueProject.status !== '9' || issue.files.length" />

      <IssueFiles
        v-if="issue.files?.length"
        :proj-status="issueProject.status"
        :issue-files="issue.files"
        @issue-file-control="fileControl"
      />

      <CRow v-if="issueProject.status !== '9'" class="mb-2">
        <CCol class="col-10">
          <span class="title mr-2">하위 업무</span>
          <SubSummary
            v-if="issue.sub_issues.length"
            :issue-pk="issue.pk"
            :sub-issues="issue.sub_issues"
          />
        </CCol>
        <CCol class="text-right form-text">
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

      <v-divider v-if="issueProject.status !== '9'" />

      <CRow v-if="issueProject.status !== '9'">
        <CCol class="col-10">
          <span class="title mr-2">연결된 업무</span>
          <RelSummary
            v-if="issue.related_issues.length"
            :issue-pk="issue.pk"
            :rel-issue-tos="issue.related_issues.map(i => i.issue_to as SubIssue)"
          />
        </CCol>
        <CCol class="text-right form-text">
          <router-link to="" @click="addRIssue = !addRIssue">추가</router-link>
        </CCol>
      </CRow>

      <!--      <Relations-->
      <!--        v-if="issue.related_issues.length"-->
      <!--        :add-r-issue="addRIssue"-->
      <!--        :related-issues="issue.related_issues"-->
      <!--        :get-issues="getIssues"-->
      <!--        @delete-relation="deleteRelation"-->
      <!--        class="mt-2"-->
      <!--      />-->

      <!--      <AddRelationForm-->
      <!--        v-if="addRIssue"-->
      <!--        :issue-pk="issue.pk"-->
      <!--        :get-issues="getIssues"-->
      <!--        @add-form-ctl="addFormCtl"-->
      <!--        @add-rel-issue="addRelIssue"-->
      <!--      />-->
    </CCardBody>
  </CCard>

  <IssueHistory
    v-if="issueLogList.length"
    :issue-log-list="issueLogList"
    :issue-comment-list="issueCommentList"
    :time-entry-list="timeEntryList"
    @call-reply="callReply"
    @del-submit="delSubmit"
  />

  <div>
    <IssueControl
      :proj-status="issueProject.status"
      :watchers="issue.watchers"
      @call-edit-form="callEditForm"
      @go-time-entry="
        () => router.push({ name: '(소요시간) - 추가', query: { issue_id: issue.pk } })
      "
      @watch-control="watchControl"
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
</template>

<style lang="scss" scoped>
.title {
  font-weight: bold;
}

.sub-title {
  font-size: 1.1em;
  font-weight: bold;
  color: #0f192a;
}
</style>
