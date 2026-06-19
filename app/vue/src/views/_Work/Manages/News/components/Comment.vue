<script lang="ts" setup>
import type { PropType } from 'vue'
import type { BaseComment } from '@/store/types/work_inform.ts'
import { elapsedTime } from '@/utils/baseMixins.ts'

defineProps({
  comment: { type: Object as PropType<BaseComment>, required: true },
})
</script>

<template>
  <div class="comment-item mb-4">
    <div class="d-flex">
      <v-avatar size="32" color="primary-lighten-4" class="mr-3">
        <v-icon icon="mdi-account" color="primary" size="20" />
      </v-avatar>
      <div class="flex-grow-1">
        <v-card variant="flat" border class="pa-3 rounded-lg card-deep">
          <div class="d-flex justify-space-between align-center mb-1">
            <router-link
              :to="{ name: '사용자 - 보기', params: { userId: comment.creator?.pk } }"
              class="text-decoration-none text-subtitle-2 font-weight-bold"
            >
              {{ comment.creator?.username }}
            </router-link>
            <span class="text-caption text-grey">{{ elapsedTime(comment.created) }}</span>
          </div>
          <span class="comment-content">
            {{ comment.content }}
          </span>
        </v-card>
        <div class="d-flex mt-1 ml-1">
          <v-btn variant="text" size="x-small" density="comfortable" color="primary" class="mr-2">
            답글
          </v-btn>
          <v-btn variant="text" size="x-small" density="comfortable" color="grey">공감</v-btn>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.comment-item {
  transition: all 0.2s ease;
}

.comment-content {
  white-space: pre-wrap;
  line-height: 1.5;
}
</style>
