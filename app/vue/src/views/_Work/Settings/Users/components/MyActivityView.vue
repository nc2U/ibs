<script lang="ts" setup>
import { computed, reactive, ref, watch } from 'vue'
import type { RouteLocationRaw } from 'vue-router'
import { useAccount } from '@/store/pinia/account'
import { type DocsFilter, useDocs } from '@/store/pinia/docs'
import { type PostFilter, useForum } from '@/store/pinia/forum'
import type { Docs } from '@/store/types/docs'
import type { Comment, Post } from '@/store/types/forum'
import { cutString, numFormat, timeFormat } from '@/utils/baseMixins'
import { bgLight, TableSecondary } from '@/utils/cssMixins'
import Pagination from '@/components/Pagination'
import NoData from '@/components/NoData/Index.vue'
import MyMenuLinks from './atomicViews/MyMenuLinks.vue'

type ActivityTab = 'docs' | 'post' | 'comment'

const accStore = useAccount()
const docStore = useDocs()
const forumStore = useForum()

const userInfo = computed(() => accStore.userInfo)

const activeTab = ref<ActivityTab>('docs')
const loading = ref(false)

// 1. 내 등록 문서
const docsFilter = reactive<DocsFilter>({
  creator: '',
  ordering: '-created',
  search: '',
  page: 1,
})

const docsList = computed(() => docStore.docsList)
const docsCount = computed(() => docStore.docsCount)
const docsTotalPages = computed(() => docStore.docsPages(10))

// 2. 내 작성글 & 댓글
const postFilter = reactive<PostFilter>({
  user: '',
  ordering: '-created',
  search: '',
  page: 1,
})
const commentPage = ref(1)

const postList = computed(() => forumStore.postList)
const postCount = computed(() => forumStore.postCount)
const postTotalPages = computed(() => forumStore.postPages(20))

const commentList = computed(() => forumStore.commentList)
const commentCount = computed(() => forumStore.commentCount)
const commentTotalPages = computed(() => Math.ceil(commentCount.value / 10))

const fetchMyDocs = async () => {
  if (!userInfo.value?.pk) return
  docsFilter.creator = userInfo.value.pk
  loading.value = true
  try {
    await docStore.fetchDocsList({ ...docsFilter })
  } finally {
    loading.value = false
  }
}

const fetchMyPosts = async () => {
  if (!userInfo.value?.pk) return
  postFilter.user = userInfo.value.pk
  loading.value = true
  try {
    await forumStore.fetchPostList({ ...postFilter })
  } finally {
    loading.value = false
  }
}

const fetchMyComments = async () => {
  if (!userInfo.value?.pk) return
  loading.value = true
  try {
    await forumStore.fetchCommentList({
      user: userInfo.value.pk,
      page: commentPage.value,
    })
  } finally {
    loading.value = false
  }
}

watch(
  () => userInfo.value?.pk,
  async pk => {
    if (!pk) return
    docsFilter.creator = pk
    postFilter.user = pk
    loading.value = true
    try {
      await Promise.all([
        docStore.fetchDocsList({ ...docsFilter }),
        forumStore.fetchPostList({ ...postFilter }),
        forumStore.fetchCommentList({ user: pk, page: commentPage.value }),
      ])
    } finally {
      loading.value = false
    }
  },
  { immediate: true },
)

const isDocsFilterDirty = computed(
  () => docsFilter.ordering !== '-created' || (docsFilter.search ?? '') !== '',
)
const isPostFilterDirty = computed(
  () => postFilter.ordering !== '-created' || (postFilter.search ?? '') !== '',
)

const resetDocsFilter = () => {
  docsFilter.ordering = '-created'
  docsFilter.search = ''
  docsFilter.page = 1
  fetchMyDocs()
}

const resetPostFilter = () => {
  postFilter.ordering = '-created'
  postFilter.search = ''
  postFilter.page = 1
  fetchMyPosts()
}

const onDocsPageChange = (p: number) => {
  docsFilter.page = p
  fetchMyDocs()
}

const onPostPageChange = (p: number) => {
  postFilter.page = p
  fetchMyPosts()
}

const onCommentPageChange = (p: number) => {
  commentPage.value = p
  fetchMyComments()
}

