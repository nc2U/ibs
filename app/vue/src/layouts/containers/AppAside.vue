<script lang="ts" setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from '@/store'
import { useAccount } from '@/store/pinia/account'
import { useApproval } from '@/store/pinia/approval'
import { useIssue } from '@/store/pinia/work_issue'
import { useCompany } from '@/store/pinia/company'
import { useProject } from '@/store/pinia/project'
import type { Company } from '@/store/types/settings'
import type { Todo as TodoType } from '@/store/types/accounts'

const router = useRouter()
const store = useStore()
const accountStore = useAccount()
const approvalStore = useApproval()
const issueStore = useIssue()
const comStore = useCompany()
const projStore = useProject()

const activeKey = ref(1)

const company = computed<Company | null>(() => comStore.company)
const currentProject = computed(() => projStore.project)
const userInfo = computed(() => accountStore.userInfo)
const isStaff = computed(() => accountStore.isStaff)
const asideVisible = computed(() => store.asideVisible)

const isDark = computed(() => store.theme === 'dark')
const white = computed(() => (isDark.value ? 'dark-theme' : 'bg-white'))
const light = computed(() => (isDark.value ? 'dark-theme' : 'bg-more-light'))

const active = (key: number) => key === activeKey.value
const updateActiveKey = (key: number) => (activeKey.value = key)

// 탭 1: 오늘 & 할 일 데이터
const pendingApprovals = computed(() => approvalStore.pendingList)
const myChargedIssues = computed(() => issueStore.issueNumByMember.open_charged || 0)
const myTodos = computed(() => accountStore.myTodos)
const newTodoTitle = ref('')

const handleAddTodo = async () => {
  const title = newTodoTitle.value.trim()
  if (!title || !userInfo.value?.pk) return
  await accountStore.createTodo({ user: userInfo.value.pk, title })
  newTodoTitle.value = ''
}

const toggleTodo = (todo: TodoType) => {
  accountStore.patchTodo({ pk: todo.pk, completed: !todo.completed })
}

const removeTodo = (pk?: number) => {
  if (pk) {
    accountStore.patchTodo({ pk, soft_deleted: true })
  }
}

// 탭 2: 최근 내 기안 문서
const myDraftedDocs = computed(() => approvalStore.draftedList)

// 브라우저 탭 타이틀 동기화
watch(
  company,
  newCom => {
    const comName = newCom?.name ? `${newCom.name} :: ` : ''
    document.title = `${comName}IBS`
  },
  { immediate: true },
)

const navigateAndClose = (path: string) => {
  store.toggleAside()
  router.push(path)
}

const openExternal = (url: string) => {
  window.open(url, '_blank')
}
</script>

