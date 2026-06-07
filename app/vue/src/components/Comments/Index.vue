<script lang="ts" setup>
import { ref, type PropType } from 'vue'
import { useForum } from '@/store/pinia/forum'
import type { Comment } from '@/store/types/forum'
import CommentList from './components/CommentList.vue'
import CommentForm from './components/CommentForm.vue'

const props = defineProps({
  post: { type: Number, required: true },
  isHide: { type: Boolean, default: false },
  comments: { type: Array as PropType<Comment[]>, default: () => [] },
})

const formVision = ref<boolean>(true)
const actForm = ref<number | undefined>(undefined)

const forumStore = useForum()
const createComment = (payload: Comment) => forumStore.createComment(payload)
const patchComment = (payload: Comment) => forumStore.patchComment(payload)
const patchCommentLike = (pk: number, post: number, page?: number) =>
  forumStore.patchCommentLike(pk, post, page)

const toLike = (pk: number) => patchCommentLike(pk, props.post)

const onSubmit = (payload: Comment) => {
  console.log(payload)
  if (!payload?.pk) createComment(payload)
  else patchComment(payload)
}

const formReset = () => {
  formVision.value = true
  actForm.value = undefined
}

const visionToggle = (payload: { num: number; sts: boolean }) => {
  formVision.value = payload.sts
  if (!payload.sts) actForm.value = payload.num
}

const pageSelect = (page: number) => forumStore.fetchCommentList({ post: props.post, page })
</script>

<template>
  <div v-show="!isHide">
    <CommentList
      :act-form="actForm"
      :comments="comments"
      @vision-toggle="visionToggle"
      @to-like="toLike"
      @on-submit="onSubmit"
      @form-reset="formReset"
      @page-select="pageSelect"
    />
    <div v-show="formVision" class="pt-1">
      <CommentForm :form-vision="formVision" :post="post" @on-submit="onSubmit" />
    </div>

    <v-divider />
  </div>
</template>
