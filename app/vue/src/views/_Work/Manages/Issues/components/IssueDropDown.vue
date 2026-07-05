<script lang="ts" setup>
import { computed, onBeforeMount, type PropType, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePerms } from '@/composables/usePerms.ts'
import { errorHandle, message } from '@/utils/helper'
import { useAccount } from '@/store/pinia/account.ts'
import { useIssue } from '@/store/pinia/work_issue.ts'
import { useWork } from '@/store/pinia/work_project.ts'
import type { Issue, SimpleIssue } from '@/store/types/work_issue.ts'
import type { SimpleUser } from '@/store/types/work_project.ts'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

const props = defineProps({
  issue: { type: Object as PropType<Issue | SimpleIssue>, required: true },
})

const emit = defineEmits(['watch-control'])

const refDelModal = ref()

const router = useRouter()
const route = useRoute()

const accStore = useAccount()
const userInfo = computed(() => accStore.userInfo)
const projectStore = useWork()

const { can, PERM } = usePerms()

// 프로젝트 종료 여부 및 내 권한 연동 연산 추가
const isProjectClosed = computed(() => {
  const proj = projectStore.allProjects.find(p => p.slug === props.issue.project.slug)
  return proj?.status === '9'
})

const issueCreator = computed(() => (props.issue as any).creator?.pk ?? null)
const issueAssignee = computed(() => {
  const assigned = props.issue.assigned_to
  if (!assigned) return null
  return typeof assigned === 'object' ? assigned.pk : assigned
})
const isCreator = computed(() => issueCreator.value === userInfo.value?.pk)
const isAssignee = computed(() => issueAssignee.value === userInfo.value?.pk)

const canEditIssue = computed(() => {
  if (isProjectClosed.value) return false
  if (can(PERM.ISSUE_UPDATE)) return true
  return can(PERM.ISSUE_OWN_UPDATE) && (isCreator.value || isAssignee.value)
})

const canCreateSubIssue = computed(() => can(PERM.ISSUE_CREATE) && !isProjectClosed.value)

const issueStore = useIssue()
const statusList = computed(() => issueStore.statusList)
const trackerList = computed(() => {
  const projectPk = props.issue.project.pk
  return issueStore.trackerList.filter(t => t.projects.some(p => p.pk === projectPk))
})
const priorityList = computed(() => issueStore.priorityList)

const isWatcher = ref(false)

const isCumputedWatcher = computed(() =>
  props.issue?.watchers.map(w => w.pk).includes(userInfo?.value?.pk as number),
)

const watchControl = () => {
  emit('watch-control', props.issue?.pk)
  isWatcher.value = !isWatcher.value
}

const changeStatus = (statusPk: number) => {
  const currentStatusPk =
    typeof props.issue.status === 'object' ? props.issue.status.pk : props.issue.status
  if (currentStatusPk !== statusPk) {
    issueStore.patchIssue(props.issue.pk, { status: statusPk })
  }
}

const changeTracker = (trackerPk: number) => {
  if (props.issue.tracker.pk !== trackerPk) {
    issueStore.patchIssue(props.issue.pk, { tracker: trackerPk })
  }
}

const changePriority = (priorityPk: number) => {
  const currentPriorityPk =
    typeof props.issue.priority === 'object' ? props.issue.priority.pk : props.issue.priority
  if (currentPriorityPk !== priorityPk) {
    issueStore.patchIssue(props.issue.pk, { priority: priorityPk })
  }
}

// 담당자 변경 관련 로직 추가
const members = ref<any[]>([])
const loadingMembers = ref(false)
const assignableMembers = computed(() => members.value.filter(m => m.is_assignable))

const canAssignToMe = computed(() => {
  const myPk = userInfo.value?.pk
  if (!myPk) return false
  if (userInfo.value?.is_superuser || accStore.workManager) return true
  return assignableMembers.value.some(m => m.user_id === myPk)
})

const fetchMembersOnDemand = async (visible: boolean) => {
  if (visible && members.value.length === 0) {
    loadingMembers.value = true
    try {
      await projectStore.fetchProjectMembers(props.issue?.project.slug)
      members.value = projectStore.projectMembers
    } catch (err: any) {
      errorHandle(err.response?.data)
    } finally {
      loadingMembers.value = false
    }
  }
}

const getAssigneePk = (assignedTo: number | SimpleUser | null | undefined) => {
  if (!assignedTo) return null
  return typeof assignedTo === 'object' ? assignedTo.pk : assignedTo
}