<template>
  <CSidebar
    color-scheme="light"
    self-hiding="xxl"
    size="lg"
    overlaid
    position="end"
    :visible="asideVisible"
    :class="white"
  >
    <CSidebarHeader class="bg-transparent p-0 aside-header">
      <CNav class="w-100 aside-nav-tabs">
        <CNavItem :class="{ active: active(1) }" class="aside-nav-item aside-first-tab">
          <CNavLink class="cursor-pointer aside-nav-link" @click="updateActiveKey(1)">
            <v-icon icon="mdi-calendar-check" size="small" class="me-1" />
            <small class="fw-bold">오늘/할일</small>
            <v-badge
              v-if="pendingApprovals.length > 0"
              :content="pendingApprovals.length"
              color="danger"
              inline
              class="ms-1"
            />
          </CNavLink>
        </CNavItem>
        <CNavItem :class="{ active: active(2) }" class="aside-nav-item">
          <CNavLink class="cursor-pointer aside-nav-link" @click="updateActiveKey(2)">
            <v-icon icon="mdi-file-document-outline" size="small" class="me-1" />
            <small class="fw-bold">내 기안</small>
            <v-badge
              v-if="myDraftedDocs.length > 0"
              :content="myDraftedDocs.length"
              color="info"
              inline
              class="ms-1"
            />
          </CNavLink>
        </CNavItem>
        <CNavItem :class="{ active: active(3) }" class="aside-nav-item">
          <CNavLink class="cursor-pointer aside-nav-link" @click="updateActiveKey(3)">
            <v-icon icon="mdi-cog-outline" size="small" class="me-1" />
            <small class="fw-bold">빠른도구</small>
          </CNavLink>
        </CNavItem>
        <CNavItem class="ms-auto me-2 py-2 d-flex align-items-center aside-close-item">
          <CCloseButton @click="store.toggleAside" />
        </CNavItem>
      </CNav>
    </CSidebarHeader>

    <CTabContent>
      <!-- ── 탭 1: 오늘 & 할 일 (Today & Tasks) ── -->
      <CTabPane :visible="activeKey === 1" class="p-3">
        <!-- 1. 결재 대기 요약 (스태프 전용) -->
        <div v-if="isStaff" class="mb-4">
          <div class="d-flex justify-content-between align-items-center mb-2">
            <span class="fw-bold small text-muted">
              <v-icon icon="mdi-file-check-outline" size="x-small" color="warning" class="me-1" />
              결재 대기 문서 ({{ pendingApprovals.length }}건)
            </span>
            <v-btn
              variant="text"
              size="x-small"
              color="primary"
              @click="navigateAndClose('/approval/pending')"
            >
              전체보기 &gt;
            </v-btn>
          </div>

          <div
            v-if="pendingApprovals.length === 0"
            class="text-center py-2 text-muted small bg-more-light rounded"
          >
            대기 중인 결재 문서가 없습니다.
          </div>
          <CListGroup v-else flush class="border rounded">
            <CListGroupItem
              v-for="doc in pendingApprovals.slice(0, 3)"
              :key="doc.id"
              class="cursor-pointer p-2 hover-bg"
              @click="navigateAndClose(`/approval/document/${doc.id}`)"
            >
              <div class="d-flex justify-content-between align-items-center">
                <span class="text-truncate fw-medium small" style="max-width: 200px">
                  {{ doc.title }}
                </span>
                <v-chip size="x-small" color="warning" variant="flat">대기</v-chip>
              </div>
              <small class="text-muted d-block mt-1">
                기안자: {{ doc.drafter?.full_name || doc.drafter?.username }} |
                {{ doc.doc_type_name }}
              </small>
            </CListGroupItem>
          </CListGroup>
        </div>

        <!-- 2. 담당 업무 링크 -->
        <div class="mb-4">
          <div class="d-flex justify-content-between align-items-center mb-2">
            <span class="fw-bold small text-muted">
              <v-icon icon="mdi-alert-circle-outline" size="x-small" color="info" class="me-1" />
              내 담당 업무 ({{ myChargedIssues }}건)
            </span>
            <v-btn
              variant="text"
              size="x-small"
              color="primary"
              @click="navigateAndClose('/work/issue')"
            >
              업무함 &gt;
            </v-btn>
          </div>
        </div>

        <v-divider />

        <!-- 3. 개인 To-Do 할 일 체크리스트 -->
        <div>
          <div class="d-flex justify-content-between align-items-center mb-2">
            <span class="fw-bold small text-muted">
              <v-icon
                icon="mdi-checkbox-marked-circle-outline"
                size="x-small"
                color="success"
                class="me-1"
              />
              나의 할 일 (To-Do)
            </span>
            <span class="small text-muted"
              >{{ myTodos.filter(t => !t.completed).length }}개 남음</span
            >
          </div>

          <!-- 새 할 일 입력 폼 -->
          <div class="d-flex gap-1 mb-2">
            <CFormInput
              v-model="newTodoTitle"
              size="sm"
              placeholder="새로운 할 일 입력 후 추가..."
              @keyup.enter="handleAddTodo"
            />
            <v-btn size="x-small" color="primary" class="mt-1" @click="handleAddTodo"> 추가 </v-btn>
          </div>

          <!-- 할 일 목록 -->
          <div
            v-if="myTodos.length === 0"
            class="text-center py-3 text-muted small bg-more-light rounded"
          >
            등록된 할 일이 없습니다.
          </div>
          <CListGroup
            v-else
            flush
            class="border rounded"
            style="max-height: 280px; overflow-y: auto"
          >
            <CListGroupItem
              v-for="todo in myTodos"
              :key="todo.pk"
              class="d-flex align-items-center justify-content-between p-2"
            >
              <div
                class="d-flex align-items-center text-truncate cursor-pointer"
                @click="toggleTodo(todo)"
              >
                <v-icon
                  :icon="todo.completed ? 'mdi-checkbox-marked' : 'mdi-checkbox-blank-outline'"
                  size="small"
                  :color="todo.completed ? 'success' : 'grey'"
                  class="me-2"
                />
                <span
                  class="small text-truncate"
                  :class="{ 'text-decoration-line-through text-muted': todo.completed }"
                >
                  {{ todo.title }}
                </span>
              </div>
              <v-btn
                icon="mdi-close"
                size="x-small"
                variant="text"
                color="danger"
                @click.stop="removeTodo(todo.pk)"
              />
            </CListGroupItem>
          </CListGroup>
        </div>
      </CTabPane>

      <!-- ── 탭 2: 내 기안 (My Drafted Documents) ── -->
      <CTabPane :visible="activeKey === 2" class="p-3">
        <div class="d-flex justify-content-between align-items-center mb-2">
          <span class="fw-bold small text-muted">
            <v-icon icon="mdi-file-send-outline" size="x-small" color="primary" class="me-1" />
            내가 기안한 최근 문서
          </span>
          <v-btn
            variant="text"
            size="x-small"
            color="primary"
            @click="navigateAndClose('/approval/drafted')"
          >
            기안함 &gt;
          </v-btn>
        </div>

        <div
          v-if="myDraftedDocs.length === 0"
          class="text-center py-4 text-muted small bg-more-light rounded"
        >
          기안한 문서가 없습니다.
        </div>
        <CListGroup v-else flush class="border rounded">
          <CListGroupItem
            v-for="doc in myDraftedDocs.slice(0, 8)"
            :key="doc.id"
            class="cursor-pointer p-2 hover-bg"
            @click="navigateAndClose(`/approval/document/${doc.id}`)"
          >
            <div class="d-flex justify-content-between align-items-center">
              <span class="text-truncate fw-medium small" style="max-width: 210px">
                {{ doc.title }}
              </span>
              <v-chip
                size="x-small"
                :color="
                  doc.status === 'approved'
                    ? 'success'
                    : doc.status === 'rejected'
                      ? 'danger'
                      : 'warning'
                "
                variant="flat"
              >
                {{
                  doc.status === 'approved' ? '완료' : doc.status === 'rejected' ? '반려' : '진행중'
                }}
              </v-chip>
            </div>
            <small class="text-muted d-block mt-1">
              {{ doc.doc_type_name }} | {{ doc.created_at?.substring(0, 10) }}
            </small>
          </CListGroupItem>
        </CListGroup>
      </CTabPane>

      <!-- ── 탭 3: 빠른 도구 & 바로가기 (Quick Tools) ── -->
      <CTabPane :visible="activeKey === 3" class="p-3">
        <h6 class="fw-bold small text-muted mb-3">
          <v-icon icon="mdi-information-outline" size="x-small" class="me-1" />
          현재 접속 정보
        </h6>
        <div class="p-2 mb-3 bg-more-light rounded small border">
          <div class="d-flex justify-content-between mb-1">
            <span class="text-muted">소속 회사:</span>
            <strong>{{ company?.name || '회사 미선택' }}</strong>
          </div>
          <div class="d-flex justify-content-between mb-1">
            <span class="text-muted">현재 프로젝트:</span>
            <strong>{{ currentProject?.name || '프로젝트 미선택' }}</strong>
          </div>
          <div class="d-flex justify-content-between">
            <span class="text-muted">사용자:</span>
            <strong>{{ userInfo?.username }}</strong>
          </div>
        </div>

        <v-divider />

        <h6 class="fw-bold small text-muted mb-2">
          <v-icon icon="mdi-link-variant" size="x-small" class="me-1" />
          시스템 바로가기
        </h6>
        <CListGroup flush class="border rounded mb-3">
          <CListGroupItem
            v-if="userInfo?.is_staff"
            class="cursor-pointer p-2 hover-bg d-flex align-items-center justify-content-between"
            @click="openExternal('/admin/')"
          >
            <span class="small">
              <v-icon icon="mdi-cog-outline" size="small" class="me-2 text-primary" />
              Django 관리자 페이지
            </span>
            <v-icon icon="mdi-open-in-new" size="x-small" color="grey" />
          </CListGroupItem>

          <CListGroupItem
            class="cursor-pointer p-2 hover-bg d-flex align-items-center justify-content-between"
            @click="openExternal('https://docs.dyibs.com/')"
          >
            <span class="small">
              <v-icon
                icon="mdi-book-open-page-variant-outline"
                size="small"
                class="me-2 text-info"
              />
              사용자 매뉴얼 (VitePress)
            </span>
            <v-icon icon="mdi-open-in-new" size="x-small" color="grey" />
          </CListGroupItem>

          <CListGroupItem
            class="cursor-pointer p-2 hover-bg d-flex align-items-center justify-content-between"
            @click="navigateAndClose('/accounts/profile')"
          >
            <span class="small">
              <v-icon icon="mdi-account-circle-outline" size="small" class="me-2 text-success" />
              내 계정 / 프로필 설정
            </span>
            <v-icon icon="mdi-chevron-right" size="x-small" color="grey" />
          </CListGroupItem>
        </CListGroup>

        <v-divider />

        <h6 class="fw-bold small text-muted mb-2">
          <v-icon icon="mdi-palette-outline" size="x-small" class="me-1" />
          테마 설정
        </h6>
        <div class="d-flex align-items-center justify-content-between p-2 bg-more-light rounded border">
          <span class="small">화면 테마</span>
          <div class="d-flex gap-1">
            <v-btn
              size="x-small"
              :variant="store.theme === 'default' ? 'flat' : 'outlined'"
              color="primary"
              @click="store.toggleTheme('default')"
            >
              라이트
            </v-btn>
            <v-btn
              size="x-small"
              :variant="store.theme === 'dark' ? 'flat' : 'outlined'"
              color="primary"
              @click="store.toggleTheme('dark')"
            >
              다크
            </v-btn>
            <v-btn
              size="x-small"
              :variant="store.theme === 'auto' ? 'flat' : 'outlined'"
              color="primary"
              @click="store.toggleTheme('auto')"
            >
              기기설정
            </v-btn>
          </div>
        </div>
      </CTabPane>
    </CTabContent>
  </CSidebar>
