import api from '@/api'
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { message, errorHandle } from '@/utils/helper'
import type {
  Board,
  PostCategory,
  PostLink,
  PostFile,
  PatchPost,
  Post,
  Comment as Cm,
  TrashPost as TP,
} from '@/store/types/board'
import { useAccount } from '@/store/pinia/account'

export type PostFilter = {
  board?: number
  project?: number | ''
  category?: number | ''
  is_notice?: boolean | ''
  is_blind?: boolean | ''
  user?: number | ''
  ordering?: string
  search?: string
  page?: number
}

export const useBoard = defineStore('board', () => {
  // state & getters
  const board = ref<Board | null>(null)
  const boardList = ref<Board[]>([])

  const fetchBoard = (pk: number) =>
    api
      .get(`/board/${pk}/`)
      .then(res => (board.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const fetchBoardList = (payload: { project?: string }) =>
    api
      .get(`/board/?project__slug=${payload.project ?? ''}`)
      .then(res => (boardList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const createBoard = (payload: Board, projId: string) =>
    api
      .post(`/board/`, { ...payload })
      .then(async res => {
        board.value = res.data
        await fetchBoardList({ project: projId })
      })
      .catch(err => errorHandle(err.response.data))
  const updateBoard = (pk: number, payload: any, projId: string) =>
    api
      .put(`/board/${pk}/`, payload)
      .then(async res => {
        board.value = res.data
        await fetchBoardList({ project: projId })
      })
      .catch(err => errorHandle(err.response.data))
  const deleteBoard = (pk: number, projId: string) =>
    api
      .delete(`/board/${pk}/`)
      .then(async res => await fetchBoardList({ project: projId }))
      .catch(err => errorHandle(err.response.data))

  const categoryList = ref<PostCategory[]>([])

  const fetchCategoryList = (board: number) =>
    api
      .get(`/post-category/?board=${board}`)
      .then(res => (categoryList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const createCategory = () => 2
  const updateCategory = () => 3
  const deleteCategory = () => 4

  const accStore = useAccount()
  const post = ref<Post | null>(null)
  const postList = ref<Post[]>([])
  const noticeList = ref<Post[]>([])
  const postCount = ref(0)
  const getPostNav = computed(() =>
    postList.value.map(p => ({
      pk: p.pk,
      prev_pk: p.prev_pk,
      next_pk: p.next_pk,
    })),
  )

  const postPages = (itemsPerPage: number) => Math.ceil(postCount.value / itemsPerPage)

  const fetchPost = async (pk: number) =>
    api
      .get(`/post/${pk}/`)
      .then(res => {
        post.value = res.data
        fetchCommentList({ post: pk })
      })
      .catch(err => errorHandle(err.response.data))

  const removePost = () => (post.value = null)

  const fetchPostList = async (payload: PostFilter) => {
    const { board, page } = payload
    let url = `/post/?page=${page ?? 1}`
    if (payload.board) url += `&board=${board}`
    if (payload.project) url += `&board_project=${payload.project}`
    if (payload.category) url += `&category=${payload.category}`
    if (payload.is_notice) url += `&is_notice=${payload.is_notice}`
    if (payload.is_blind) url += `&is_blind=${payload.is_blind}`
    if (payload.user) url += `&user=${payload.user}`
    if (payload.ordering) url += `&ordering=${payload.ordering}`
    if (payload.search) url += `&search=${payload.search}`

    return await api
      .get(url)
      .then(res => {
        postList.value = res.data.results
        postCount.value = res.data.count
      })
      .catch(err => errorHandle(err.response.data))
  }

  const config_headers = { headers: { 'Content-Type': 'multipart/form-data' } }

  const createPost = (
    payload: {
      form: FormData
    } & {
      isProject?: boolean
    },
  ) =>
    api
      .post(`/post/`, payload.form, config_headers)
      .then(async res => {
        await fetchPostList({
          board: res.data.board,
          page: 1,
        })
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const updatePost = (
    payload: {
      pk: number
      form: FormData
    } & {
      isProject?: boolean
    },
  ) =>
    api
      .put(`/post/${payload.pk}/`, payload.form, config_headers)
      .then(async res => {
        await fetchPostList({
          board: res.data.board,
          page: 1,
        })
        await fetchPost(res.data.pk)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const patchPost = async (
    payload: PatchPost & {
      filter?: PostFilter
    },
  ) => {
    const { filter, ...data } = payload
    return await api
      .patch(`/post/${data.pk}/`, data)
      .then(res =>
        fetchPostList({
          ...filter,
        }).then(() => fetchPost(res.data.pk)),
      )
      .catch(err => errorHandle(err.response.data))
  }

  const patchPostLike = (pk: number) =>
    api
      .patch(`/post-like/${pk}/`, { pk })
      .then(() => accStore.fetchProfile().then(() => fetchPost(pk)))
      .catch(err => errorHandle(err.response.data))

  const patchPostBlame = (pk: number) =>
    api
      .patch(`/post-blame/${pk}/`, { pk })
      .then(() => accStore.fetchProfile().then(() => fetchPost(pk)))
      .catch(err => errorHandle(err.response.data))

  const copyPost = (payload: { post: number; board: number }) =>
    api
      .post(`post/${payload.post}/copy/`, payload)
      .then(() => message('success', '', '게시물 복사가 완료되었습니다.'))
      .catch(err => errorHandle(err.response.data))

  const deletePost = (pk: number, filter: PostFilter) =>
    api
      .delete(`/post/${pk}/`)
      .then(() =>
        fetchPostList(filter).then(() =>
          message('warning', '', '해당 게시물이 휴지통으로 삭제되었습니다.'),
        ),
      )
      .catch(err => errorHandle(err.response.data))

  // state
  const trashPost = ref<TP | null>(null)
  const trashPostList = ref<TP[]>([])
  const trashPostCount = ref(0)

  const trashPostPages = (itemsPerPage: number) => Math.ceil(trashPostCount.value / itemsPerPage)

  const fetchTrashPost = async (pk: number) =>
    api
      .get(`/post-trash-can/${pk}/`)
      .then(res => {
        trashPost.value = res.data
        fetchCommentList({ post: pk })
      })
      .catch(err => errorHandle(err.response.data))

  const fetchTrashPostList = (page = 1) =>
    api
      .get(`/post-trash-can/?page=${page}`)
      .then(res => {
        trashPostList.value = res.data.results
        trashPostCount.value = res.data.count
      })
      .catch(err => errorHandle(err.response.data))

  const restorePost = (pk: number, isProject = false) =>
    api
      .patch(`/post-trash-can/${pk}/`)
      .then(res =>
        fetchPostList({
          board: res.data.board,
          page: 1,
        }).then(() =>
          fetchTrashPostList().then(() =>
            message('success', '', '해당 게시물 휴지통에서 복원되었습니다.'),
          ),
        ),
      )
      .catch(err => errorHandle(err.response.data))

  const link = ref<PostLink | null>(null)

  const fetchLink = (pk: number) =>
    api
      .get(`/post-link/${pk}/`)
      .then(res => (link.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const patchLink = (payload: PostLink) =>
    api
      .patch(`/post-link/${payload.pk}/`, payload)
      .then(res => fetchPost(res.data.post))
      .catch(err => errorHandle(err.response.data))

  const file = ref<PostFile | null>(null)

  const fetchFile = (pk: number) =>
    api
      .get(`/post-file/${pk}/`)
      .then(res => (file.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const patchFile = (payload: PostFile) =>
    api
      .patch(`/post-file/${payload.pk}/`, payload)
      .then(res => fetchPost(res.data.post))
      .catch(err => errorHandle(err.response.data))

  const comment = ref<Cm | null>(null)
  const commentList = ref<Cm[]>([])
  const commentCount = ref(0)

  const fetchComment = (pk: number) =>
    api
      .get(`/comment/${pk}/`)
      .then(res => (comment.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const fetchCommentList = async (payload: { post?: number; user?: number; page?: number }) => {
    const { post, user, page } = payload
    let url = `/comment/?page=${page ?? 1}`
    url = post ? `${url}&post=${post}&is_comment=true` : url
    url = user ? `${url}&user=${user}` : url

    return await api
      .get(url)
      .then(res => {
        commentList.value = res.data.results
        commentCount.value = res.data.count
      })
      .catch(err => errorHandle(err.response.data))
  }

  const createComment = (payload: Cm) =>
    api
      .post(`/comment/`, payload)
      .then(res => fetchPost(res.data.post.pk).then(() => message()))
      .catch(err => errorHandle(err.response.data))

  const patchComment = (payload: Cm) =>
    api
      .patch(`/comment/${payload.pk}/`, payload)
      .then(res => fetchPost(res.data.post.pk).then(() => message()))
      .catch(err => errorHandle(err.response.data))

  const patchCommentLike = (pk: number, post: number, page = 1) =>
    api
      .patch(`/comment-like/${pk}/`, { pk })
      .then(() => accStore.fetchProfile().then(() => fetchCommentList({ post, page })))
      .catch(err => errorHandle(err.response.data))

  const patchCommentBlame = (pk: number, post: number, page = 1) =>
    api
      .patch(`/comment-blame/${pk}/`, { pk })
      .then(() => accStore.fetchProfile().then(() => fetchCommentList({ post, page })))
      .catch(err => errorHandle(err.response.data))

  const deleteComment = (payload: { pk: number; post: number }) =>
    api
      .delete(`/comment/${payload.pk}/`)
      .then(() => fetchPost(payload.post).then(() => message()))
      .catch(err => errorHandle(err.response.data))

  const tag = ref(null)

  const fetchTag = () => 1
  const createTag = () => 2
  const updateTag = () => 3
  const deleteTag = () => 4

  return {
    board,
    boardList,

    fetchBoard,
    fetchBoardList,
    createBoard,
    updateBoard,
    deleteBoard,

    categoryList,

    fetchCategoryList,
    createCategory,
    updateCategory,
    deleteCategory,

    post,
    postList,
    noticeList,
    postCount,
    getPostNav,

    postPages,
    fetchPost,
    removePost,
    fetchPostList,
    createPost,
    updatePost,
    patchPost,
    patchPostLike,
    patchPostBlame,
    copyPost,
    deletePost,

    trashPost,
    trashPostList,
    trashPostCount,

    trashPostPages,
    fetchTrashPost,
    fetchTrashPostList,
    restorePost,

    link,
    fetchLink,
    patchLink,

    file,
    fetchFile,
    patchFile,

    comment,
    commentList,
    commentCount,

    fetchComment,
    fetchCommentList,
    createComment,
    patchComment,
    patchCommentLike,
    patchCommentBlame,
    deleteComment,

    tag,

    fetchTag,
    createTag,
    updateTag,
    deleteTag,
  }
})
