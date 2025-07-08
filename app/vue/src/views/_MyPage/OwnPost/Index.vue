<script lang="ts" setup>
import { computed, type ComputedRef, inject, onBeforeMount, ref } from 'vue'
import { pageTitle, navMenu } from '@/views/_MyPage/_menu/headermixin'
import type { User } from '@/store/types/accounts'
import { type PostFilter, useBoard } from '@/store/pinia/board'
import Loading from '@/components/Loading/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ListController from './components/ListController.vue'
import PostList from './components/PostList.vue'
import CommentList from './components/CommentList.vue'

const mainViewName = ref('내 작성글')
const sort = ref<'post' | 'comment'>('post')
const userInfo = inject<ComputedRef<User>>('userInfo')

const postFilter = ref<PostFilter>({
  user: '',
  search: '',
  ordering: '-created',
  page: 1,
})

const listFiltering = (payload: PostFilter) => {
  postFilter.value.ordering = payload.ordering
  postFilter.value.search = payload.search
  postFilter.value.page = payload.page
  fetchPostList({ ...postFilter.value })
}

const pageSelect = (page: number) => {
  postFilter.value.page = page
  listFiltering(postFilter.value)
}

const boardStore = useBoard()
const boardList = computed(() => boardStore.boardList)
const postList = computed(() => boardStore.postList)
const commentList = computed(() => boardStore.commentList)

const fetchBoardList = () => boardStore.fetchBoardList({})
const fetchPostList = (payload: PostFilter) => boardStore.fetchPostList(payload)
const fetchCommentList = (payload: any) => boardStore.fetchCommentList(payload)

const dataSetup = (pk: number) => {
  postFilter.value.user = pk
  fetchBoardList()
  fetchPostList(postFilter.value)
  fetchCommentList({ user: userInfo?.value.pk })
}

const loading = ref(true)
onBeforeMount(() => {
  dataSetup(userInfo?.value.pk as number)
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <ContentHeader :page-title="pageTitle" :nav-menu="navMenu" />

  <ContentBody>
    <CCardBody class="pb-5">
      <div class="pt-3">
        <ListController
          ref="fController"
          :sort="sort"
          :post-filter="postFilter"
          @list-filter="listFiltering"
        />

        <CRow class="pb-2">
          <CCol sm="12" lg="9" xl="6">
            <CRow>
              <CCol class="d-grid gap-2 pr-0">
                <CFormCheck
                  v-model="sort"
                  value="post"
                  :button="{
                    color: 'primary',
                    variant: 'outline',
                    shape: 'rounded-0',
                  }"
                  type="radio"
                  name="options-outlined"
                  id="primary-outlined"
                  label="원글"
                />
              </CCol>
              <CCol class="d-grid gap-2 pl-0">
                <CFormCheck
                  v-model="sort"
                  value="comment"
                  :button="{ color: 'success', variant: 'outline', shape: 'rounded-0' }"
                  type="radio"
                  name="options-outlined"
                  id="success-outlined"
                  label="댓글"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <PostList
          v-if="sort === 'post'"
          :board-list="boardList"
          :post-list="postList"
          :view-route="mainViewName"
          @page-select="pageSelect"
        />

        <CommentList v-if="sort === 'comment'" :board-list="boardList" :comments="commentList" />
      </div>
    </CCardBody>
  </ContentBody>
</template>
