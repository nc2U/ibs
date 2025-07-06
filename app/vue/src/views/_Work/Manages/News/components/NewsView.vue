<script lang="ts" setup>
import { type PropType } from 'vue'
import type { News } from '@/store/types/work_inform.ts'
import { elapsedTime } from '@/utils/baseMixins.ts'
import { useInform } from '@/store/pinia/work_inform.ts'
import { VueMarkdownIt } from '@f3ve/vue-markdown-it'
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
  <template v-if="news">
    <CRow class="mb-3">
      <CCol class="text-50 fst-italic">
        {{ news.summary || '요약 내용이 없습니다.' }}
      </CCol>
    </CRow>

    <CRow>
      <CCol class="text-grey">
        <router-link :to="{ name: '사용자 - 보기', params: { userId: news.author?.pk } }">
          {{ news.author?.username }}
        </router-link>
        이(가)
        <router-link :to="{ name: '(작업내역)', params: { projId: news.project?.slug } }">
          {{ elapsedTime(news.created) }}
        </router-link>
        에 추가함
      </CCol>
    </CRow>

    <v-divider />

    <CRow class="my-5">
      <VueMarkdownIt :source="news.content as string" />
    </CRow>

    <div v-if="news.files.length" class="mb-5">
      <CRow v-for="(file, index) in news.files" :key="index">
        <FileDisplay :file="file" @delete-file="deleteFile" />
      </CRow>
    </div>

    <CRow>
      <CCol>
        <CommentList />
      </CCol>
    </CRow>
  </template>
</template>
