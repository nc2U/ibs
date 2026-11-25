<script lang="ts" setup>
import { computed, ref, watch } from 'vue'
import type { RouteLocationRaw } from 'vue-router'
import { useAccount } from '@/store/pinia/account'
import type { Scrape } from '@/store/types/accounts'
import { cutString, numFormat, timeFormat } from '@/utils/baseMixins'
import { TableSecondary } from '@/utils/cssMixins'
import Pagination from '@/components/Pagination'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import NoData from '@/components/NoData/Index.vue'
import MyMenuLinks from './atomicViews/MyMenuLinks.vue'

type ScrapeSort = 'docs' | 'post'

const accStore = useAccount()
const userInfo = computed(() => accStore.userInfo)

const sort = ref<ScrapeSort>('docs')
const page = ref<number>(1)
const loading = ref<boolean>(false)

// 문서 스크랩
const docScrapeList = computed(() => accStore.docScrapeList)
const docScrapeCount = computed(() => accStore.docScrapeCount)

// 게시글 스크랩
const postScrapeList = computed(() => accStore.scrapeList)
const postScrapeCount = computed(() => accStore.scrapeCount)

const activeList = computed(() =>
  sort.value === 'docs' ? docScrapeList.value : postScrapeList.value,
)
const activeCount = computed(() =>
  sort.value === 'docs' ? docScrapeCount.value : postScrapeCount.value,
)
const totalPages = computed(() =>
  sort.value === 'docs' ? accStore.docScrapePages(10) : accStore.scrapePages(10),
)

// 인라인 별칭 수정 상태
const editingId = ref<number | null>(null)
const editTitle = ref('')

// 삭제 모달 상태
const refConfirmModal = ref<InstanceType<typeof ConfirmModal> | null>(null)
const pendingDeletePk = ref<number | null>(null)

const fetchCurrentList = async (targetPage = page.value) => {
  if (!userInfo.value?.pk) return
  loading.value = true
  try {
    if (sort.value === 'docs') {
      await accStore.fetchDocScrapeList(targetPage)
    } else {
      await accStore.fetchScrapeList(targetPage)
    }
  } finally {
    loading.value = false
  }
}

watch(
  () => userInfo.value?.pk,
  async pk => {
    if (!pk) return
    loading.value = true
    try {
      await Promise.all([accStore.fetchDocScrapeList(1), accStore.fetchScrapeList(1)])
    } finally {
      loading.value = false
    }
  },
  { immediate: true },
)

watch(sort, () => {
  page.value = 1
  editingId.value = null
  editTitle.value = ''
  fetchCurrentList(1)
})

const onPageSelect = (p: number) => {
  page.value = p
  fetchCurrentList(p)
}

const getDocTarget = (item: Scrape): RouteLocationRaw | null => {
  const doc = item.docs
  if (!doc?.pk) return null
  if (doc.proj_sort === '2') {
    const routeName = doc.doc_type === 2 ? '소송 문서 관리 - 보기' : '일반 문서 관리 - 보기'
    return { name: routeName, params: { docsId: doc.pk } }
  }
  if (doc.project_slug) {
    return { name: '(문서) - 보기', params: { projId: doc.project_slug, docId: doc.pk } }
  }
  return null
}

const getDocLocationLabel = (item: Scrape): string => {
  const doc = item.docs
  if (!doc) return '-'
  if (doc.project_name) return `${doc.project_name} · ${doc.type_name}`
  return doc.type_name || '-'
}

const getPostTarget = (item: Scrape): RouteLocationRaw | null => {
  const post = item.post
  if (!post?.pk || !post.forum || !post.project_slug) return null
  return {
    name: '(게시판) - 게시물 보기',
    params: { projId: post.project_slug, forumId: post.forum, postId: post.pk },
  }
}

const startEdit = (item: Scrape) => {
  if (!item.pk) return
  if (editingId.value === item.pk) {
    editingId.value = null
    editTitle.value = ''
    return
  }
  editingId.value = item.pk
  editTitle.value =
    item.title || (sort.value === 'docs' ? item.docs?.title : item.post?.title) || ''
}

const submitTitle = async (item: Scrape) => {
  if (!item.pk) return
  const nextTitle = editTitle.value.trim()
  if (sort.value === 'docs') {
    await accStore.patchDocScrape(item.pk, nextTitle)
  } else {
    await accStore.patchScrape(item.pk, nextTitle)
  }
  if (page.value > 1) await fetchCurrentList(page.value)
  editingId.value = null
  editTitle.value = ''
}

const openDeleteModal = (item: Scrape) => {
  if (!item.pk) return
  pendingDeletePk.value = item.pk
  refConfirmModal.value?.callModal(
    '스크랩 삭제 확인',
    '선택한 스크랩 항목을 보관함에서 삭제하시겠습니까?',
    'mdi-bookmark-remove-outline',
    'warning',
    '삭제',
    'danger',
  )
}

const confirmDelete = async () => {
  const pk = pendingDeletePk.value
  if (!pk) return
  if (sort.value === 'docs') {
    await accStore.deleteDocScrape(pk)
  } else {
    await accStore.deleteScrape(pk)
  }
  if (page.value > 1) await fetchCurrentList(page.value)
  pendingDeletePk.value = null
  refConfirmModal.value?.close()
}
</script>

