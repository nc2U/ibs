<script lang="ts" setup>
import { type PropType } from 'vue'
import type { Forum, Post } from '@/store/types/forum'
import { useForum } from '@/store/pinia/forum'
import NoData from '@/components/NoData/Index.vue'
import Pagination from '@/components/Pagination'
import PostItem from './PostItem.vue'

defineProps({
  forum: { type: Object as PropType<Forum | null>, default: null },
  postList: { type: Array as PropType<Post[]>, default: () => [] },
  page: { type: Number, default: 1 },
})

const emit = defineEmits(['page-select'])

const frmStore = useForum()
const postPages = (limit: number) => frmStore.postPages(limit)

const pageSelect = (page: number) => emit('page-select', page)
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>
        <v-icon icon="mdi-forum-outline" color="info" class="mr-2" />
        {{ forum?.name }}
      </h5>
    </CCol>
    <CCol class="text-right">
      <v-btn
        color="success"
        size="small"
        variant="flat"
        prepend-icon="mdi-pencil-plus"
        :to="{
          name: '(게시판) - 게시물 작성',
          params: { projId: $route.params.projId, forumId: forum?.pk },
        }"
      >
        새 게시물
      </v-btn>
    </CCol>
  </CRow>

  <p class="text-body-2 text-muted mb-4">{{ forum?.description }}</p>

  <NoData v-if="!postList.length" />

  <CCol v-else col="12">
    <CTable striped hover small responsive align="middle">
      <colgroup>
        <col style="width: 10%" />
        <col style="width: 50%" />
        <col style="width: 15%" />
        <col style="width: 15%" />
        <col style="width: 10%" />
      </colgroup>
      <CTableHead>
        <CTableRow color="light" class="text-center">
          <CTableHeaderCell scope="col">#</CTableHeaderCell>
          <CTableHeaderCell scope="col">제목</CTableHeaderCell>
          <CTableHeaderCell scope="col">작성자</CTableHeaderCell>
          <CTableHeaderCell scope="col">날짜</CTableHeaderCell>
          <CTableHeaderCell scope="col">조회수</CTableHeaderCell>
        </CTableRow>
      </CTableHead>
      <CTableBody>
        <CTableRow v-for="post in postList" :key="post.pk" :class="{ strong: post.is_notice }">
          <PostItem :post="post" />
        </CTableRow>
      </CTableBody>
    </CTable>

    <Pagination
      :active-page="page"
      :limit="8"
      :pages="postPages(20)"
      @active-page-change="pageSelect"
      class="mt-3"
    />
  </CCol>
</template>