const getDocTarget = (doc: Docs): RouteLocationRaw | null => {
  if (!doc.pk) return null
  if (doc.proj_type === '2') {
    const routeName = doc.doc_type === 2 ? '소송 문서 관리 - 보기' : '일반 문서 관리 - 보기'
    return { name: routeName, params: { docsId: doc.pk } }
  }
  if (doc.project?.slug) {
    return { name: '(문서) - 보기', params: { projId: doc.project.slug, docId: doc.pk } }
  }
  return null
}

const getPostTarget = (post: Post): RouteLocationRaw | null => {
  if (!post.pk || !post.forum || !post.project_slug) return null
  return {
    name: '(게시판) - 게시물 보기',
    params: { projId: post.project_slug, forumId: post.forum, postId: post.pk },
  }
}

const getCommentTarget = (cmt: Comment): RouteLocationRaw | null => {
  const post = cmt.post
  if (!post?.pk || !post.forum || !post.project_slug) return null
  return {
    name: '(게시판) - 게시물 보기',
    params: { projId: post.project_slug, forumId: post.forum, postId: post.pk },
  }
}
</script>

<template>
  <div>
    <CRow class="py-2 align-items-center">
      <CCol class="mb-2">
        <span class="h5 me-2">내 작성 활동</span>
      </CCol>
      <MyMenuLinks current="activity" />
    </CRow>

    <CCard class="mb-4">
      <CCardHeader class="d-flex flex-wrap justify-content-between align-items-center gap-2">
        <v-btn-toggle
          v-model="activeTab"
          mandatory
          density="compact"
          color="primary"
          variant="outlined"
          class="text-muted"
        >
          <v-btn value="docs" size="small"> 내 등록 문서 ({{ numFormat(docsCount) }}) </v-btn>
          <v-btn value="post" size="small"> 내 작성글 ({{ numFormat(postCount) }}) </v-btn>
          <v-btn value="comment" size="small"> 내 댓글 ({{ numFormat(commentCount) }}) </v-btn>
        </v-btn-toggle>
      </CCardHeader>

      <CCardBody>
        <v-progress-linear v-if="loading" indeterminate color="primary" class="mb-3" />

        <!-- 1. 내 등록 문서 -->
        <template v-if="activeTab === 'docs'">
          <CCallout color="secondary" class="pb-2 mb-4" :class="bgLight">
            <CRow class="align-items-center">
              <CCol md="4" lg="3" class="mb-2">
                <CFormSelect
                  v-model="docsFilter.ordering"
                  @change="
                    () => {
                      docsFilter.page = 1
                      fetchMyDocs()
                    }
                  "
                >
                  <option value="-created">작성일자 내림차순</option>
                  <option value="created">작성일자 오름차순</option>
                  <option value="-execution_date">발행일자 내림차순</option>
                  <option value="execution_date">발행일자 오름차순</option>
                  <option value="-hit">조회수 내림차순</option>
                  <option value="hit">조회수 오름차순</option>
                </CFormSelect>
              </CCol>

              <CCol md="5" lg="4" class="ms-auto mb-2">
                <CInputGroup class="flex-nowrap">
                  <CFormInput
                    v-model="docsFilter.search"
                    placeholder="제목, 내용, 링크, 파일명"
                    @keydown.enter="
                      () => {
                        docsFilter.page = 1
                        fetchMyDocs()
                      }
                    "
                  />
                  <CInputGroupText
                    class="pointer"
                    @click="
                      () => {
                        docsFilter.page = 1
                        fetchMyDocs()
                      }
                    "
                  >
                    검색
                  </CInputGroupText>
                </CInputGroup>
              </CCol>
            </CRow>
            <CRow class="align-items-center">
              <CCol class="ps-3">
                <strong>문서 조회 결과 : {{ numFormat(docsCount) }}건</strong>
              </CCol>
              <CCol v-if="isDocsFilterDirty" class="text-end">
                <v-btn color="info" size="small" @click="resetDocsFilter">검색조건 초기화</v-btn>
              </CCol>
            </CRow>
          </CCallout>

          <CTable v-if="docsList.length > 0" hover responsive align="middle">
            <colgroup>
              <col style="width: 7%" />
              <col style="width: 22%" />
              <col style="width: 15%" />
              <col style="width: 38%" />
              <col style="width: 18%" />
            </colgroup>
            <CTableHead>
              <CTableRow :color="TableSecondary" class="text-center border-top">
                <CTableHeaderCell scope="col">번호</CTableHeaderCell>
                <CTableHeaderCell scope="col">소속 · 구분</CTableHeaderCell>
                <CTableHeaderCell scope="col">분류</CTableHeaderCell>
                <CTableHeaderCell scope="col">제목</CTableHeaderCell>
                <CTableHeaderCell scope="col">등록일시</CTableHeaderCell>
              </CTableRow>
            </CTableHead>
            <CTableBody>
              <CTableRow v-for="doc in docsList" :key="doc.pk" class="text-center">
                <CTableDataCell>{{ doc.pk }}</CTableDataCell>
                <CTableDataCell class="text-start">
                  {{ doc.project?.name ? `${doc.project.name} · ${doc.type_name}` : doc.type_name }}
                </CTableDataCell>
                <CTableDataCell>{{ doc.cate_name || '-' }}</CTableDataCell>
                <CTableDataCell class="text-start">
                  <router-link v-if="getDocTarget(doc)" :to="getDocTarget(doc)!">
                    {{ cutString(doc.title, 50) }}
                  </router-link>
                  <span v-else>{{ cutString(doc.title, 50) }}</span>
                  <v-chip
                    v-if="doc.is_new"
                    color="warning"
                    variant="flat"
                    size="x-small"
                    class="ms-2"
                  >
                    new
                  </v-chip>
                </CTableDataCell>
                <CTableDataCell class="text-medium-emphasis">
                  {{ timeFormat(doc.created ?? '') }}
                </CTableDataCell>
              </CTableRow>
            </CTableBody>
          </CTable>
          <NoData v-else-if="!loading" />

          <CRow v-if="docsTotalPages > 1" class="mt-3">
            <CCol>
              <Pagination
                :active-page="docsFilter.page || 1"
                :limit="8"
                :pages="docsTotalPages"
                @active-page-change="onDocsPageChange"
              />
            </CCol>
          </CRow>
        </template>

        <!-- 2. 내 작성글 -->
        <template v-else-if="activeTab === 'post'">
          <CCallout color="secondary" class="pb-2 mb-4" :class="bgLight">
            <CRow class="align-items-center">
              <CCol md="4" lg="3" class="mb-2">
                <CFormSelect
                  v-model="postFilter.ordering"
                  @change="
                    () => {
                      postFilter.page = 1
                      fetchMyPosts()
                    }
                  "
                >
                  <option value="-created">작성일자 내림차순</option>
                  <option value="created">작성일자 오름차순</option>
                  <option value="-hit">조회수 내림차순</option>
                  <option value="hit">조회수 오름차순</option>
                </CFormSelect>
              </CCol>

              <CCol md="5" lg="4" class="ms-auto mb-2">
                <CInputGroup class="flex-nowrap">
                  <CFormInput
                    v-model="postFilter.search"
                    placeholder="제목, 내용, 파일명"
                    @keydown.enter="
                      () => {
                        postFilter.page = 1
                        fetchMyPosts()
                      }
                    "
                  />
                  <CInputGroupText
                    class="pointer"
                    @click="
                      () => {
                        postFilter.page = 1
                        fetchMyPosts()
                      }
                    "
                  >
                    검색
                  </CInputGroupText>
                </CInputGroup>
              </CCol>
            </CRow>
            <CRow class="align-items-center">
              <CCol class="ps-3">
                <strong>게시물 조회 결과 : {{ numFormat(postCount) }}건</strong>
              </CCol>
              <CCol v-if="isPostFilterDirty" class="text-end">
                <v-btn color="info" size="small" @click="resetPostFilter">검색조건 초기화</v-btn>
              </CCol>
            </CRow>
          </CCallout>

          <CTable v-if="postList.length > 0" hover responsive align="middle">
            <colgroup>
              <col style="width: 7%" />
              <col style="width: 24%" />
              <col style="width: 51%" />
              <col style="width: 18%" />
            </colgroup>
            <CTableHead>
              <CTableRow :color="TableSecondary" class="text-center border-top">
                <CTableHeaderCell scope="col">번호</CTableHeaderCell>
                <CTableHeaderCell scope="col">워크스페이스 · 게시판</CTableHeaderCell>
                <CTableHeaderCell scope="col">제목</CTableHeaderCell>
                <CTableHeaderCell scope="col">등록일시</CTableHeaderCell>
              </CTableRow>
            </CTableHead>
            <CTableBody>
              <CTableRow v-for="post in postList" :key="post.pk" class="text-center">
                <CTableDataCell>{{ post.pk }}</CTableDataCell>
                <CTableDataCell class="text-start">
                  {{
                    post.project_name
                      ? `${post.project_name} · ${post.forum_name || ''}`
                      : post.forum_name || '-'
                  }}
                </CTableDataCell>
                <CTableDataCell class="text-start">
                  <router-link v-if="getPostTarget(post)" :to="getPostTarget(post)!">
                    {{ cutString(post.title, 50) }}
                  </router-link>
                  <span v-else>{{ cutString(post.title, 50) }}</span>
                  <v-chip
                    v-if="post.is_new"
                    color="warning"
                    variant="flat"
                    size="x-small"
                    class="ms-2"
                  >
                    new
                  </v-chip>
                </CTableDataCell>
                <CTableDataCell class="text-medium-emphasis">
                  {{ timeFormat(post.created ?? '') }}
                </CTableDataCell>
              </CTableRow>
            </CTableBody>
          </CTable>
          <NoData v-else-if="!loading" />

          <CRow v-if="postTotalPages > 1" class="mt-3">
            <CCol>
              <Pagination
                :active-page="postFilter.page || 1"
                :limit="8"
                :pages="postTotalPages"
                @active-page-change="onPostPageChange"
              />
            </CCol>
          </CRow>
        </template>

        <!-- 3. 내 댓글 -->
        <template v-else>
          <div class="mb-3 ps-1">
            <strong>댓글 조회 결과 : {{ numFormat(commentCount) }}건</strong>
          </div>

          <CTable v-if="commentList.length > 0" hover responsive align="middle">
            <colgroup>
              <col style="width: 8%" />
              <col style="width: 24%" />
              <col style="width: 50%" />
              <col style="width: 18%" />
            </colgroup>
            <CTableHead>
              <CTableRow :color="TableSecondary" class="text-center border-top">
                <CTableHeaderCell scope="col">번호</CTableHeaderCell>
                <CTableHeaderCell scope="col">워크스페이스 · 게시판</CTableHeaderCell>
                <CTableHeaderCell scope="col">댓글 내용</CTableHeaderCell>
                <CTableHeaderCell scope="col">등록일시</CTableHeaderCell>
              </CTableRow>
            </CTableHead>
            <CTableBody>
              <CTableRow v-for="cmt in commentList" :key="cmt.pk" class="text-center">
                <CTableDataCell>{{ cmt.pk }}</CTableDataCell>
                <CTableDataCell class="text-start">
                  {{
                    cmt.post?.project_name
                      ? `${cmt.post.project_name} · ${cmt.post.forum_name || ''}`
                      : cmt.post?.forum_name || '-'
                  }}
                </CTableDataCell>
                <CTableDataCell class="text-start">
                  <router-link v-if="getCommentTarget(cmt)" :to="getCommentTarget(cmt)!">
                    {{ cutString(cmt.content, 60) }}
                  </router-link>
                  <span v-else>{{ cutString(cmt.content, 60) }}</span>
                </CTableDataCell>
                <CTableDataCell class="text-medium-emphasis">
                  {{ timeFormat(cmt.created ?? '') }}
                </CTableDataCell>
              </CTableRow>
            </CTableBody>
          </CTable>
          <NoData v-else-if="!loading" />

          <CRow v-if="commentTotalPages > 1" class="mt-3">
            <CCol>
              <Pagination
                :active-page="commentPage"
                :limit="8"
                :pages="commentTotalPages"
                @active-page-change="onCommentPageChange"
              />
            </CCol>
          </CRow>
        </template>
      </CCardBody>
    </CCard>
  </div>
</template>
