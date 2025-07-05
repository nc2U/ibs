<script lang="ts" setup>
import type { PropType } from 'vue'
import type { News } from '@/store/types/work_inform.ts'
import { elapsedTime } from '@/utils/baseMixins.ts'
import CommentList from './CommentList.vue'
import FileDisplay from '@/views/_Work/components/atomics/FileDisplay.vue'

defineProps({ news: { type: Object as PropType<News>, required: true } })
</script>

<template>
  <template v-if="news">
    <router-link :to="{ name: '(공지)' }">공지</router-link>
    »

    <CRow>
      <CCol class="py-2">
        <h5>{{ news.title }}</h5>
      </CCol>

      <CCol class="text-right">
        <span class="mr-2 form-text">
          <v-icon icon="mdi-star" color="amber" size="15" />
          <router-link to="" class="ml-1">관심끄기</router-link>
        </span>

        <span class="mr-2 form-text">
          <v-icon icon="mdi-pencil" color="amber" size="15" />
          <router-link to="" class="ml-1">편집</router-link>
        </span>

        <span class="mr-2 form-text">
          <v-icon icon="mdi-trash-can-outline" color="grey" size="15" />
          <router-link to="" class="ml-1">삭제</router-link>
        </span>
      </CCol>
    </CRow>

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
      <CCol v-html="news.content" />
    </CRow>

    <div v-if="news.files.length" class="mb-5">
      <CRow v-for="(file, index) in news.files" :key="index">
        <FileDisplay :file="file" />
      </CRow>
    </div>

    <CRow>
      <CCol>
        <CommentList />
      </CCol>
    </CRow>
  </template>
</template>