const changeAssignee = (userPk: number | null) => {
  const currentAssigneePk = getAssigneePk(props.issue.assigned_to)
  if (currentAssigneePk !== userPk) {
    issueStore.patchIssue(props.issue.pk, { assigned_to: userPk ?? '' })
  }
}

// 진척도 변경 관련 로직 추가
const progressOptions = Array.from({ length: 11 }, (_, i) => i * 10)

const changeProgress = (ratio: number) => {
  if (props.issue.done_ratio !== ratio) {
    issueStore.patchIssue(props.issue.pk, { done_ratio: ratio })
  }
}

// 업무 관람자 변경 관련 로직 추가
const isWatcherMember = (userPk: number) => {
  return props.issue.watchers.map(w => w.pk).includes(userPk)
}

const toggleWatcher = (userPk: number) => {
  if (isWatcherMember(userPk)) {
    issueStore.patchIssue(props.issue.pk, { del_watcher: userPk })
  } else {
    issueStore.patchIssue(props.issue.pk, { watchers: [userPk] })
  }
}

// 복사, 링크복사, 삭제 권한 정의
const showCopyButton = computed(() => can(PERM.ISSUE_COPY) && !isProjectClosed.value)
const showDeleteButton = computed(() => can(PERM.ISSUE_DELETE) && !isProjectClosed.value)

// 링크 복사 기능
const fallbackCopy = (text: string) => {
  const textArea = document.createElement('textarea')
  textArea.value = text
  textArea.style.position = 'fixed'
  textArea.style.left = '-999999px'
  textArea.style.top = '-999999px'
  document.body.appendChild(textArea)
  textArea.focus()
  textArea.select()
  try {
    document.execCommand('copy')
    message('success', '복사 완료', '업무 상세 링크가 클립보드에 복사되었습니다.')
  } catch (err) {
    message('danger', '오류!', '링크 복사에 실패했습니다.')
  }
  document.body.removeChild(textArea)
}

const issueLinkCopy = () => {
  const url = `${window.location.origin}/work/project/${props.issue.project.slug}/issue/${props.issue.pk}`
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard
      .writeText(url)
      .then(() => {
        message('success', '복사 완료', '업무 상세 링크가 클립보드에 복사되었습니다.')
      })
      .catch(() => fallbackCopy(url))
  } else fallbackCopy(url)
}

// 복사 (일감 복사 생성으로 이동)
const copyIssue = () => {
  const routeName = route.params.projId ? '(업무) - 추가' : '업무 - 추가'
  router.push({
    name: routeName,
    query: { copy: props.issue.pk },
  })
}

// 업무 삭제
const deleteIssue = () => {
  refDelModal.value.callModal(
    '업무 삭제',
    '정말로 이 업무를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.',
    'mdi-trash-can-outline',
    'danger',
  )
}

const confirmDelete = async () => {
  await issueStore.deleteIssue(props.issue.pk)
  refDelModal.value.close()
}

onBeforeMount(() => (isWatcher.value = isCumputedWatcher.value as any))
</script>

