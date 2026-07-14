<script lang="ts" setup>
import { computed, type PropType, ref } from 'vue'
import type { IssueLogEntry } from '@/store/types/work_logging.ts'
import { useRoute } from 'vue-router'
import { usePerms } from '@/composables/usePerms'
import { markdownRender, message } from '@/utils/helper.ts'
import { elapsedTime, timeFormat } from '@/utils/baseMixins'
import { useAccount } from '@/store/pinia/account.ts'
import { useIssue } from '@/store/pinia/work_issue.ts'
import MdEditor from '@/components/MdEditor/Index.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

const props = defineProps({ log: { type: Object as PropType<IssueLogEntry>, required: true } })

const emit = defineEmits(['del-submit', 'call-reply'])

const RefDelConfirm = ref()
const delPk = ref<null | number>(null)

const route = useRoute()

const { can, canViewUser, PERM } = usePerms()

const accStore = useAccount()
const userInfo = computed(() => accStore.userInfo)

const callReply = (log_id: number, user: string, content: string) => {
  return emit('call-reply', {
    id: log_id,
    user,
    content,
  })
}

const editMode = ref(false)
const content = ref('')
const isPrivate = ref(false)

const isLockedByAdmin = computed(
  () => !can(PERM.ISSUE_PRIVATE_COMMENT_SET) && !!props.log.comment?.is_blocked,
)

const toEdit = (commentVal: string) => {
  editMode.value = !editMode.value
  content.value = commentVal
  isPrivate.value = !!props.log.comment?.is_private
}

const issueStore = useIssue()
const commentSubmit = () => {
  const pk = props.log?.comment?.pk
  const issue = props.log?.issue?.pk
  issueStore.patchIssueComment({
    pk,
    issue,
    content: content.value,
    is_private: isPrivate.value,
  })
  editMode.value = false
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
    message('success', '복사 완료', '댓글 링크가 클립보드에 복사되었습니다.')
  } catch (err) {
    message('danger', '오류!', '댓글 링크 복사에 실패했습니다.')
  }
  document.body.removeChild(textArea)
}

const copyLink = (path: string, hash: string) => {
  const url = window.location.origin + '/#' + path + hash
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard
      .writeText(url)
      .then(() => {
        message('success', '복사 완료', '댓글 링크가 클립보드에 복사되었습니다.')
      })
      .catch(() => fallbackCopy(url))
  } else {
    fallbackCopy(url)
  }
}

const delConfirm = (pk: number) => {
  delPk.value = pk
  RefDelConfirm.value.callModal('삭제 확인', '계속 진행하시겠습니까?', '', 'warning')
}

const delSubmit = () => {
  emit('del-submit', delPk.value)
  delPk.value = null
  RefDelConfirm.value.close()
}
</script>

<template>
  <CRow>
    <CCol>
      <CRow
        :id="`note-${log.pk}`"
        :class="{ 'bg-blue-lighten-5': route.hash == `#note-${log.log_id}` }"
      >
        <CCol v-if="log.creator" class="pt-1">
          <router-link
            v-if="canViewUser(log.creator.pk)"
            :to="{ name: '사용자 - 보기', params: { userId: log.creator.pk } }"
          >
            {{ log.creator.username }}
          </router-link>
          <span v-else>{{ log.creator.username }}</span>
          이(가)
          <span>
            <router-link
              :to="{
                name: '(업무실행내역)',
                params: { projId: route.params.projId },
                query: { from: log.timestamp.substring(0, 10) },
              }"
            >
              {{ elapsedTime(log.timestamp) }}
            </router-link>
            <v-tooltip activator="parent" location="top">{{ timeFormat(log.timestamp) }}</v-tooltip>
          </span>
          에 변경
          <v-icon
            v-if="log.comment?.is_private"
            icon="mdi-lock"
            color="warning"
            size="14"
            class="ml-1 align-middle"
          />
          <v-tooltip activator="parent" location="top"> 비공개 댓글 </v-tooltip>
        </CCol>
        <CCol class="text-right">
          <span v-if="can(PERM.ISSUE_COMMENT_CREATE)">
            <v-icon
              icon="mdi-comment-processing-outline"
              color="info"
              size="16"
              class="mr-2 pointer"
              @click="
                callReply(
                  log.log_id,
                  log.comment?.creator.username ?? '',
                  log.comment?.content ?? '',
                )
              "
            />
            <v-tooltip activator="parent" location="top">댓글달기</v-tooltip>
          </span>
          <span
            v-if="
              can(PERM.ISSUE_COMMENT_UPDATE) ||
              (can(PERM.ISSUE_COMMENT_OWN_UPDATE) && userInfo?.pk === log.comment?.creator.pk)
            "
          >
            <v-icon
              icon="mdi-pencil"
              color="amber"
              size="16"
              class="mr-1 pointer"
              @click="toEdit(log.comment?.content ?? '')"
            />
            <v-tooltip activator="parent" location="top">편집</v-tooltip>
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
                <CDropdownItem
                  class="form-text"
                  @click="copyLink(route.path, `#note-${log.log_id}`)"
                >
                  <router-link to="">
                    <v-icon icon="mdi-pencil" color="amber" size="sm" />
                    링크 복사
                  </router-link>
                </CDropdownItem>
                <CDropdownItem
                  v-if="
                    can(PERM.ISSUE_COMMENT_UPDATE) ||
                    (can(PERM.ISSUE_COMMENT_OWN_UPDATE) && userInfo?.pk === log.comment?.creator.pk)
                  "
                  class="form-text"
                  @click="delConfirm(log.comment?.pk as number)"
                >
                  <router-link to="">
                    <v-icon icon="mdi-trash-can" color="grey" size="sm" />
                    삭제
                  </router-link>
                </CDropdownItem>
              </CDropdownMenu>
            </CDropdown>
          </span>

          <router-link :to="{ hash: '#note-' + log.log_id }">#{{ log.log_id }}</router-link>
        </CCol>
      </CRow>
      <v-divider class="mt-0 mb-2" />
      <div class="history pl-0 text-body">
        <div v-if="!editMode" v-html="markdownRender(log.comment?.content + '\n' || '\n')" />
        <span v-else>
          <MdEditor v-model="content" style="height: 150px" class="mb-1" placeholder="Comment.." />
          <CFormCheck
            v-model="isPrivate"
            id="private_comment"
            inline
            label="비공개 댓글"
            :disabled="isLockedByAdmin"
          />

          <span v-if="isLockedByAdmin" class="text-danger small inline">
            관리자에 의해 비공개로 전환된 댓글입니다. 설정을 변경할 수 없습니다.
          </span>
          <div class="my-3">
            <v-btn color="success" size="small" @click="commentSubmit" :disabled="isLockedByAdmin">
              저장
            </v-btn>
            <v-btn color="light" size="small" @click="() => (editMode = false)" flat>취소</v-btn>
          </div>
        </span>
      </div>

      <ConfirmModal ref="RefDelConfirm">
        <template #footer>
          <v-btn color="warning" @click="delSubmit">확인</v-btn>
        </template>
      </ConfirmModal>
    </CCol>
  </CRow>
</template>
