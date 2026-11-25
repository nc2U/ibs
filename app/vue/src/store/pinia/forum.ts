import api from '@/api'
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { message, errorHandle } from '@/utils/helper'
import type {
  Forum,
  PostCategory,
  PostFile,
  PatchPost,
  Post,
  Comment as Cm,
  TrashPost as TP,
} from '@/store/types/forum'
import { useAccount } from '@/store/pinia/account'

export type PostFilter = {
  forum?: number
  project?: number | ''
  category?: number | ''
  is_notice?: boolean | ''
  is_faq?: boolean | ''
  is_blind?: boolean | ''
  user?: number | ''
  ordering?: string
  search?: string
  page?: number
}

export const useForum = defineStore('forum', () => {
  // state & getters
  const forum = ref<Forum | null>(null)
  const forumList = ref<Forum[]>([])

  const fetchForum = (pk: number) =>
    api
      .get(`/forum/${pk}/`)
      .then(res => (forum.value = res.data))
      .catch(err => errorHandle(err))

  const fetchForumList = (payload: { project?: string }) => {
    const params = new URLSearchParams()
    params.append('limit', '500')
    if (payload.project) params.append('project__slug', payload.project)
    return api
      .get(`/forum/?${params.toString()}`)
      .then(res => (forumList.value = res.data.results ?? []))
      .catch(err => errorHandle(err))
  }

  const createForum = (payload: Forum, projId: string) =>
    api
      .post(`/forum/`, payload)
      .then(async res => {
        forum.value = res.data
        await fetchForumList({ project: projId })
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })
  const updateForum = (pk: number, payload: Partial<Forum>, projId: string) =>
    api
      .put(`/forum/${pk}/`, payload)
      .then(async res => {
        forum.value = res.data
        await fetchForumList({ project: projId })
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })
  const deleteForum = (pk: number, projId: string): Promise<boolean> =>
    api
      .delete(`/forum/${pk}/`)
      .then(async () => {
        await fetchForumList({ project: projId })
        return true
      })
      .catch(err => {
        errorHandle(err)
        return false
      })

  const categoryList = ref<PostCategory[]>([])

  const fetchCategoryList = (forumId: number) =>
    api
      .get(`/post-category/?forum=${forumId}&limit=500`)
      .then(res => (categoryList.value = res.data.results ?? []))
      .catch(err => errorHandle(err))

  const createCategory = (payload: PostCategory, projId: string = '') =>
    api
      .post(`/post-category/?project=${projId}`, payload)
      .then(async res => {
        await fetchCategoryList(res.data.forum)
        message()
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const updateCategory = (payload: PostCategory, projId: string = '') =>
    api
      .put(`/post-category/${payload.pk}/?project=${projId}`, payload)
      .then(async res => {
        await fetchCategoryList(res.data.forum)
        message()
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const deleteCategory = (payload: { pk: number; forum: number }, projId: string = '') =>
    api
      .delete(`/post-category/${payload.pk}/?project=${projId}`)
      .then(async () => {
        await fetchCategoryList(payload.forum)
        message('warning', '', '카테고리가 삭제되었습니다.')
        return true
      })
      .catch(err => {
        errorHandle(err)
        return false
      })

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
      .then(async res => {
        post.value = res.data
        await fetchCommentList({ post: pk })
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const removePost = () => (post.value = null)
  const clearForumViewState = () => {
    forum.value = null
    post.value = null
    postList.value = []
    postCount.value = 0
    commentList.value = []
    commentCount.value = 0
    categoryList.value = []
  }

  const fetchPostList = async (payload: PostFilter) => {
    const params = new URLSearchParams()
    params.append('page', String(payload.page ?? 1))
    if (payload.forum) params.append('forum', String(payload.forum))
    if (payload.project) params.append('forum__project', String(payload.project))
    if (payload.category) params.append('category', String(payload.category))
    if (payload.is_notice) params.append('is_notice', String(payload.is_notice))
    if (payload.is_faq !== undefined && payload.is_faq !== '') {
      params.append('is_faq', String(payload.is_faq))
    } else {
      // 일반 게시판 기본값: is_faq=false 인 일반 게시물만 조회
      params.append('is_faq', 'false')
    }
    if (payload.is_blind) params.append('is_blind', String(payload.is_blind))
    if (payload.user) params.append('creator', String(payload.user))
    if (payload.ordering) params.append('ordering', payload.ordering)
    if (payload.search) params.append('search', payload.search)

    return await api
      .get(`/post/?${params.toString()}`)
      .then(res => {
        postList.value = res.data.results
        postCount.value = res.data.count
      })
      .catch(err => errorHandle(err))
  }

  const config_headers = { headers: { 'Content-Type': 'multipart/form-data' } }

  const createPost = (
    payload: {
      form: FormData
    } & {
      isProject?: boolean
    },
    projId: string = '',
  ) =>
    api
      .post(`/post/?project=${projId}`, payload.form, config_headers)
      .then(async res => {
        await fetchPostList({
          forum: res.data.forum,
          page: 1,
        })
        message()
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const updatePost = (
    payload: {
      pk: number
      form: FormData
    } & {
      isProject?: boolean
    },
    projId: string = '',
  ) =>
    api
      .put(`/post/${payload.pk}/?project=${projId}`, payload.form, config_headers)
      .then(async res => {
        await fetchPostList({
          forum: res.data.forum,
          page: 1,
        })
        await fetchPost(res.data.pk)
        message()
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const patchPost = async (
    payload: PatchPost & {
      filter?: PostFilter
    },
    projId: string = '',
  ) => {
    const { filter, ...data } = payload
    return await api
      .patch(`/post/${data.pk}/?project=${projId}`, data)
      .then(res =>
        fetchPostList({
          ...filter,
        }).then(() => fetchPost(res.data.pk)),
      )
      .catch(err => errorHandle(err))
  }

  const hitPost = (pk: number) =>
    api
      .post(`/post/${pk}/hit/`, { pk })
      .then(res => {
        if (post.value && post.value.pk === pk) {
          post.value.hit = res.data.hit
        }
      })
      .catch(err => errorHandle(err))

  const patchPostLike = (pk: number) =>
    api
      .patch(`/post-like/${pk}/`, { pk })
      .then(() => accStore.fetchProfile().then(() => fetchPost(pk)))
      .catch(err => errorHandle(err))

  const patchPostBlame = (pk: number) =>
    api
      .patch(`/post-blame/${pk}/`, { pk })
      .then(() => accStore.fetchProfile().then(() => fetchPost(pk)))
      .catch(err => errorHandle(err))

  const copyPost = (payload: { post: number; forum: number }, projId: string = '') =>
    api
      .post(`/post/${payload.post}/copy/?project=${projId}`, payload)
      .then(() => message('success', '', '게시물 복사가 완료되었습니다.'))
      .catch(err => errorHandle(err))

  const deletePost = (pk: number, filter: PostFilter, projId: string = ''): Promise<boolean> =>
    api
      .delete(`/post/${pk}/?project=${projId}`)
      .then(async () => {
        post.value = null
        await fetchPostList(filter)
        message('warning', '', '해당 게시물이 휴지통으로 삭제되었습니다.')
        return true
      })
      .catch(err => {
        errorHandle(err)
        return false
      })

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
      .catch(err => errorHandle(err))

  const fetchTrashPostList = (page = 1) =>
    api
      .get(`/post-trash-can/?page=${page}`)
      .then(res => {
        trashPostList.value = res.data.results
        trashPostCount.value = res.data.count
      })
      .catch(err => errorHandle(err))

  const restorePost = (pk: number) =>
    api
      .patch(`/post-trash-can/${pk}/`)
      .then(res =>
        fetchPostList({
          forum: res.data.forum,
          page: 1,
        }).then(() =>
          fetchTrashPostList().then(() =>
            message('success', '', '해당 게시물 휴지통에서 복원되었습니다.'),
          ),
        ),
      )
      .catch(err => errorHandle(err))

  const file = ref<PostFile | null>(null)

  const fetchFile = (pk: number) =>
    api
      .get(`/post-file/${pk}/`)
      .then(res => (file.value = res.data))
      .catch(err => errorHandle(err))

  const patchFile = (payload: PostFile) =>
    api
      .patch(`/post-file/${payload.pk}/`, payload)
      .then(res => fetchPost(res.data.post))
      .catch(err => errorHandle(err))

  const comment = ref<Cm | null>(null)
  const commentList = ref<Cm[]>([])
  const commentCount = ref(0)

  const fetchComment = (pk: number) =>
    api
      .get(`/comment/${pk}/`)
      .then(res => (comment.value = res.data))
      .catch(err => errorHandle(err))

  const fetchCommentList = async (payload: { post?: number; user?: number; page?: number }) => {
    const params = new URLSearchParams()
    params.append('page', String(payload.page ?? 1))
    if (payload.post) {
      params.append('post', String(payload.post))
      params.append('is_comment', 'true')
    }
    if (payload.user) params.append('creator', String(payload.user))

    return await api
      .get(`/comment/?${params.toString()}`)
      .then(res => {
        commentList.value = res.data.results
        commentCount.value = res.data.count
      })
      .catch(err => errorHandle(err))
  }

  const createComment = (payload: Cm, projId: string = '') =>
    api
      .post(`/comment/?project=${projId}`, payload)
      .then(res => fetchPost(res.data.post.pk).then(() => message()))
      .catch(err => errorHandle(err))

  const patchComment = (payload: Cm, projId: string = '') =>
    api
      .patch(`/comment/${payload.pk}/?project=${projId}`, payload)
      .then(res => fetchPost(res.data.post.pk).then(() => message()))
      .catch(err => errorHandle(err))

  const patchCommentLike = (pk: number, post: number, page = 1) =>
    api
      .patch(`/comment-like/${pk}/`, { pk })
      .then(() => accStore.fetchProfile().then(() => fetchCommentList({ post, page })))
      .catch(err => errorHandle(err))

  const patchCommentBlame = (pk: number, post: number, page = 1) =>
    api
      .patch(`/comment-blame/${pk}/`, { pk })
      .then(() => accStore.fetchProfile().then(() => fetchCommentList({ post, page })))
      .catch(err => errorHandle(err))

  const deleteComment = (payload: { pk: number; post: number }, projId: string = '') =>
    api
      .delete(`/comment/${payload.pk}/?project=${projId}`)
      .then(() =>
        fetchPost(payload.post).then(() => message('warning', '', '해당 댓글이 삭제되었습니다.')),
      )
      .catch(err => errorHandle(err))

  const tag = ref(null)

  const fetchTag = () => 1
  const createTag = () => 2
  const updateTag = () => 3
  const deleteTag = () => 4

  return {
    forum,
    forumList,

    fetchForum,
    fetchForumList,
    createForum,
    updateForum,
    deleteForum,

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
    clearForumViewState,
    fetchPostList,
    createPost,
    updatePost,
    patchPost,
    hitPost,
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
