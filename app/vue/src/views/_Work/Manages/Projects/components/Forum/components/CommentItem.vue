<script lang="ts" setup>
import { computed, type PropType, ref } from 'vue'
import { useAccount } from '@/store/pinia/account.ts'
import type { Comment } from '@/store/types/forum'
import { elapsedTime, timeFormat } from '@/utils/baseMixins'
import { usePerms } from '@/composables/usePerms.ts'
import { markdownRender } from '@/utils/helper'
import CommentForm from './CommentForm.vue'

const props = defineProps({
  comment: { type: Object as PropType<Comment>, required: true },
})

const emit = defineEmits(['submit-comment', 'delete-comment'])

const accStore = useAccount()
const userInfo = computed(() => accStore.userInfo)

const { can, PERM } = usePerms()
const canCommentCreate = computed(() => can(PERM.FORUM_CREATE))
const canCommentUpdate = computed(() => {
  if (can(PERM.FORUM_UPDATE)) return true
  else if (can(PERM.FORUM_OWN_UPDATE) && userInfo.value?.pk === props.comment.creator?.pk)
    return true
  else return false
})
const canCommentDelete = computed(() => {
  if (can(PERM.FORUM_DELETE)) return true
  else if (can(PERM.FORUM_OWN_DELETE) && userInfo.value?.pk === props.comment.creator?.pk)
    return true
  else return false
})

const showReplyForm = ref(false)
const showEditForm = ref(false)

const onReply = (content: string) => {
  emit('submit-comment', { content, parent: props.comment.pk })
  showReplyForm.value = false
}

const onEdit = (content: string) => {
  emit('submit-comment', { pk: props.comment.pk, content })
  showEditForm.value = false
}
</script>

<template>
  <div class="comment-item mb-3">
    <CCard class="border-light shadow-sm">
      <CCardBody class="py-2">
        <div class="d-flex justify-content-between align-items-center mb-2">
          <div class="text-body-2">
            <span class="fw-bold mr-2">{{ comment.creator?.username }}</span>
            <span class="text-muted">{{ elapsedTime(comment.created as string) }}</span>
            <v-tooltip activator="parent" location="top">
              {{ timeFormat(comment.created as string) }}
            </v-tooltip>
          </div>
          <div class="actions">
            <v-btn
              v-if="!comment.parent"
              variant="text"
              size="small"
              color="primary"
              :disabled="!canCommentCreate"
              @click="showReplyForm = !showReplyForm"
            >
              답글
            </v-btn>
            <template v-if="userInfo?.pk === comment.creator?.pk">
              <v-btn
                variant="text"
                size="small"
                color="success"
                :disabled="!canCommentUpdate"
                @click="showEditForm = !showEditForm"
              >
                수정
              </v-btn>
              <v-btn
                variant="text"
                size="small"
                color="danger"
                :disabled="!canCommentDelete"
                @click="emit('delete-comment', comment.pk)"
              >
                삭제
              </v-btn>
            </template>
          </div>
        </div>

        <div
          v-if="!showEditForm"
          v-html="markdownRender(comment.content)"
          class="comment-content"
        />
        <CommentForm
          v-else
          :content="comment.content"
          @submit-comment="onEdit"
          @cancel="showEditForm = false"
        />

        <div v-if="showReplyForm" class="mt-3">
          <CommentForm @submit-comment="onReply" @cancel="showReplyForm = false" />
        </div>
      </CCardBody>
    </CCard>

    <!-- Recursive rendering for replies -->
    <div v-if="comment.replies?.length" class="replies-list ml-5 mt-2 border-left pl-3">
      <CommentItem
        v-for="reply in comment.replies"
        :key="reply.pk"
        :comment="reply"
        @submit-comment="emit('submit-comment', $event)"
        @delete-comment="emit('delete-comment', $event)"
      />
    </div>
  </div>
</template>

<style lang="scss" scoped>
.comment-content {
  font-size: 0.95rem;
}
.replies-list {
  border-left: 2px solid #e9ecef;
}
</style>
