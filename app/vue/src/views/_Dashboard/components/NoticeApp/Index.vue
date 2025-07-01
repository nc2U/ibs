<script lang="ts" setup>
import { ref, computed, watch, onBeforeMount } from 'vue'
import { useCompany } from '@/store/pinia/company'
import { useAccount } from '@/store/pinia/account'
import { type RouteLocationNormalizedLoaded as Loaded, useRoute, useRouter } from 'vue-router'
import type { PostFile, Attatches, PostLink, PatchPost, Post } from '@/store/types/board'
import { type PostFilter, useBoard } from '@/store/pinia/board'
import ListController from '@/components/Posts/ListController.vue'
import CategoryTabs from '@/components/Posts/CategoryTabs.vue'
import PostList from '@/components/Posts/PostList.vue'
import PostView from '@/components/Posts/PostView.vue'
import PostForm from '@/components/Posts/PostForm.vue'

const lController = ref()
const boardNumber = ref(1)
const mainViewName = ref('공지 게시판')

const postFilter = ref<PostFilter>({
  board: boardNumber.value,
  category: '',
  ordering: '-created',
  search: '',
  page: 1,
})

const heatedPage = ref<number[]>([])
const newFiles = ref<File[]>([])
const cngFiles = ref<
  {
    pk: number
    file: File
  }[]
>([])

const listFiltering = (payload: PostFilter) => {
  postFilter.value.ordering = payload.ordering ?? '-created'
  postFilter.value.search = payload.search ?? ''
  if (company.value) fetchPostList({ ...postFilter.value })
}

const selectCate = (cate: number) => {
  postFilter.value.page = 1
  postFilter.value.category = cate
  listFiltering(postFilter.value)
}

const pageSelect = (page: number) => {
  postFilter.value.page = page
  listFiltering(postFilter.value)
}

const comStore = useCompany()
const company = computed(() => comStore.company?.pk)

const accStore = useAccount()
const writeAuth = computed(() => accStore.writeComDocs)

const createScrape = (payload: { post: number; user: number }) => accStore.createScrape(payload)

const boardStore = useBoard()
const post = computed(() => boardStore.post)
const postList = computed(() => boardStore.postList)
const noticeList = computed(() => boardStore.noticeList)
const categoryList = computed(() => boardStore.categoryList)

const fetchBoardList = () => boardStore.fetchBoardList()
const fetchLink = (pk: number) => boardStore.fetchLink(pk)
const fetchFile = (pk: number) => boardStore.fetchFile(pk)
const fetchPost = (pk: number) => boardStore.fetchPost(pk)
const fetchPostList = (payload: PostFilter) => boardStore.fetchPostList(payload)
const fetchCategoryList = (board: number) => boardStore.fetchCategoryList(board)

const createPost = (payload: { form: FormData }) => boardStore.createPost(payload)
const updatePost = (payload: { pk: number; form: FormData }) => boardStore.updatePost(payload)
const patchPost = (payload: PatchPost & { filter: PostFilter }) => boardStore.patchPost(payload)
const patchLink = (payload: PostLink) => boardStore.patchLink(payload)
const patchFile = (payload: PostFile) => boardStore.patchFile(payload)

const [route, router] = [
  useRoute() as Loaded & {
    name: string
  },
  useRouter(),
]

watch(route, val => {
  if (val.params.postId) fetchPost(Number(val.params.postId))
  else boardStore.removePost()
})

const postsRenewal = (page: number) => {
  postFilter.value.page = page
  fetchPostList(postFilter.value)
}

const fileChange = (payload: { pk: number; file: File }) => cngFiles.value.push(payload)

const fileUpload = (file: File) => newFiles.value.push(file)

const postHit = async (pk: number) => {
  if (!heatedPage.value.includes(pk)) {
    heatedPage.value.push(pk)
    await fetchPost(pk)
    const hit = (post.value?.hit ?? 0) + 1
    await patchPost({ pk, hit, filter: postFilter.value })
  }
}
const linkHit = async (pk: number) => {
  const link = (await fetchLink(pk)) as PostLink
  link.hit = (link.hit as number) + 1
  await patchLink(link)
}
const fileHit = async (pk: number) => {
  const file = (await fetchFile(pk)) as PostFile
  const hit = (file.hit as number) + 1
  await patchFile({ pk, hit })
}

