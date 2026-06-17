<script lang="ts" setup>
import { computed, ref } from 'vue'
import { useInform } from '@/store/pinia/work_inform.ts'
import type { News } from '@/store/types/work_inform.ts'
import Comment from './Comment.vue'

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
        placeholder="댓글을 입력하세요..."
        variant="outlined"
        density="comfortable"
        rows="2"
        auto-grow
        hide-details
        class="bg-white rounded-lg"
      >
        <template #append-inner>
          <v-btn
            color="primary"
            variant="flat"
            size="small"
            class="ml-2"
            :disabled="!commentContent.trim()"
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
