<script setup lang="ts">
import type { PropType } from 'vue'
import { useRouter } from 'vue-router'
import { useBoard } from '@/store/pinia/board'
import { btnLight, TableSecondary } from '@/utils/cssMixins'
import type { Post as P } from '@/store/types/board'
import TopPosts from '@/components/Posts/components/TopPosts.vue'
import Post from './components/Post.vue'
import Pagination from '@/components/Pagination'

defineProps({
  company: { type: Number, default: null },
  project: { type: Number, default: null },
  toHome: { type: String, default: '' },
  page: { type: Number, default: 1 },
  noticeList: { type: Array as PropType<P[]>, default: () => [] },
  postList: { type: Array as PropType<P[]>, default: () => [] },
  viewRoute: { type: String, required: true },
  isLawsuit: { type: Boolean, default: false },
  writeAuth: { type: Boolean, default: true },
})

const emit = defineEmits(['page-select'])

const router = useRouter()

const boardStore = useBoard()
const postPages = (num: number) => boardStore.postPages(num)
const pageSelect = (page: number) => emit('page-select', page)
</script>

<template>
  <CTable hover responsive align="middle">
    <colgroup>
      <col style="width: 13%" />
      <col style="width: 50%" />
      <col style="width: 12%" />
      <col style="width: 15%" />
      <col style="width: 10%" />
    </colgroup>

    <CTableHead>
      <CTableRow :color="TableSecondary" class="text-center border-top-1">
        <CTableHeaderCell scope="col">번호</CTableHeaderCell>
        <CTableHeaderCell scope="col">제목</CTableHeaderCell>
        <CTableHeaderCell scope="col">등록자</CTableHeaderCell>
        <CTableHeaderCell scope="col">등록일시</CTableHeaderCell>
        <CTableHeaderCell scope="col">조회수</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <TopPosts
        v-for="post in noticeList"
        :key="post.pk"
        :post="post"
        :view-route="viewRoute"
        :is-lawsuit="isLawsuit"
      />
      <Post
        v-for="post in postList"
        :key="post.pk"
        :post="post"
        :view-route="viewRoute"
        :is-lawsuit="isLawsuit"
      />
    </CTableBody>
  </CTable>

  <CRow class="flex-lg-row flex-column-reverse">
    <CCol lg="8">
      <Pagination
        :active-page="page"
        :limit="8"
        :pages="postPages(10)"
        class="mt-3"
        @active-page-change="pageSelect"
      />
    </CCol>
    <CCol lg="4" class="text-right pt-3">
      <v-btn
        v-if="toHome"
        :color="btnLight"
        class="px-5"
        @click="router.push({ name: `대 시 보 드` })"
      >
        홈으로
      </v-btn>
      <v-btn
        v-if="writeAuth"
        color="primary"
        class="px-5"
        :disabled="!company && !project"
        @click="router.push({ name: `${viewRoute} - 작성` })"
      >
        등록하기
      </v-btn>
    </CCol>
  </CRow>
</template>
