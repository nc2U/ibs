<script lang="ts" setup>
import { computed, inject, ref } from 'vue'
import { useInform } from '@/store/pinia/work_inform.ts'
import type { News } from '@/store/types/work_inform.ts'
import Comment from './Comment.vue'

const userInfo = inject<any>('userInfo')

const infStore = useInform()
const news = computed(() => infStore.news as News | null)

const commentContent = ref('')

const onSubmit = () => {
  if (!commentContent.value.trim()) return

  const payload: any = {
    news: news.value?.pk,
    content: commentContent.value,
    parent: null,
  }

  infStore.createNewsComment(payload)
  commentContent.value = ''
}
</script>

<template>
  <div class="comment-list-container">
    <!-- Comment Input -->
    <div class="comment-form mb-6">
      <v-textarea
        v-model="commentContent"
        :placeholder="userInfo ? '댓글을 입력하세요...' : '댓글을 작성하려면 로그인이 필요합니다.'"
        :disabled="!userInfo"
        variant="outlined"
        density="comfortable"
        rows="2"
        auto-grow
        hide-details
      >
        <template #append-inner>
          <v-btn
            color="primary"
            variant="flat"
            size="small"
            class="ml-2"
            :disabled="!commentContent.trim() || !userInfo"
            @click="onSubmit"
          >
            등록
          </v-btn>
        </template>
      </v-textarea>
    </div>

    <!-- Comments Display -->
    <div v-if="news && news.comments && news.comments.length" class="comments-wrapper">
      <Comment v-for="comment in news.comments" :key="comment.pk" :comment="comment" />
    </div>
    <div v-else class="text-center py-6 text-grey-lighten-1 italic small">
      아직 댓글이 없습니다. 첫 번째 댓글을 남겨보세요!
    </div>
  </div>
</template>

<style scoped>
.comment-form :deep(.v-field__append-inner) {
  align-items: center;
  padding-bottom: 8px;
}
</style>