</template>

<style lang="scss" scoped>
//.aside-header {
//  border-bottom: 1px solid var(--cui-border-color, #e9ecef);
//}

.aside-nav-tabs {
  position: relative;
  top: -1px; // 탭 라인을 정확히 1px 위로 배치하여 기존 헤더 보더와 일치시킴
  margin-bottom: -1px;
}

.aside-nav-item {
  position: relative;
  border-bottom: 1px solid var(--cui-border-color, #e9ecef);
  transition: all 0.2s ease-in-out;

  &.active {
    border-bottom: 2px solid #0d6efd; // 활성 탭: 메인 컬러로 2px 강조

    .aside-nav-link {
      color: #0d6efd;
    }
  }

  &:hover:not(.active) {
    border-bottom: 2px solid var(--cui-border-color, #dee2e6);
  }
}

// 첫 번째 탭 (오늘/할일) 시작 부분(좌측)에 옅은 회색 세로 경계선 추가 (기존 헤더와 사이드바 간의 시각적 경계 구분)
.aside-first-tab {
  border-left: 1px solid var(--cui-border-color, #f2f2f2);
}

.aside-nav-link {
  padding: 0.85rem 0.95rem;
  color: var(--cui-body-color, #4f5d73);
  text-decoration: none;
  display: flex;
  align-items: center;

  &:hover {
    color: var(--cui-body-color, #2c384a);
  }
}

.aside-close-item {
  border-bottom: 2px solid transparent;
}

.hover-bg:hover {
  background-color: rgba(0, 0, 0, 0.03);
}

.cursor-pointer {
  cursor: pointer;
}
</style>
