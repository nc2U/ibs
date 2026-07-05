<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from '@/utils/helper.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { useAccount } from '@/store/pinia/account.ts'
import type { Issue } from '@/store/types/work_issue.ts'
import TextButton from '@/views/_Work/components/atomics/TextButton.vue'

const props = defineProps({
  projStatus: { type: String, default: '' },
  watchers: {
    type: Array as PropType<{ pk: number; username: string }[]>,
    default: () => [],
  },
  issue: {
    type: Object as PropType<Issue>,
    required: true,
  },
})

const emit = defineEmits(['call-edit-form', 'watch-control', 'call-delete-issue'])

const route = useRoute()
const router = useRouter()

const accStore = useAccount()
const userInfo = computed(() => accStore.userInfo)

const { can, PERM } = usePerms()

// 1. 본인이 생성자인지 여부
const isCreator = computed(() => props.issue.creator?.pk === userInfo.value?.pk)

// 2. 본인이 담당자인지 여부
const isAssignee = computed(() => props.issue.assigned_to?.pk === userInfo.value?.pk)

// 3. 일감 수정 권한
const canEditIssue = computed(() => {
  if (can(PERM.ISSUE_UPDATE)) return true
  return can(PERM.ISSUE_OWN_UPDATE) && (isCreator.value || isAssignee.value)
})

// 4. 댓글 작성 권한
const canCreateComment = computed(() => can(PERM.ISSUE_COMMENT_CREATE))

// 5. 편집 버튼 노출 조건 (일감을 편집할 수 있거나 댓글을 달 수 있다면 활성화)
const showEditButton = computed(() => canEditIssue.value || canCreateComment.value)

// 6. 복사 버튼 노출 조건
const showCopyButton = computed(() => can(PERM.ISSUE_COPY) && props.projStatus !== '9')

// 7. 삭제 버튼 노출 조건
const showDeleteButton = computed(() => can(PERM.ISSUE_DELETE) && props.projStatus !== '9')

const isWatcher = computed(() =>
  (props.watchers || []).map(w => w.pk).includes(userInfo?.value?.pk as number),
)

const watchControl = () => emit('watch-control')

const copyIssue = () => {
  const routeName = route.params.projId ? '(업무) - 추가' : '업무 - 추가'
  router.push({
    name: routeName,
    query: { copy: props.issue.pk },
  })
}

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
  const url = window.location.href
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard
      .writeText(url)
      .then(() => {
        message('success', '복사 완료', '업무 상세 링크가 클립보드에 복사되었습니다.')
      })
      .catch(() => fallbackCopy(url))
  } else fallbackCopy(url)
}

const callEditForm = () => emit('call-edit-form')
const callDeleteIssue = () => emit('call-delete-issue')
</script>

<template>
  <CCol class="text-right form-text">
    <span v-if="projStatus !== '9' && showEditButton">
      <TextButton name="편집" icon="mdi-pencil" icon-color="amber" @click="callEditForm" />
    </span>

    <span>
      <TextButton
        :name="isWatcher ? '관심끄기' : '지켜보기'"
        icon="mdi-star"
        :icon-color="isWatcher ? 'amber' : 'secondary'"
        @click="watchControl"
      />
    </span>

    <span v-if="showCopyButton">
      <TextButton name="복사" icon="mdi-content-copy" icon-color="grey" @click="copyIssue" />
    </span>

    <span>
      <CDropdown color="secondary" variant="input-group" placement="bottom-end">
        <CDropdownToggle
          :caret="false"
          color="light"
          variant="ghost"
          size="sm"
          shape="rounded-pill"
        >
          <v-icon icon="mdi-dots-horizontal" class="pointer" color="grey-darken-1" />
          <v-tooltip activator="parent" location="top">Actions</v-tooltip>
        </CDropdownToggle>
        <CDropdownMenu>
          <CDropdownItem class="form-text" @click="issueLinkCopy">
            <router-link to="">
              <v-icon icon="mdi-link-plus" color="grey" size="sm" />
              링크 복사
            </router-link>
          </CDropdownItem>
          <CDropdownItem v-if="showDeleteButton" class="form-text" @click="callDeleteIssue">
            <router-link to="">
              <v-icon icon="mdi-trash-can-outline" color="grey" size="sm" />
              업무 삭제
            </router-link>
          </CDropdownItem>
        </CDropdownMenu>
      </CDropdown>
    </span>
  </CCol>
</template>
