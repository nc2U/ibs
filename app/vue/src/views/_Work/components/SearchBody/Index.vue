<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { navMenu2 as navMenu } from '@/views/_Work/_menu/headermixin1'
import { colorLight } from '@/utils/cssMixins'
import { useCompany } from '@/store/pinia/company.ts'
import { useSearch } from '@/store/pinia/work_search.ts'
import type { Company } from '@/store/types/settings'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'
import Header from '@/views/_Work/components/Header/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'

const cBody = ref()
const comStore = useCompany()
const company = computed<Company | null>(() => comStore.company)
const comName = computed(() => company?.value?.name)
const sideNavCAll = () => cBody.value.toggle()

const searchStore = useSearch()
const searchWord = ref('')
const projectScope = ref<'all' | 'my'>('all')
const titleOnly = ref(false)
const targets = ref({
  meetings: true,
  issues: true,
  comments: true,
  news: true,
  documents: true,
  posts: true,
})
const openedOnly = ref(false)
const visible = ref(false)

const [route, router] = [useRoute(), useRouter()]

const activeTargets = computed(() =>
  Object.entries(targets.value)
    .filter(([, v]) => v)
    .map(([k]) => k),
)

const goSearch = () => {
  if (searchWord.value.trim().length < 2) return
  router.replace({
    name: '전체검색',
    query: {
      q: searchWord.value,
      scope: projectScope.value,
      title_only: titleOnly.value ? '1' : '0',
      opened_only: openedOnly.value ? '1' : '0',
      t: activeTargets.value,
    },
  })
}

const doSearch = (q: string) => {
  searchStore.fetchSearch({
    q,
    scope: projectScope.value,
    t: activeTargets.value,
    title_only: titleOnly.value ? '1' : '0',
    opened_only: openedOnly.value ? '1' : '0',
  })
}

watch(
  () => route.query,
  query => {
    const q = query.q
    if (q && typeof q === 'string') {
      searchWord.value = q
      if (query.scope === 'my') {
        projectScope.value = 'my'
      } else {
        projectScope.value = 'all'
      }
      if (query.title_only) {
        titleOnly.value = query.title_only === '1'
      }
      if (query.opened_only) {
        openedOnly.value = query.opened_only === '1'
      }
      if (query.t) {
        const queryTargets = Array.isArray(query.t) ? query.t : [query.t]
        Object.keys(targets.value).forEach(k => {
          targets.value[k as keyof typeof targets.value] = queryTargets.includes(k)
        })
      } else {
        Object.keys(targets.value).forEach(k => {
          targets.value[k as keyof typeof targets.value] = true
        })
      }
      doSearch(q)
    }
  },
  { deep: true, immediate: true },
)

onBeforeRouteLeave((to, from, next) => {
  searchStore.reset()
  to.query = {}
  next()
})

// 결과 타입 라벨
const typeLabel: Record<string, string> = {
  meetings: '회의록',
  issues: '업무',
  comments: '댓글',
  news: '공지',
  documents: '문서',
  posts: '게시판',
}

const statusColor = (closed: boolean) => (closed ? 'grey' : 'primary')

const meetingStatusLabel: Record<string, string> = { '1': '준비', '2': '종료', '3': '취소' }
</script>

