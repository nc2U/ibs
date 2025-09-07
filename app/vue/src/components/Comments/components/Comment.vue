<script lang="ts" setup>
import { ref, watch, inject, type ComputedRef, type PropType } from 'vue'
import { elapsedTime } from '@/utils/baseMixins'
import type { User } from '@/store/types/accounts'
import type { Comment as Cm } from '@/store/types/board'
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

const emit = defineEmits(['vision-toggle', 'to-like', 'to-blame', 'on-submit'])

const refBlameModal = ref()

const userInfo = inject<ComputedRef<User>>('userInfo')

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

const toDelete = () => alert('delete')

const onSubmit = (payload: Cm) => emit('on-submit', payload)
</script>

<template>
  <li class="text-50" :id="`comment_${comment.pk}`">
    <strong>{{ comment?.creator?.username }}</strong>
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
      {{ !isReplying ? '답변' : '취소' }}
    </small>
    <template v-if="!comment.replies?.length && userInfo?.pk === props.comment?.creator?.pk">
      <!--    해당 본인 작성글이고 댓글에 대댓글이 없을 경우 수정/삭제 활성-->
      <small class="ml-1 text-btn" @click="toModify">
        {{ !isEditing ? '수정' : '취소' }}
      </small>
      <small class="ml-1 text-btn" @click="toDelete">삭제</small>
    </template>

    <p v-if="!(formShow && isEditing)">
      <CBadge v-if="comment.secret" color="warning" class="mr-1">비밀글입니다</CBadge>
      <span
        v-show="!comment.secret || userInfo?.is_superuser || userInfo?.pk === comment.creator?.pk"
      >
        {{ comment?.content }}
      </span>
    </p>
    <p v-if="formShow && isEditing">
      <!-- 수정시 -->
      <CommentForm :post="comment?.post.pk as number" :comment="comment" @on-submit="onSubmit" />
    </p>
    <p v-if="formShow && isReplying">
      <!-- 답변시 -->
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
      이 댓글을 신고 {{ comment.my_blame ? '를 취소' : '' }} 하시겠습니까?<br /><br />
    </template>
    <template #footer>
      <v-btn :color="comment.my_blame ? 'secondary' : 'warning'" @click="blameAction">
        {{ comment.my_blame ? '취소' : '신고' }}
      </v-btn>
    </template>
  </ConfirmModal>
</template>

<style lang="scss" scoped>
li {
  list-style-type: none;
}
</style>
