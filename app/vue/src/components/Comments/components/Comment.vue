<script lang="ts" setup>
import { computed, type PropType, ref, watch } from 'vue'
import { useAccount } from '@/store/pinia/account.ts'
import { elapsedTime } from '@/utils/baseMixins'
import { usePerms } from '@/composables/usePerms.ts'
import type { Comment as Cm } from '@/store/types/forum'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import CommentForm from './CommentForm.vue'

const props = defineProps({
  formShow: { type: Boolean, default: true }, // 현재 댓글과 편집 폼 댓글이 동일한지 여부
  comment: { type: Object as PropType<Cm>, default: null },
  lastDepth: { type: Boolean, default: false },
})

watch(props, val => {
  if (!val.formShow) {
    // 현재 편집폼이 아니면 초기화
    isReplying.value = false
    isEditing.value = false
  }
})

const emit = defineEmits(['vision-toggle', 'to-like', 'to-blame', 'on-submit', 'on-delete'])

const refBlameModal = ref()
const refDeleteModal = ref()

const accStore = useAccount()
const userInfo = computed(() => accStore.userInfo)

const isReplying = ref<boolean>(false)
const isEditing = ref<boolean>(false)

const toLike = () => emit('to-like', props.comment.pk, props.comment?.post.pk)

const blameConfirm = () => refBlameModal.value.callModal()

const blameAction = () => {
  refBlameModal.value.close()
  emit('to-blame', props.comment.pk as number, props.comment?.post.pk)
}

const toReply = () => {
  isEditing.value = false
  isReplying.value = !isReplying.value
  emit('vision-toggle', { num: props.comment?.pk as number, sts: !isReplying.value })
}

const toModify = () => {
  isReplying.value = false
  isEditing.value = !isEditing.value
  emit('vision-toggle', { num: props.comment?.pk as number, sts: !isEditing.value })
}

const { can, canViewUser, PERM } = usePerms()
const canCommentUpdate = computed(() => {
  if (can(PERM.FORUM_UPDATE)) return true
  else if (can(PERM.FORUM_OWN_UPDATE) && userInfo.value?.pk === props.comment?.creator?.pk)
    return true
  else return false
})
const canCommentDelete = computed(() => {
  if (can(PERM.FORUM_DELETE)) return true
  else if (can(PERM.FORUM_OWN_DELETE) && userInfo.value?.pk === props.comment?.creator?.pk)
    return true
  else return false
})

const toDelete = () => refDeleteModal.value.callModal()
const deleteComment = () => emit('on-delete', props.comment?.pk, props.comment?.post.pk)

const onSubmit = (payload: Cm) => emit('on-submit', payload)
</script>

<template>
  <li class="text-muted" :id="`comment_${comment.pk}`">
    <strong>
      <router-link
        v-if="canViewUser(userInfo?.pk)"
        :to="{ name: '사용자 - 보기', params: { userId: comment?.creator?.pk } }"
        class="text-decoration-none text-muted"
      >
        {{ comment?.creator?.username }}
      </router-link>
      <span v-else>{{ comment?.creator?.username }}</span>
    </strong>
    <small class="ml-2">
      <v-icon icon="mdi-clock-time-four-outline" size="sm" />
      {{ elapsedTime(comment?.created ?? '') }}
    </small>
    <small class="ml-3 text-btn" @click="toLike">
      <v-icon
        :icon="comment.my_like ? 'mdi-heart' : 'mdi-heart-outline'"
        size="sm"
        class="icon-btn"
      />
      <v-tooltip activator="parent" location="top">
        {{ !comment.my_like ? '좋아요' : '취소' }}
      </v-tooltip>
      {{ comment?.like ?? 0 }}
    </small>

    <small class="ml-3 text-btn" @click="blameConfirm">
      <v-icon
        :icon="comment.my_blame ? 'mdi-bell' : 'mdi-bell-outline'"
        size="xs"
        class="icon-btn"
      />
      <!--      신고-->
      <v-tooltip activator="parent" location="top">
        {{ !comment.my_blame ? '신고' : '취소' }}
      </v-tooltip>
      {{ comment.blame ?? 0 }}
    </small>

    <small v-if="!lastDepth" class="ml-3 text-btn" @click="toReply">
      {{ !isReplying ? '답글' : '취소' }}
    </small>
    <template v-if="!comment.replies?.length && (canCommentUpdate || canCommentDelete)">
      <!--    해당 작성글/관리자 권한이고 댓글에 대댓글이 없을 경우 수정/삭제 활성-->
      <small v-if="canCommentUpdate" class="ml-1 text-btn" @click="toModify">
        {{ !isEditing ? '수정' : '취소' }}
      </small>
      <small v-if="canCommentDelete" class="ml-1 text-btn" @click="toDelete">삭제</small>
    </template>

    <p v-if="!(formShow && isEditing)" class="mt-1 p-1">
      <CBadge v-if="comment.secret" color="danger" class="mr-2">비밀글입니다</CBadge>
      <span
        v-show="
          !comment.secret ||
          userInfo?.is_superuser ||
          userInfo?.pk === comment.creator?.pk ||
          canCommentUpdate
        "
      >
        {{ comment?.content }}
      </span>
    </p>
    <p v-if="formShow && isEditing">
      <!-- 수정시 -->
      <CommentForm :post="comment?.post.pk as number" :comment="comment" @on-submit="onSubmit" />
    </p>
    <p v-if="formShow && isReplying">
      <!-- 답글시 -->
      <CommentForm
        :post="comment?.post.pk as number"
        :parent="comment?.pk as number"
        @on-submit="onSubmit"
      />
    </p>
  </li>

  <ConfirmModal ref="refBlameModal">
    <template #header>알림</template>
    <template #default>
      이 댓글을 신고 {{ comment.my_blame ? '를 취소' : '' }} 하시겠습니까?
    </template>
    <template #footer>
      <v-btn size="small" :color="comment.my_blame ? 'secondary' : 'warning'" @click="blameAction">
        {{ comment.my_blame ? '취소' : '신고' }}
      </v-btn>
    </template>
  </ConfirmModal>

  <ConfirmModal ref="refDeleteModal">
    <template #header>알림</template>
    <template #default> 이 댓글을 삭제하시겠습니까? </template>
    <template #footer>
      <v-btn color="warning" size="small" @click="deleteComment"> 삭제 </v-btn>
    </template>
  </ConfirmModal>
</template>

<style lang="scss" scoped>
li {
  list-style-type: none;
}
</style>