<template>
  <span>
    {{ members }}
    <v-btn icon variant="text" size="x-small" color="grey-darken-1">
      <v-icon icon="mdi-dots-horizontal" />
      <v-tooltip activator="parent" location="top">Actions</v-tooltip>
      <v-menu activator="parent" location="bottom end" transition="scale-transition">
        <v-list density="compact" class="py-1">
          <v-list-item
            v-if="canEditIssue"
            min-height="30px"
            class="py-0"
            @click="
              router.push({
                name: '(업무) - 보기',
                params: { projId: issue.project.slug, issueId: issue.pk },
                query: { edit: '1' },
              })
            "
          >
            <template v-slot:prepend>
              <v-icon icon="mdi-pencil" color="amber" size="15" class="mr-n2" />
            </template>
            <v-list-item-title class="text-caption">편집</v-list-item-title>
          </v-list-item>

          <v-menu v-if="canEditIssue" open-on-hover location="end" offset="5">
            <template v-slot:activator="{ props: menuProps }">
              <v-list-item
                v-bind="menuProps"
                append-icon="mdi-chevron-right"
                min-height="28px"
                class="py-0"
              >
                <template v-slot:prepend>
                  <v-icon icon="mdi-list-status" color="primary" size="small" class="mr-n2" />
                </template>
                <v-list-item-title class="text-caption">상태</v-list-item-title>
              </v-list-item>
            </template>
            <v-list density="compact" class="py-1">
              <v-list-item
                v-for="status in statusList"
                :key="status.pk"
                :active="
                  (typeof issue.status === 'object' ? issue.status.pk : issue.status) === status.pk
                "
                min-height="30px"
                min-width="150px"
                class="py-0"
                @click="changeStatus(status.pk)"
              >
                <v-list-item-title class="text-caption">{{ status.name }}</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>

          <v-menu v-if="canEditIssue && !isProjectClosed" open-on-hover location="end" offset="5">
            <template v-slot:activator="{ props: menuProps }">
              <v-list-item
                v-bind="menuProps"
                append-icon="mdi-chevron-right"
                min-height="28px"
                class="py-0"
              >
                <template v-slot:prepend>
                  <v-icon icon="mdi-tag-outline" color="teal" size="small" class="mr-n2" />
                </template>
                <v-list-item-title class="text-caption">유형</v-list-item-title>
              </v-list-item>
            </template>
            <v-list density="compact" class="py-1">
              <v-list-item
                v-for="tracker in trackerList"
                :key="tracker.pk"
                :active="issue.tracker.pk === tracker.pk"
                min-height="30px"
                min-width="150px"
                class="py-0"
                @click="changeTracker(tracker.pk)"
              >
                <v-list-item-title class="text-caption">{{ tracker.name }}</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>
          <v-menu v-if="canEditIssue && !isProjectClosed" open-on-hover location="end" offset="5">
            <template v-slot:activator="{ props: menuProps }">
              <v-list-item
                v-bind="menuProps"
                append-icon="mdi-chevron-right"
                min-height="28px"
                class="py-0"
              >
                <template v-slot:prepend>
                  <v-icon icon="mdi-alert-circle-outline" color="red" size="small" class="mr-n2" />
                </template>
                <v-list-item-title class="text-caption">우선순위</v-list-item-title>
              </v-list-item>
            </template>
            <v-list density="compact" class="py-1">
              <v-list-item
                v-for="priority in priorityList"
                :key="priority.pk"
                :active="
                  (typeof issue.priority === 'object' ? issue.priority.pk : issue.priority) ===
                  priority.pk
                "
                min-height="30px"
                min-width="150px"
                class="py-0"
                @click="changePriority(priority.pk)"
              >
                <v-list-item-title class="text-caption">{{ priority.name }}</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>

          <v-menu
            v-if="canEditIssue"
            open-on-hover
            location="end"
            offset="5"
            @update:model-value="fetchMembersOnDemand"
          >
            <template v-slot:activator="{ props: menuProps }">
              <v-list-item
                v-bind="menuProps"
                append-icon="mdi-chevron-right"
                min-height="28px"
                class="py-0"
              >
                <template v-slot:prepend>
                  <v-icon icon="mdi-account-outline" color="primary" size="small" class="mr-n2" />
                </template>
                <v-list-item-title class="text-caption">담당자</v-list-item-title>
              </v-list-item>
            </template>
            <v-list density="compact" class="py-1">
              <v-list-item v-if="loadingMembers" min-height="30px" class="py-0" disabled>
                <v-list-item-title class="text-caption text-grey">로딩 중...</v-list-item-title>
              </v-list-item>
              <template v-else>
                <v-list-item
                  v-if="canAssignToMe"
                  :active="getAssigneePk(issue.assigned_to) === userInfo?.pk"
                  min-height="30px"
                  min-width="150px"
                  class="py-0"
                  @click="changeAssignee(userInfo?.pk as number)"
                >
                  <v-list-item-title class="text-caption text-grey-darken-1">
                    &lt;&lt; 나 &gt;&gt;
                  </v-list-item-title>
                </v-list-item>
                <v-list-item
                  v-for="member in assignableMembers"
                  :key="member.pk"
                  :active="getAssigneePk(issue.assigned_to) === member.user_id"
                  min-height="30px"
                  min-width="150px"
                  class="py-0"
                  @click="changeAssignee(member.user_id)"
                >
                  <v-list-item-title class="text-caption">{{ member.username }}</v-list-item-title>
                </v-list-item>
                <v-list-item
                  :active="getAssigneePk(issue.assigned_to) === null"
                  min-height="30px"
                  min-width="150px"
                  class="py-0"
                  @click="changeAssignee(null)"
                >
                  <v-list-item-title class="text-caption text-grey-darken-1">
                    미지정
                  </v-list-item-title>
                </v-list-item>
              </template>
            </v-list>
          </v-menu>

          <v-menu v-if="canEditIssue" open-on-hover location="end" offset="5">
            <template v-slot:activator="{ props: menuProps }">
              <v-list-item
                v-bind="menuProps"
                append-icon="mdi-chevron-right"
                min-height="28px"
                class="py-0"
              >
                <template v-slot:prepend>
                  <v-icon icon="mdi-percent-outline" color="orange" size="small" class="mr-n2" />
                </template>
                <v-list-item-title class="text-caption">진척도</v-list-item-title>
              </v-list-item>
            </template>
            <v-list density="compact" class="py-1">
              <v-list-item
                v-for="ratio in progressOptions"
                :key="ratio"
                :active="issue.done_ratio === ratio"
                min-height="30px"
                min-width="100px"
                class="py-0"
                @click="changeProgress(ratio)"
              >
                <v-list-item-title class="text-caption">{{ ratio }}%</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>

          <v-menu
            v-if="canEditIssue"
            open-on-hover
            location="end"
            offset="5"
            @update:model-value="fetchMembersOnDemand"
          >
            <template v-slot:activator="{ props: menuProps }">
              <v-list-item
                v-bind="menuProps"
                append-icon="mdi-chevron-right"
                min-height="28px"
                class="py-0"
              >
                <template v-slot:prepend>
                  <v-icon icon="mdi-eye-outline" color="purple" size="small" class="mr-n2" />
                </template>
                <v-list-item-title class="text-caption">업무 관람자</v-list-item-title>
              </v-list-item>
            </template>
            <v-list density="compact" class="py-1">
              <v-list-item v-if="loadingMembers" min-height="30px" class="py-0" disabled>
                <v-list-item-title class="text-caption text-grey">로딩 중...</v-list-item-title>
              </v-list-item>
              <template v-else>
                <v-list-item
                  v-for="member in members"
                  :key="member.pk"
                  :active="isWatcherMember(member.user_id)"
                  min-height="30px"
                  min-width="150px"
                  class="py-0"
                  @click="toggleWatcher(member.user_id)"
                >
                  <template v-slot:prepend>
                    <v-icon
                      :icon="
                        isWatcherMember(member.user_id)
                          ? 'mdi-checkbox-marked'
                          : 'mdi-checkbox-blank-outline'
                      "
                      :color="isWatcherMember(member.user_id) ? 'purple' : 'grey'"
                      size="x-small"
                      class="mr-2"
                    />
                  </template>
                  <v-list-item-title class="text-caption">{{ member.username }}</v-list-item-title>
                </v-list-item>
              </template>
            </v-list>
          </v-menu>

          <v-list-item @click="watchControl" min-height="28px" class="py-0">
            <template v-slot:prepend>
              <v-icon
                icon="mdi-star"
                :color="isWatcher ? 'amber' : 'secondary'"
                size="small"
                class="mr-n2"
              />
            </template>
            <v-list-item-title class="text-caption">
              {{ isWatcher ? '관심끄기' : '지켜보기' }}
            </v-list-item-title>
          </v-list-item>

          <v-list-item
            v-if="canCreateSubIssue"
            min-height="28px"
            class="py-0"
            @click="
              router.push({
                name: '(업무) - 추가',
                params: { projId: issue.project.slug },
                query: { parent: issue.pk, tracker: issue.tracker.pk },
              })
            "
          >
            <template v-slot:prepend>
              <v-icon icon="mdi-plus-circle" color="success" size="small" class="mr-n2" />
            </template>
            <v-list-item-title class="text-caption">하위 업무 추가</v-list-item-title>
          </v-list-item>

          <v-list-item min-height="28px" class="py-0" @click="issueLinkCopy">
            <template v-slot:prepend>
              <v-icon icon="mdi-link-variant" color="secondary" size="small" class="mr-n2" />
            </template>
            <v-list-item-title class="text-caption">링크복사</v-list-item-title>
          </v-list-item>

          <v-list-item v-if="showCopyButton" min-height="28px" class="py-0" @click="copyIssue">
            <template v-slot:prepend>
              <v-icon icon="mdi-content-copy" color="secondary" size="small" class="mr-n2" />
            </template>
            <v-list-item-title class="text-caption">복사</v-list-item-title>
          </v-list-item>

          <v-list-item v-if="showDeleteButton" min-height="28px" class="py-0" @click="deleteIssue">
            <template v-slot:prepend>
              <v-icon icon="mdi-trash-can-outline" color="secondary" size="small" class="mr-n2" />
            </template>
            <v-list-item-title class="text-caption">업무 삭제</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
    </v-btn>
  </span>

  <ConfirmModal ref="refDelModal">
    <template #footer>
      <v-btn size="small" color="warning" @click="confirmDelete">삭제</v-btn>
    </template>
  </ConfirmModal>
</template>
