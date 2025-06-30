<script lang="ts" setup>
import type { PropType } from 'vue'
import type { News } from '@/store/types/work_inform.ts'
import { elapsedTime } from '@/utils/baseMixins.ts'
import CommentList from './CommentList.vue'

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
          <v-icon icon="mdi-star" color="amber" size="sm" />
          <router-link to="" class="ml-1">관심끄기</router-link>
        </span>

        <span class="mr-2 form-text">
          <v-icon icon="mdi-pencil" color="amber" size="sm" />
          <router-link to="" class="ml-1">편집</router-link>
        </span>

        <span class="mr-2 form-text">
          <v-icon icon="mdi-trash-can-outline" color="grey" size="sm" />
          <router-link to="" class="ml-1">삭제</router-link>
        </span>
      </CCol>
    </CRow>

    <CRow>
      <CCol class="text-50 fst-italic">
        {{ news.summary || '요약 내용이 없습니다.' }}
      </CCol>
    </CRow>

    <CRow>
      <CCol>
        <router-link to="">{{ news.author?.username }}</router-link>
        이(가)
        <router-link to="">{{ elapsedTime(news.created) }}</router-link>
        에 추가함
      </CCol>
    </CRow>

    <v-divider />

    <CRow class="mt-3">
      <CCol v-html="news.content" />
    </CRow>

    <CRow class="mt-5">
      <h5>댓글</h5>
    </CRow>

    <CRow class="mb-5">
      <CCol>
        <CommentList />
      </CCol>
    </CRow>

    <CRow>
      <CCol>
        <router-link to="">댓글 추가</router-link>
      </CCol>
    </CRow>
  </template>
</template>