<template>
  <Header :page-title="comName" :nav-menu="navMenu" @side-nav-call="sideNavCAll" />

  <ContentBody ref="cBody" :nav-menu="navMenu" :query="route?.query" :aside="false">
    <template v-slot:default>
      <CRow class="py-2">
        <CCol>
          <h5>
            <v-icon icon="mdi-magnify" size="small" class="mr-1" />
            검색
          </h5>
        </CCol>
      </CRow>

      <!-- 검색 폼 -->
      <CCard :color="colorLight">
        <CCardBody>
          <CRow>
            <CCol sm="12" md="8" lg="6" xl="5">
              <CRow>
                <CCol sm="8" xl="9" class="mb-1">
                  <CInputGroup>
                    <CFormInput
                      v-model="searchWord"
                      placeholder="검색어 입력 (2자 이상)"
                      @keydown.enter="goSearch"
                    />
                    <span
                      color="primary"
                      variant="flat"
                      rounded="0"
                      size="small"
                      class="input-group-text"
                      :loading="searchStore.loading"
                      @click="goSearch"
                    >
                      <v-icon icon="mdi-magnify" size="18" class="mr-1" />
                    </span>
                  </CInputGroup>
                </CCol>
                <CCol sm="4" xl="3" class="mb-1">
                  <CFormSelect v-model="projectScope">
                    <option value="all">모든 프로젝트</option>
                    <option value="my">내 프로젝트</option>
                  </CFormSelect>
                </CCol>
              </CRow>
            </CCol>

            <CCol class="pt-2">
              <CFormCheck v-model="titleOnly" inline label="제목에서만 찾기" id="title-only" />
            </CCol>
          </CRow>

          <!-- 검색 대상 선택 -->
          <CRow class="mt-3 m-1">
            <CCard class="mt-3" :color="colorLight">
              <CCardBody>
                <CFormCheck v-model="targets.meetings" inline label="회의록" id="target-meetings" />
                <CFormCheck v-model="targets.issues" inline label="업무" id="target-issues" />
                <CFormCheck v-model="targets.comments" inline label="댓글" id="target-comments" />
                <CFormCheck v-model="targets.news" inline label="공지" id="target-news" />
                <CFormCheck v-model="targets.documents" inline label="문서" id="target-documents" />
                <CFormCheck v-model="targets.posts" inline label="게시판" id="target-posts" />
              </CCardBody>
            </CCard>
          </CRow>

          <!-- 옵션 -->
          <CRow class="mt-3">
            <CCol class="pointer mb-0" @click="visible = !visible">
              <v-icon :icon="visible ? 'mdi-chevron-down' : 'mdi-chevron-right'" size="sm" />
              옵션
            </CCol>
            <CCollapse :visible="visible">
              <v-divider class="mx-1" />
              <CRow class="mt-2 pl-1">
                <CCol>
                  <CFormCheck v-model="openedOnly" label="열린 업무만" id="opened-only" />
                </CCol>
              </CRow>
            </CCollapse>
          </CRow>
        </CCardBody>
      </CCard>

      <CRow class="mt-2">
        <CCol>
          <v-btn
            color="primary"
            variant="outlined"
            size="small"
            :loading="searchStore.loading"
            @click="goSearch"
          >
            검색
          </v-btn>
        </CCol>
      </CRow>

      <!-- 에러 -->
      <CRow v-if="searchStore.error" class="mt-3">
        <CCol>
          <v-alert type="warning" variant="tonal">
            {{ searchStore.error }}
          </v-alert>
        </CCol>
      </CRow>

      <!-- 검색 결과 -->
      <div v-if="route.query.q && !searchStore.loading">
        <CRow class="mt-4">
          <CCol>
            <h5>
              결과
              <v-chip size="small" color="primary" class="ml-1">
                {{ searchStore.totalCount }}
              </v-chip>
            </h5>
          </CCol>
        </CRow>

        <!-- 결과 없음 -->
        <CRow v-if="!searchStore.hasResults" class="mt-2">
          <CCol>
            <v-alert variant="tonal" color="blue-grey">
              <v-icon icon="mdi-magnify-close" size="22" class="mr-1" />
              검색 결과가 없습니다.
            </v-alert>
          </CCol>
        </CRow>

        <!-- 회의록 결과 -->
        <template v-if="searchStore.results?.meetings?.length">
          <CRow class="mt-4">
            <CCol>
              <h6 class="text-medium-emphasis">
                <v-icon icon="mdi-account-group-outline" size="small" class="mr-1" />
                {{ typeLabel.meetings }}
                <v-chip size="x-small" class="ml-1">
                  {{ searchStore.results.meetings.length }}
                </v-chip>
              </h6>
              <v-divider />
            </CCol>
          </CRow>
          <CRow
            v-for="item in searchStore.results.meetings"
            :key="`meeting-${item.pk}`"
            class="mt-2"
          >
            <CCol>
              <div class="d-flex align-center gap-2 flex-wrap">
                <v-chip size="x-small" color="teal" label>
                  {{ meetingStatusLabel[item.status] ?? item.status }}
                </v-chip>
                <router-link
                  :to="{
                    name: '(회의) - 보기',
                    params: { projId: item.project.slug, meetingId: item.pk },
                  }"
                  class="text-body-2"
                >
                  {{ item.title }}
                </router-link>
                <span class="text-caption text-medium-emphasis">
                  {{ item.project.name }} · {{ item.creator.username }} ·
                  {{
                    item.meeting_date
                      ? new Date(item.meeting_date).toLocaleDateString('ko-KR')
                      : '-'
                  }}
                </span>
              </div>
            </CCol>
          </CRow>
        </template>

        <!-- 업무 결과 -->
        <template v-if="searchStore.results?.issues?.length">
          <CRow class="mt-4">
            <CCol>
              <h6 class="text-medium-emphasis">
                <v-icon icon="mdi-clipboard-check-outline" size="small" class="mr-1" />
                {{ typeLabel.issues }}
                <v-chip size="x-small" class="ml-1">{{ searchStore.results.issues.length }}</v-chip>
              </h6>
              <v-divider />
            </CCol>
          </CRow>
          <CRow v-for="item in searchStore.results.issues" :key="`issue-${item.pk}`" class="mt-2">
            <CCol>
              <div class="d-flex align-center gap-2 flex-wrap">
                <v-chip size="x-small" :color="statusColor(item.status.closed)" label>
                  {{ item.status.name }}
                </v-chip>
                <v-chip size="x-small" color="blue-grey" label>{{ item.tracker.name }}</v-chip>
                <router-link
                  :to="{
                    name: '(업무) - 보기',
                    params: { projId: item.project.slug, issueId: item.pk },
                  }"
                  class="text-body-2"
                >
                  <v-icon
                    v-if="item.is_private"
                    icon="mdi-lock-outline"
                    size="x-small"
                    class="mr-1 text-warning"
                  />
                  {{ item.subject }}
                </router-link>
                <span class="text-caption text-medium-emphasis">
                  {{ item.project.name }} · {{ item.creator?.username }} ·
                  {{ new Date(item.created).toLocaleDateString('ko-KR') }}
                </span>
              </div>
            </CCol>
          </CRow>
        </template>

        <!-- 댓글 결과 -->
        <template v-if="searchStore.results?.comments?.length">
          <CRow class="mt-4">
            <CCol>
              <h6 class="text-medium-emphasis">
                <v-icon icon="mdi-comment-search-outline" size="small" class="mr-1" />
                {{ typeLabel.comments }}
                <v-chip size="x-small" class="ml-1">
                  {{ searchStore.results.comments.length }}
                </v-chip>
              </h6>
              <v-divider />
            </CCol>
          </CRow>
          <CRow
            v-for="item in searchStore.results.comments"
            :key="`comment-${item.pk}`"
            class="mt-2"
          >
            <CCol>
              <div class="d-flex align-center gap-2 flex-wrap">
                <router-link
                  :to="{
                    name: '(업무) - 보기',
                    params: { projId: item.issue.project.slug, issueId: item.issue.pk },
                  }"
                  class="text-body-2"
                >
                  {{ item.issue.subject }}
                </router-link>
                <span class="text-caption text-medium-emphasis">에 달린 댓글:</span>
                <span class="text-body-2">{{ item.content }}</span>
                <span class="text-caption text-medium-emphasis">
                  {{ item.creator.username }} ·
                  {{ new Date(item.created).toLocaleDateString('ko-KR') }}
                </span>
              </div>
            </CCol>
          </CRow>
        </template>

        <!-- 공지 결과 -->
        <template v-if="searchStore.results?.news?.length">
          <CRow class="mt-4">
            <CCol>
              <h6 class="text-medium-emphasis">
                <v-icon icon="mdi-message-badge-outline" size="small" class="mr-1" />
                {{ typeLabel.news }}
                <v-chip size="x-small" class="ml-1">{{ searchStore.results.news.length }}</v-chip>
              </h6>
              <v-divider />
            </CCol>
          </CRow>
          <CRow v-for="item in searchStore.results.news" :key="`news-${item.pk}`" class="mt-2">
            <CCol>
              <div class="d-flex align-center gap-2 flex-wrap">
                <router-link
                  :to="{
                    name: '(공지) - 보기',
                    params: { projId: item.project.slug, newsId: item.pk },
                  }"
                  class="text-body-2"
                >
                  {{ item.title }}
                </router-link>
                <span v-if="item.summary" class="text-caption text-medium-emphasis">
                  — {{ item.summary }}
                </span>
                <span class="text-caption text-medium-emphasis">
                  {{ item.project.name }} · {{ item.author.username }} ·
                  {{ new Date(item.created).toLocaleDateString('ko-KR') }}
                </span>
              </div>
            </CCol>
          </CRow>
        </template>

        <!-- 문서 결과 -->
        <template v-if="searchStore.results?.documents?.length">
          <CRow class="mt-4">
            <CCol>
              <h6 class="text-medium-emphasis">
                <v-icon icon="mdi-text-box-search-outline" size="small" class="mr-1" />
                {{ typeLabel.documents }}
                <v-chip size="x-small" class="ml-1">
                  {{ searchStore.results.documents.length }}
                </v-chip>
              </h6>
              <v-divider />
            </CCol>
          </CRow>
          <CRow v-for="item in searchStore.results.documents" :key="`doc-${item.pk}`" class="mt-2">
            <CCol>
              <div class="d-flex align-center gap-2 flex-wrap">
                <router-link
                  :to="{
                    name: '(문서) - 보기',
                    params: { projId: item.project.slug, docId: item.pk },
                  }"
                  class="text-body-2"
                >
                  {{ item.title }}
                </router-link>
                <span v-if="item.description" class="text-caption text-medium-emphasis">
                  — {{ item.description }}
                </span>
                <span class="text-caption text-medium-emphasis">
                  {{ item.project.name }} · {{ item.creator?.username }} ·
                  {{ new Date(item.created).toLocaleDateString('ko-KR') }}
                </span>
              </div>
            </CCol>
          </CRow>
        </template>

        <!-- 게시판 결과 -->
        <template v-if="searchStore.results?.posts?.length">
          <CRow class="mt-4">
            <CCol>
              <h6 class="text-medium-emphasis">
                <v-icon icon="mdi-forum-outline" size="small" class="mr-1" />
                {{ typeLabel.posts }}
                <v-chip size="x-small" class="ml-1">{{ searchStore.results.posts.length }}</v-chip>
              </h6>
              <v-divider />
            </CCol>
          </CRow>
          <CRow v-for="item in searchStore.results.posts" :key="`post-${item.pk}`" class="mt-2">
            <CCol>
              <div class="d-flex align-center gap-2 flex-wrap">
                <router-link
                  :to="{
                    name: '(게시판) - 게시물 보기',
                    params: { projId: item.project.slug, forumId: item.forum, postId: item.pk },
                  }"
                  class="text-body-2"
                >
                  {{ item.title }}
                </router-link>
                <span class="text-caption text-medium-emphasis">
                  {{ item.project.name }} · {{ item.creator?.username }} ·
                  {{ new Date(item.created).toLocaleDateString('ko-KR') }}
                </span>
              </div>
            </CCol>
          </CRow>
        </template>
      </div>
    </template>

    <template v-slot:aside></template>
  </ContentBody>
</template>
