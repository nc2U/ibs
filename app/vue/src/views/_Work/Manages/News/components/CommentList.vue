<script lang="ts" setup>
import { computed, ref } from 'vue'
import { usePerms } from '@/composables/usePerms'
import { useInform } from '@/store/pinia/work_inform'
import { useAccount } from '@/store/pinia/account'
import { useWork } from '@/store/pinia/work_project'
import type { News, NewsComment } from '@/store/types/work_inform'
import Comment from './Comment.vue'

const accStore = useAccount()
const workStore = useWork()
const userInfo = computed(() => accStore.userInfo)

const { can, PERM } = usePerms()

const infStore = useInform()
const news = computed(() => infStore.news as News | null)
const canComment = computed(
  () =>
    workStore.currentProject?.status === '1' && can(PERM.NEWS_COMMENT, news.value?.project?.slug),
)

const commentContent = ref('')
const submitting = ref(false)

const onSubmit = async () => {
  if (submitting.value || !commentContent.value.trim() || !news.value?.pk) return

  const payload: NewsComment = {
    news: news.value.pk,
    content: commentContent.value,
    parent: null,
    created: '',
    updated: '',
  }

  submitting.value = true
  try {
    const ok = await infStore.createNewsComment(payload)
    if (ok) commentContent.value = ''
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="comment-list-container">
    <!-- Comment Input -->
    <div v-if="canComment" class="comment-form mb-6">
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
            class="ms-2"
            :disabled="submitting || !commentContent.trim() || !userInfo"
            :loading="submitting"
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
    <div v-else class="text-center py-6 text-medium-emphasis fst-italic small">
      {{
        canComment
          ? '아직 댓글이 없습니다. 첫 번째 댓글을 남겨보세요!'
          : '아직 등록된 댓글이 없습니다.'
      }}
    </div>
  </div>
</template>

<style scoped>
.comment-form :deep(.v-field__append-inner) {
  align-items: center;
  padding-bottom: 8px;
}
</style>