<template>
  <div>
    <CRow class="py-2 align-items-center">
      <CCol class="mb-2">
        <span class="h5 me-2">내 스크랩</span>
      </CCol>
      <MyMenuLinks current="scrap" />
    </CRow>

    <CCard class="mb-4">
      <CCardHeader class="d-flex flex-wrap justify-content-between align-items-center gap-2">
        <div class="d-flex align-items-center gap-2">
          <v-btn-toggle
            v-model="sort"
            mandatory
            density="compact"
            color="primary"
            variant="outlined"
            class="text-muted"
          >
            <v-btn value="docs" size="small"> 문서 스크랩 ({{ numFormat(docScrapeCount) }}) </v-btn>
            <v-btn value="post" size="small">
              게시글 스크랩 ({{ numFormat(postScrapeCount) }})
            </v-btn>
          </v-btn-toggle>
        </div>
        <span class="text-body-2 text-medium-emphasis">
          총 <strong>{{ numFormat(activeCount) }}</strong> 건
        </span>
      </CCardHeader>

      <CCardBody>
        <v-progress-linear v-if="loading" indeterminate color="primary" class="mb-3" />

        <CTable v-if="activeList.length > 0" hover responsive align="middle">
          <colgroup>
            <col style="width: 7%" />
            <col style="width: 23%" />
            <col style="width: 38%" />
            <col style="width: 16%" />
            <col style="width: 8%" />
            <col style="width: 8%" />
          </colgroup>

          <CTableHead>
            <CTableRow :color="TableSecondary" class="text-center border-top">
              <CTableHeaderCell scope="col">번호</CTableHeaderCell>
              <CTableHeaderCell scope="col">
                {{ sort === 'docs' ? '소속 · 구분' : '워크스페이스 · 게시판' }}
              </CTableHeaderCell>
              <CTableHeaderCell scope="col">제목</CTableHeaderCell>
              <CTableHeaderCell scope="col">보관일시</CTableHeaderCell>
              <CTableHeaderCell scope="col">별칭수정</CTableHeaderCell>
              <CTableHeaderCell scope="col">보관취소</CTableHeaderCell>
            </CTableRow>
          </CTableHead>

          <CTableBody>
            <CTableRow v-for="item in activeList" :key="item.pk" class="text-center">
              <CTableDataCell>
                {{ sort === 'docs' ? item.docs?.pk : item.post?.pk }}
              </CTableDataCell>

              <CTableDataCell class="text-start">
                <template v-if="sort === 'docs'">
                  <span class="text-body-2">{{ getDocLocationLabel(item) }}</span>
                </template>
                <template v-else>
                  <span class="text-body-2">
                    {{
                      item.post?.project_name
                        ? `${item.post.project_name} · ${item.post.forum_name}`
                        : item.post?.forum_name || '-'
                    }}
                  </span>
                </template>
              </CTableDataCell>

              <CTableDataCell class="text-start">
                <template v-if="editingId === item.pk">
                  <CInputGroup size="sm">
                    <CFormInput
                      v-model="editTitle"
                      placeholder="스크랩 별칭을 입력하세요"
                      @keydown.enter="submitTitle(item)"
                    />
                    <v-btn color="info" size="small" variant="flat" @click="submitTitle(item)">
                      저장
                    </v-btn>
                    <v-btn color="secondary" size="small" variant="text" @click="editingId = null">
                      취소
                    </v-btn>
                  </CInputGroup>
                </template>
                <template v-else>
                  <template v-if="sort === 'docs'">
                    <router-link v-if="getDocTarget(item)" :to="getDocTarget(item)!">
                      {{ cutString(item.title || item.docs?.title || '-', 55) }}
                    </router-link>
                    <span v-else>{{ cutString(item.title || item.docs?.title || '-', 55) }}</span>
                  </template>
                  <template v-else>
                    <router-link v-if="getPostTarget(item)" :to="getPostTarget(item)!">
                      {{ cutString(item.title || item.post?.title || '-', 55) }}
                    </router-link>
                    <span v-else>{{ cutString(item.title || item.post?.title || '-', 55) }}</span>
                  </template>
                </template>
              </CTableDataCell>

              <CTableDataCell class="text-medium-emphasis">
                {{ timeFormat(item.created ?? '') }}
              </CTableDataCell>

              <CTableDataCell>
                <v-btn
                  density="compact"
                  icon="mdi-pencil-outline"
                  size="small"
                  variant="text"
                  color="success"
                  @click="startEdit(item)"
                />
              </CTableDataCell>

              <CTableDataCell>
                <v-btn
                  density="compact"
                  icon="mdi-trash-can-outline"
                  size="small"
                  variant="text"
                  color="error"
                  @click="openDeleteModal(item)"
                />
              </CTableDataCell>
            </CTableRow>
          </CTableBody>
        </CTable>

        <NoData v-else-if="!loading" />

        <CRow v-if="totalPages > 1" class="mt-3">
          <CCol>
            <Pagination
              :active-page="page"
              :limit="8"
              :pages="totalPages"
              @active-page-change="onPageSelect"
            />
          </CCol>
        </CRow>
      </CCardBody>
    </CCard>

    <ConfirmModal ref="refConfirmModal" @confirm-func="confirmDelete" />
  </div>
</template>
