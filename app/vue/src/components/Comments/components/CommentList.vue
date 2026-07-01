<script lang="ts" setup>
import { ref, computed, type PropType } from 'vue'
import { useForum } from '@/store/pinia/forum'
import type { Comment as Cm } from '@/store/types/forum'
import { toCommentLike, toCommentBlame } from '@/utils/postMixins'
import Pagination from '@/components/Pagination'
import Comment from './Comment.vue'

defineProps({
  actForm: { type: Number, default: undefined },
  comments: { type: Array as PropType<Cm[]>, default: () => [] },
})
const emit = defineEmits(['vision-toggle', 'on-submit', 'form-reset', 'page-select', 'on-delete'])

const page = ref(1)

const forumStore = useForum()
const commentCount = computed(() => forumStore.commentCount)

const visionToggle = (payload: { num: number; sts: boolean }) => emit('vision-toggle', payload)

const toLike = (pk: number, post: number) => toCommentLike(pk, post, page.value)

const toBlame = (pk: number, post: number) => toCommentBlame(pk, post, page.value)

const onDelete = (pk: number, post: number) => emit('on-delete', pk, post)

const onSubmit = (payload: Cm) => {
  emit('on-submit', payload)
  emit('form-reset')
}

const pageSelect = (p: number) => {
  page.value = p
  emit('page-select', p)
}

const itemsPerPage = ref(10)
const commentPages = (pages: number) => Math.ceil(commentCount.value / pages)
</script>

<template>
  <div v-if="commentCount">
    <h5 class="mt-5 ml-4">댓글 ({{ commentCount }})</h5>
    <v-divider class="mb-4 mx-3" />
    <ul v-for="cmt1 in comments" :key="cmt1.pk" class="comments ml-4 mb-3">
      <Comment
        :form-show="actForm === cmt1.pk"
        :comment="cmt1"
        @vision-toggle="visionToggle"
        @to-like="toLike"
        @to-blame="toBlame"
        @on-submit="onSubmit"
        @on-delete="onDelete"
      />

      <ul v-for="cmt2 in cmt1.replies" :key="cmt2.pk" class="comments ml-4 mb-3">
        <Comment
          :form-show="actForm === cmt2.pk"
          :comment="cmt2"
          @vision-toggle="visionToggle"
          @to-like="toLike"
          @to-blame="toBlame"
          @on-submit="onSubmit"
          @on-delete="onDelete"
        />

        <ul v-for="cmt3 in cmt2.replies" :key="cmt3.pk" class="comments ml-4 mb-3">
          <Comment
            :form-show="actForm === cmt3.pk"
            :comment="cmt3"
            @vision-toggle="visionToggle"
            @to-like="toLike"
            @to-blame="toBlame"
            @on-submit="onSubmit"
            @on-delete="onDelete"
          />

          <ul v-for="cmt4 in cmt3.replies" :key="cmt4.pk" class="comments ml-4 mb-3">
            <Comment
              :form-show="actForm === cmt4.pk"
              :comment="cmt4"
              @vision-toggle="visionToggle"
              @to-like="toLike"
              @to-blame="toBlame"
              @on-submit="onSubmit"
              @on-delete="onDelete"
            />
            <ul v-for="cmt5 in cmt4.replies" :key="cmt5.pk" class="comments ml-4 mb-3">
              <Comment
                :form-show="actForm === cmt5.pk"
                :comment="cmt5"
                :last-depth="true"
                @vision-toggle="visionToggle"
                @to-like="toLike"
                @to-blame="toBlame"
                @on-submit="onSubmit"
                @on-delete="onDelete"
              />
            </ul>
          </ul>
        </ul>
      </ul>
    </ul>

    <div v-if="commentCount > itemsPerPage">
      <Pagination
        :active-page="1"
        :limit="8"
        :pages="commentPages(itemsPerPage)"
        class="mt-3"
        align="end"
        @active-page-change="pageSelect"
      />
    </div>
  </div>
</template>
