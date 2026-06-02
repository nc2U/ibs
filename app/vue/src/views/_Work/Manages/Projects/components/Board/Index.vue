<script lang="ts" setup>
import { computed, inject, onBeforeMount, ref, watch, type ComputedRef } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useBoard } from '@/store/pinia/board.ts'
import type { Board, Post } from '@/store/types/board.ts'
import Loading from '@/components/Loading/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import BoardIndex from './components/BoardIndex.vue'
import BoardList from './components/BoardList.vue'
import BoardView from './components/BoardView.vue'
import BoardForm from './components/BoardForm.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

const cBody = ref()
const toggle = () => cBody.value.toggle()
defineExpose({ toggle })

const workManager = inject<ComputedRef<boolean>>('workManager')

const brdStore = useBoard()
const board = computed(() => brdStore.board)
const boardList = computed(() => brdStore.boardList)
const categoryList = computed(() => brdStore.categoryList)
const postList = computed(() => brdStore.postList)
const post = computed(() => brdStore.post)
const commentList = computed(() => brdStore.commentList)

const [route, router] = [useRoute(), useRouter()]

const page = ref(1)

const heatedPage = ref<number[]>([])

const postHit = async (pk: number) => {
  if (!heatedPage.value.includes(pk)) {
    heatedPage.value.push(pk)
    await brdStore.fetchPost(pk)
    const hit = ((post.value as Post)?.hit ?? 0) + 1
    await brdStore.patchPost({ pk, hit })
  }
}

const refConfirmModal = ref()
const delPk = ref<number | null>(null)

const onDeletePost = (pk: number) => {
  delPk.value = pk
  refConfirmModal.value.callModal('게시물 삭제', '이 게시물을 정말 삭제하시겠습니까?', '', 'danger')
}

const deletePostConfirm = async () => {
  if (delPk.value) {
    await brdStore.deletePost(delPk.value, { board: Number(route.params.brdId), page: page.value })
    router.replace({ name: '(게시판) - 보기', params: { projId: route.params.projId, brdId: route.params.brdId } })
  }
  refConfirmModal.value.close()
}

const onLikePost = (pk: number) => brdStore.patchPostLike(pk)
const onBlamePost = (pk: number) => brdStore.patchPostBlame(pk)

const dataSetup = async () => {
  const projId = route.params.projId as string
  const brdId = route.params.brdId ? Number(route.params.brdId) : null
  const postId = route.params.postId ? Number(route.params.postId) : null

  if (projId) {
    await brdStore.fetchBoardList({ project: projId })
    if (brdId) {
      await brdStore.fetchBoard(brdId)
      await brdStore.fetchCategoryList(brdId)
      if (postId) {
        await brdStore.fetchPost(postId)
      } else {
        await brdStore.fetchPostList({ board: brdId, page: page.value })
      }
    }
  }
}

const onPageSelect = (p: number) => {
  page.value = p
  if (route.params.brdId) {
    brdStore.fetchPostList({ board: Number(route.params.brdId), page: p })
  }
}

watch(
  () => route.params.brdId,
  async nVal => {
    if (nVal && !route.params.postId) {
      page.value = 1
      await brdStore.fetchBoard(Number(nVal))
      await brdStore.fetchCategoryList(Number(nVal))
      await brdStore.fetchPostList({ board: Number(nVal), page: 1 })
    }
  },
)

watch(
  () => route.params.postId,
  async nVal => {
    if (nVal) {
      await postHit(Number(nVal))
    } else {
      brdStore.removePost()
    }
  },
)

const loading = ref(true)
onBeforeMount(async () => {
  await dataSetup()
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <ContentBody ref="cBody">
    <template v-slot:default>
      <!-- 게시판 메인 인덱스 -->
      <BoardIndex v-if="route.name === '(게시판)'" :board-list="boardList" />

      <!-- 게시물 목록 -->
      <BoardList
        v-else-if="route.name === '(게시판) - 보기'"
        :board="board"
        :post-list="postList"
        :page="page"
        @page-select="onPageSelect"
      />

      <!-- 게시물 상세 -->
      <BoardView
        v-else-if="route.name === '(게시판) - 게시물 보기' && post"
        :post="post as Post"
        :comments="commentList"
        @delete-post="onDeletePost"
        @like-post="onLikePost"
        @blame-post="onBlamePost"
      />

      <!-- 게시물 작성 -->
      <BoardForm
        v-else-if="route.name === '(게시판) - 게시물 작성'"
        :brd-id="Number(route.params.brdId)"
        :categories="categoryList"
      />

      <!-- 게시물 수정 -->
      <BoardForm
        v-else-if="route.name === '(게시판) - 게시물 수정' && post"
        :post="post"
        :brd-id="Number(route.params.brdId)"
        :categories="categoryList"
      />
    </template>

    <template v-slot:aside>
      <CRow class="mb-4">
        <CCol>
          <h6 class="asideTitle">게시판 관리</h6>
          <v-divider class="mt-0" />
          <ul class="list-unstyled aside-menu">
            <li class="mb-2">
              <v-icon icon="mdi-view-dashboard-outline" size="small" class="mr-2" />
              <router-link :to="{ name: '(개요)', params: { projId: route.params.projId } }">
                프로젝트 개요
              </router-link>
            </li>
            <li v-if="workManager" class="mb-2">
              <v-icon icon="mdi-cog-outline" size="small" class="mr-2" />
              <router-link
                :to="{
                  name: '(설정)',
                  params: { projId: route.params.projId },
                  query: { menu: '게시판' },
                }"
              >
                게시판 설정
              </router-link>
            </li>
            <li>
              <v-icon icon="mdi-trash-can-outline" size="small" class="mr-2" />
              <router-link to="">휴지통</router-link>
            </li>
          </ul>
        </CCol>
      </CRow>
    </template>
  </ContentBody>

  <ConfirmModal ref="refConfirmModal">
    <template #footer>
      <v-btn color="danger" @click="deletePostConfirm">삭제</v-btn>
    </template>
  </ConfirmModal>
</template>
