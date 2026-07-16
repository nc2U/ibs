<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePerms } from '@/composables/usePerms.ts'
import { useForum } from '@/store/pinia/forum.ts'
import type { Post } from '@/store/types/forum.ts'
import Loading from '@/components/Loading/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import ForumIndex from './components/ForumIndex.vue'
import PostList from './components/PostList.vue'
import PostDetail from './components/PostDetail.vue'
import PostForm from './components/PostForm.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

const cBody = ref()
const toggle = () => cBody.value.toggle()
defineExpose({ toggle })

const { can, PERM } = usePerms()
const canForumRead = computed(() => can(PERM.FORUM_READ))
const canForumManage = computed(() => can(PERM.FORUM_MANAGE))

const forumStore = useForum()
const forum = computed(() => forumStore.forum)
const forumList = computed(() => forumStore.forumList)
const categoryList = computed(() => forumStore.categoryList)
const postList = computed(() => forumStore.postList)
const post = computed(() => forumStore.post)
const commentList = computed(() => forumStore.commentList)

const [route, router] = [useRoute(), useRouter()]

const page = ref(1)

const heatedPage = ref<number[]>([])

const fetchPostData = async (pk: number) => {
  await forumStore.fetchPost(pk)
  if (!heatedPage.value.includes(pk)) {
    heatedPage.value.push(pk)
    await forumStore.hitPost(pk)
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
    await forumStore.deletePost(delPk.value, {
      forum: Number(route.params.forumId),
      page: page.value,
    })
    await router.replace({
      name: '(게시판) - 보기',
      params: { projId: route.params.projId, forumId: route.params.forumId },
    })
  }
  refConfirmModal.value.close()
}

const onLikePost = (pk: number) => forumStore.patchPostLike(pk)
const onBlamePost = (pk: number) => forumStore.patchPostBlame(pk)

const dataSetup = async () => {
  loading.value = true
  const projId = route.params.projId as string
  const forumId = route.params.forumId ? Number(route.params.forumId) : null
  const postId = route.params.postId ? Number(route.params.postId) : null

  if (projId) {
    await forumStore.fetchForumList({ project: projId })
    if (forumId) {
      await forumStore.fetchForum(forumId)
      await forumStore.fetchCategoryList(forumId)
      if (postId) {
        await fetchPostData(postId)
      } else {
        await forumStore.fetchPostList({ forum: forumId, page: page.value })
      }
    }
  }
  loading.value = false
}

const onPageSelect = (p: number) => {
  page.value = p
  if (route.params.forumId) {
    forumStore.fetchPostList({ forum: Number(route.params.forumId), page: p })
  }
}

watch(
  () => route.params,
  async (newParams, oldParams) => {
    if (newParams.projId !== oldParams?.projId) {
      await dataSetup()
    } else if (newParams.forumId !== oldParams?.forumId || newParams.postId !== oldParams?.postId) {
      if (newParams.forumId) {
        loading.value = true
        if (newParams.forumId !== oldParams?.forumId) {
          page.value = 1
          await forumStore.fetchForum(Number(newParams.forumId))
          await forumStore.fetchCategoryList(Number(newParams.forumId))
        }

        if (newParams.postId) {
          forumStore.removePost() // Clear old post data
          await fetchPostData(Number(newParams.postId))
        } else {
          forumStore.removePost()
          await forumStore.fetchPostList({ forum: Number(newParams.forumId), page: page.value })
        }
        loading.value = false
      }
    }
  },
  { deep: true },
)

const loading = ref(true)
onBeforeMount(async () => {
  await dataSetup()
})
</script>

<template>
  <ContentBody ref="cBody">
    <template v-slot:default>
      <Loading v-model:active="loading" />

      <!-- 게시판 메인 인덱스 -->
      <ForumIndex v-if="route.name === '(게시판)'" :forum-list="forumList" />

      <!-- 게시물 목록 -->
      <PostList
        v-else-if="route.name === '(게시판) - 보기' && !route.params.postId"
        :forum="forum"
        :post-list="postList"
        :page="page"
        @page-select="onPageSelect"
      />

      <!-- 게시물 상세 -->
      <PostDetail
        v-else-if="route.name === '(게시판) - 게시물 보기' && (post || loading)"
        :post="post as Post"
        :comments="commentList"
        @delete-post="onDeletePost"
        @like-post="onLikePost"
        @blame-post="onBlamePost"
      />

      <!-- 게시물 작성 -->
      <PostForm
        v-else-if="route.name === '(게시판) - 게시물 작성'"
        :forum-id="Number(route.params.forumId)"
        :categories="categoryList"
      />

      <!-- 게시물 수정 -->
      <PostForm
        v-else-if="route.name === '(게시판) - 게시물 수정' && (post || loading)"
        :post="post"
        :forum-id="Number(route.params.forumId)"
        :categories="categoryList"
      />
    </template>

    <template v-slot:aside>
      <CRow class="mb-4">
        <CCol>
          <h6 class="text-subtitle-1 mb-2">최근 게시물</h6>
          <v-divider class="mt-0" />
          <ul v-if="postList.length" class="list-unstyled aside-menu mb-4">
            <li v-for="p in postList.slice(0, 5)" :key="p.pk" class="mb-2 text-truncate">
              <v-icon icon="mdi-comment-text-outline" size="x-small" class="mr-1" />
              <router-link
                v-if="canForumRead"
                :to="{
                  name: '(게시판) - 게시물 보기',
                  params: {
                    projId: route.params.projId,
                    forumId: p.forum,
                    postId: p.pk,
                  },
                }"
                class="text-body-2"
              >
                {{ p.title }}
              </router-link>
              <span v-else>{{ p.title }}</span>
              <span v-if="p.comments?.length" class="ml-2 text-grey">
                ({{ p.comments.length }})
              </span>
            </li>
          </ul>
          <div v-else class="py-4 text-muted">등록된 게시물이 없습니다.</div>
        </CCol>
      </CRow>

      <CRow class="mb-4">
        <CCol>
          <h6 class="text-subtitle-1 mb-2">게시판 관리</h6>
          <v-divider class="mt-0" />
          <ul v-if="canForumManage" class="list-unstyled aside-menu">
            <li class="mb-2">
              <v-icon icon="mdi-view-dashboard-outline" size="small" class="mr-2" />
              <router-link :to="{ name: '(개요)', params: { projId: route.params.projId } }">
                프로젝트 개요
              </router-link>
            </li>
            <li v-if="canForumManage" class="mb-2">
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
          <div v-else class="py-4 text-muted">게시판 관리 권한이 없습니다.</div>
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
