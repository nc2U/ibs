<script lang="ts" setup>
import { type PropType } from 'vue'
import type { News } from '@/store/types/work_inform.ts'
import { markdownRender } from '@/utils/helper.ts'
import { elapsedTime } from '@/utils/baseMixins.ts'
import { useInform } from '@/store/pinia/work_inform.ts'
import FileDisplay from '@/views/_Work/components/atomics/FileDisplay.vue'
import CommentList from './CommentList.vue'

const props = defineProps({
  news: { type: Object as PropType<News>, required: true },
  viewForm: { type: Boolean, default: false },
})

const infStore = useInform()

const deleteFile = (pk: number) => {
  const form = new FormData()
  form.append('del_file', JSON.stringify(pk))
  infStore.patchNews(props.news?.pk as number, form)
}
</script>

<template>
  <div v-if="news" class="news-view">
    <v-card variant="flat" border class="pa-5 mb-5 rounded-lg card-white">
      <!-- Title Section -->
      <div class="d-flex justify-space-between align-start mb-3">
        <h5 class="font-weight-bold">
          <v-chip
            v-if="news.is_important"
            color="primary"
            size="small"
            variant="flat"
            class="mr-2 mb-1"
          >
            중요 공지
          </v-chip>
          {{ news.title }}
        </h5>
      </div>

      <!-- Metadata Section -->
      <div class="metadata d-flex flex-wrap align-center mb-5">
        <div class="d-flex align-center mr-4">
          <v-avatar size="24" class="mr-2">
            <v-icon icon="mdi-account" size="18" />
          </v-avatar>
          <router-link
            :to="{ name: '사용자 - 보기', params: { userId: news.author?.pk } }"
            class="text-decoration-none text-primary font-weight-medium"
          >
            {{ news.author?.username }}
          </router-link>
        </div>
        <div class="d-flex align-center mr-4">
          <v-icon icon="mdi-clock-outline" size="18" class="mr-1" />
          <router-link
            :to="{ name: '(실행기록)', params: { projId: news.project?.slug } }"
            class="text-decoration-none"
          >
            {{ elapsedTime(news.created) }}
          </router-link>
          <span class="ml-1">에 추가됨</span>
        </div>
        <div v-if="news.updated !== news.created" class="d-flex align-center">
          <v-icon icon="mdi-update" size="18" class="mr-1" />
          <span class="small">수정됨: {{ elapsedTime(news.updated) }}</span>
        </div>
      </div>

      <v-divider />

      <!-- Summary Section -->
      <div v-if="news.summary" class="summary-box my-6 pa-4 rounded-e-lg bg-more-light">
        <div class="text-subtitle-2 mb-1 font-weight-bold">요약</div>
        <div class="text-body-1 fst-italic">
          {{ news.summary }}
        </div>
      </div>
      <div v-else class="my-6 text-grey-lighten-2 fst-italic text-center small">
        요약 내용이 없습니다.
      </div>

      <!-- Content Section -->
      <div class="content-body py-4 mb-6" v-html="markdownRender(news.content)" />

      <!-- Files Section -->
      <div v-if="news.files.length" class="files-section mt-6 pt-6">
        <div class="d-flex align-center mb-4">
          <v-icon icon="mdi-attachment" size="20" class="mr-2 text-grey" />
          <span class="font-weight-bold"> 첨부 파일 ({{ news.files.length }}) </span>
        </div>
        <v-list density="compact" class="bg-transparent pa-0" style="overflow-x: hidden">
          <CRow v-for="(file, index) in news.files" :key="index" class="mb-2 no-gutters">
            <FileDisplay :file="file" @delete-file="deleteFile" />
          </CRow>
        </v-list>
      </div>
    </v-card>

    <!-- Comments Section -->
    <v-sheet border rounded="lg" class="pa-5 card-white">
      <div class="d-flex align-center mb-6">
        <v-icon icon="mdi-comment-text-multiple-outline" size="20" class="mr-3 text-primary" />
        <h6 class="font-weight-bold mb-0">댓글</h6>
        <v-badge
          v-if="news.comments?.length"
          :content="news.comments.length"
          color="primary"
          inline
          class="ml-2"
        />
      </div>
      <CommentList />
    </v-sheet>
  </div>
</template>

<style scoped>
.news-view {
  max-width: 100%;
}

.metadata {
  font-size: 0.9rem;
}

.summary-box {
  border-left: 5px solid #1867c0; /* Vuetify primary blue */
}

.content-body {
  font-size: 1rem;
  line-height: 1.8;
}

.content-body :deep(h1),
.content-body :deep(h2),
.content-body :deep(h3) {
  margin-top: 1.5rem;
  margin-bottom: 1rem;
  font-weight: 700;
}

.content-body :deep(p) {
  margin-bottom: 1.25rem;
}

.content-body :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  margin: 1.5rem 0;
}

.content-body :deep(code) {
  background-color: #f8f9fa;
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
  color: #e83e8c;
  font-size: 0.9em;
}

.dark-theme .content-body :deep(code) {
  background-color: #2d2d2d;
  color: #ff79c6;
}

.content-body :deep(pre) {
  background-color: #282c34;
  color: #abb2bf;
  padding: 1rem;
  border-radius: 8px;
  overflow-x: auto;
  margin-bottom: 1.5rem;
}

.border-t-sm {
  border-top: 1px solid #e0e0e0;
}

.border-t-dark {
  border-top: 1px solid #444;
}
</style>
