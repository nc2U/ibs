<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import { useRoute } from 'vue-router'
import type { News } from '@/store/types/work_inform.ts'

defineProps({ news: { type: Object as PropType<News>, required: true } })

const route = useRoute()

const isProj = computed(() => !!route.params.projId)
</script>

<template>
  <CRow>
    <CCol>
      <h6>
        <span v-if="!isProj">
          <router-link :to="{ name: '(개요)', params: { projId: news.project?.slug } }">
            {{ news.project?.name }}
          </router-link>
          :
        </span>
        <router-link
          :to="{ name: '(공지) - 보기', params: { projId: news.project?.slug, newsId: news.pk } }"
        >
          {{ news.title }}
          <span v-if="news.comments && news.comments.length" class="strong">
            ({{ news.comments.length }} 개의 댓글)
          </span>
        </router-link>
      </h6>
    </CCol>
  </CRow>

  <CRow class="mb-4 text-grey">
    <CCol>
      <router-link to="">Austin Kho</router-link>
      이(가) 2일 전에 추가함
    </CCol>
  </CRow>

  <CRow class="mb-0">
    <CCol v-html="news.content" />
  </CRow>

  <v-divider class="mb-4" />
</template>