const postScrape = (post: number) => {
  const user = accStore.userInfo?.pk as number
  createScrape({ post, user }) // 스크랩 추가
}

const onSubmit = async (payload: Post & Attatches) => {
  if (company.value) {
    const { pk, ...getData } = payload
    getData.newFiles = newFiles.value
    getData.cngFiles = cngFiles.value

    const form = new FormData()

    for (const key in getData) {
      if (key === 'links' || key === 'files') {
        ;(getData[key] as any[]).forEach(val => form.append(key, JSON.stringify(val)))
      } else if (key === 'newLinks' || key === 'newFiles' || key === 'cngFiles') {
        if (key === 'cngFiles') {
          getData[key]?.forEach(val => {
            form.append('cngPks', val.pk as any)
            form.append('cngFiles', val.file as Blob)
          })
        } else (getData[key] as any[]).forEach(val => form.append(key, val as string | Blob))
      } else {
        const formValue = getData[key] === null ? '' : getData[key]
        form.append(key, formValue as string)
      }
    }

    if (pk) {
      await updatePost({ pk, form })
      await router.replace({
        name: `${mainViewName.value} - 보기`,
        params: { postId: pk },
      })
    } else {
      await createPost({ form })
      await router.replace({ name: `${mainViewName.value}` })
      lController.value.resetForm()
    }
    newFiles.value = []
    cngFiles.value = []
  }
}

const dataSetup = (postId?: string | string[]) => {
  fetchBoardList()
  fetchCategoryList(boardNumber.value)
  fetchPostList(postFilter.value)
  if (postId) fetchPost(Number(postId))
}

onBeforeMount(() => dataSetup(route.params?.postId))
</script>

<template>
  <CContainer fluid>
    <CCard>
      <CCardBody>
        <h5>{{ mainViewName }}</h5>

        <v-divider />

        <div v-if="route.name === mainViewName">
          <ListController
            ref="lController"
            :com-from="true"
            :post-filter="postFilter"
            @list-filter="listFiltering"
          />
          <CategoryTabs
            :category="postFilter.category as number"
            :category-list="categoryList"
            @select-cate="selectCate"
          />
          <PostList
            :company="company as number"
            :to-home="mainViewName"
            :page="postFilter.page"
            :notice-list="noticeList"
            :post-list="postList"
            :view-route="mainViewName"
            :write-auth="writeAuth"
            @page-select="pageSelect"
          />
        </div>

        <div v-else-if="route.name.includes('보기')">
          <PostView
            :board-num="boardNumber"
            :heated-page="heatedPage"
            :re-order="postFilter.ordering !== '-created'"
            :category="postFilter.category as number"
            :post="post as Post"
            :view-route="mainViewName"
            :curr-page="postFilter.page ?? 1"
            :write-auth="writeAuth"
            :post-filter="postFilter"
            @post-hit="postHit"
            @link-hit="linkHit"
            @file-hit="fileHit"
            @post-scrape="postScrape"
            @posts-renewal="postsRenewal"
          />
        </div>

        <div v-else-if="route.name.includes('작성')">
          <PostForm
            :board-num="boardNumber"
            :category-list="categoryList"
            :view-route="mainViewName"
            :write-auth="writeAuth"
            @file-upload="fileUpload"
            @on-submit="onSubmit"
          />
        </div>

        <div v-else-if="route.name.includes('수정')">
          <PostForm
            :board-num="boardNumber"
            :category-list="categoryList"
            :post="post as Post"
            :view-route="mainViewName"
            :write-auth="writeAuth"
            @file-change="fileChange"
            @file-upload="fileUpload"
            @on-submit="onSubmit"
          />
        </div>
      </CCardBody>
    </CCard>
  </CContainer>
</template>
