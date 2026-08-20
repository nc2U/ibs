<script lang="ts" setup>
import { computed, onMounted, ref, watch } from 'vue'
import { pageTitle, navMenu } from '@/views/hrManage/_menu/headermixin1'
import { useCompany } from '@/store/pinia/company'
import type { Department, Staff } from '@/store/types/company'
import ComHrAuthGuard from '@/components/AuthGuard/ComHrAuthGuard.vue'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import OrgTreeNode, { type OrgNode } from './components/OrgTreeNode.vue'
import DeptMembersModal from './components/DeptMembersModal.vue'

const comStore = useCompany()
const loading = ref(true)
const viewMode = ref<'tree' | 'grid'>('tree')
const searchTerm = ref('')
const zoomLevel = ref(1.0)
const collapsedNodes = ref<Set<number>>(new Set())

const selectedDeptNode = ref<OrgNode | null>(null)
const isModalVisible = ref(false)

// 선택된 회사 ID
const currentCompanyId = computed(() => comStore.initComId || 1)

// 데이터 로드
const loadOrgData = async (comId: number) => {
  loading.value = true
  try {
    await Promise.all([comStore.fetchAllDepartList(comId), comStore.fetchAllStaffList(comId)])
  } finally {
    loading.value = false
  }
}

const comSelect = async (target: number | null) => {
  if (target) {
    await loadOrgData(target)
  }
}

const getDeptMembers = (dept: Department): Staff[] => {
  const staffs: Staff[] = comStore.allStaffList || []
  return staffs.filter(s => {
    const matchDirect = s.department === dept.name
    const matchAssignment = s.assignments?.some(
      a => a.department === dept.pk || a.department_name === dept.name,
    )
    return matchDirect || matchAssignment
  })
}

// 트리 구조 생성
const orgTree = computed<OrgNode[]>(() => {
  const depts: Department[] = comStore.allDepartList || []
  const staffs: Staff[] = comStore.allStaffList || []

  // 1. 부서별 노드 맵 생성
  const nodeMap = new Map<number, OrgNode>()

  depts.forEach(d => {
    if (!d.pk) return
    // 해당 부서 소속 직원들 필터링
    const deptMembers = staffs.filter(s => {
      const matchDirect = s.department === d.name
      const matchAssignment = s.assignments?.some(
        a => a.department === d.pk || a.department_name === d.name,
      )
      return matchDirect || matchAssignment
    })

    // 부서장/책임자 찾기 (manager 지정 우선, 없으면 직책에 '대표'/'본부장'/'팀장' 등)
    let leader: Staff | null = null
    if (d.manager) {
      leader = staffs.find(s => s.pk === d.manager) || null
    }
    if (!leader) {
      leader =
        deptMembers.find(
          m =>
            m.duty?.includes('대표') ||
            m.duty?.includes('총괄') ||
            m.duty?.includes('본부장') ||
            m.duty?.includes('팀장'),
        ) || null
    }

    nodeMap.set(d.pk, {
      id: d.pk,
      name: d.name,
      level: d.level || 1,
      task: d.task,
      manager_name: d.manager_name || (leader ? leader.name : null),
      leader,
      members: deptMembers,
      children: [],
    })
  })

  // 2. 계층 관계(upper_depart) 연결
  const roots: OrgNode[] = []

  depts.forEach(d => {
    if (!d.pk) return
    const node = nodeMap.get(d.pk)
    if (!node) return

    if (d.upper_depart && nodeMap.has(d.upper_depart)) {
      const parent = nodeMap.get(d.upper_depart)
      parent?.children.push(node)
    } else {
      roots.push(node)
    }
  })

  // 3. 레벨 및 순서 정렬
  roots.sort((a, b) => a.level - b.level)
  return roots
})

// 총 부서 수 & 총 재직자 수
const totalDeptsCount = computed(() => comStore.allDepartList.length)
const totalStaffsCount = computed(() => comStore.allStaffList.length)

// 줌 컨트롤
const zoomIn = () => {
  if (zoomLevel.value < 1.5) zoomLevel.value = parseFloat((zoomLevel.value + 0.1).toFixed(1))
}
const zoomOut = () => {
  if (zoomLevel.value > 0.6) zoomLevel.value = parseFloat((zoomLevel.value - 0.1).toFixed(1))
}
const resetZoom = () => {
  zoomLevel.value = 1.0
}

// 전체 펼치기 / 접기
const expandAll = () => {
  collapsedNodes.value.clear()
}

const collapseAll = () => {
  const set = new Set<number>()
  const collect = (nodes: OrgNode[]) => {
    nodes.forEach(n => {
      if (n.children.length) {
        set.add(n.id)
        collect(n.children)
      }
    })
  }
  collect(orgTree.value)
  collapsedNodes.value = set
}

const toggleCollapse = (nodeId: number) => {
  if (collapsedNodes.value.has(nodeId)) {
    collapsedNodes.value.delete(nodeId)
  } else {
    collapsedNodes.value.add(nodeId)
  }
}

const onSelectDept = (node: OrgNode) => {
  selectedDeptNode.value = node
  isModalVisible.value = true
}

// 검색어 입력 시 자동 펼치기
watch(
  () => searchTerm.value,
  q => {
    if (q.trim()) {
      expandAll()
    }
  },
)

onMounted(async () => {
  await loadOrgData(currentCompanyId.value)
})
</script>

<template>
  <ComHrAuthGuard>
    <Loading v-model:active="loading" />
    <ContentHeader
      :page-title="pageTitle"
      :nav-menu="navMenu"
      selector="CompanySelect"
      @com-select="comSelect"
    />

    <ContentBody>
      <CCardBody class="p-4">
        <!-- 상단 컨트롤 툴바 -->
        <div
          class="d-flex flex-wrap align-items-center justify-content-between gap-3 mb-4 pb-3 border-bottom"
        >
          <!-- 좌측: 제목 & 통계 뱃지 -->
          <div class="d-flex align-items-center gap-3">
            <h5 class="mb-0 fw-bold d-flex align-items-center">
              <v-icon icon="mdi-sitemap" size="22" class="me-3 text-primary" />
              조직도
            </h5>
            <div class="d-flex gap-2">
              <span
                class="badge bg-primary-subtle text-primary border border-primary-subtle px-2 py-1"
              >
                부서 <strong>{{ totalDeptsCount }}</strong>
                개
              </span>
              <span
                class="badge bg-success-subtle text-success border border-success-subtle px-2 py-1"
              >
                임직원 <strong>{{ totalStaffsCount }}</strong
                >명
              </span>
            </div>
          </div>

          <!-- 우측: 검색 + 줌/모드 컨트롤 -->
          <div class="d-flex flex-wrap align-items-center gap-2">
            <!-- 검색창 -->
            <div style="width: 220px">
              <CInputGroup size="sm">
                <CFormInput v-model="searchTerm" placeholder="부서명/직원명 검색..." />
                <CButton v-if="searchTerm" color="light" variant="outline" @click="searchTerm = ''">
                  <v-icon icon="mdi-close" size="x-small" />
                </CButton>
              </CInputGroup>
            </div>

            <!-- 뷰 모드 토글 (트리 / 그리드) -->
            <div class="btn-group btn-group-sm">
              <button
                class="btn"
                :class="viewMode === 'tree' ? 'btn-primary' : 'btn-outline-secondary'"
                @click="viewMode = 'tree'"
              >
                <v-icon icon="mdi-file-tree" size="small" class="me-1" />트리 뷰
              </button>
              <button
                class="btn"
                :class="viewMode === 'grid' ? 'btn-primary' : 'btn-outline-secondary'"
                @click="viewMode = 'grid'"
              >
                <v-icon icon="mdi-view-grid-outline" size="small" class="me-1" />부서별 뷰
              </button>
            </div>

            <!-- 트리 뷰 전용: 줌 & 펼치기 컨트롤 -->
            <template v-if="viewMode === 'tree'">
              <div class="btn-group btn-group-sm">
                <button class="btn btn-outline-secondary" title="전체 펼치기" @click="expandAll">
                  <v-icon icon="mdi-arrow-expand-all" size="small" />
                </button>
                <button class="btn btn-outline-secondary" title="전체 접기" @click="collapseAll">
                  <v-icon icon="mdi-arrow-collapse-all" size="small" />
                </button>
              </div>

              <div class="btn-group btn-group-sm">
                <button
                  class="btn btn-outline-secondary"
                  :disabled="zoomLevel <= 0.6"
                  title="축소"
                  @click="zoomOut"
                >
                  <v-icon icon="mdi-magnify-minus-outline" size="small" />
                </button>
                <button class="btn btn-outline-secondary px-2" title="기본 크기" @click="resetZoom">
                  {{ Math.round(zoomLevel * 100) }}%
                </button>
                <button
                  class="btn btn-outline-secondary"
                  :disabled="zoomLevel >= 1.5"
                  title="확대"
                  @click="zoomIn"
                >
                  <v-icon icon="mdi-magnify-plus-outline" size="small" />
                </button>
              </div>
            </template>
          </div>
        </div>

        <!-- 1. 계층형 조직도 트리 뷰 -->
        <div v-if="viewMode === 'tree'" class="org-chart-viewport">
          <div v-if="!orgTree.length" class="text-center text-muted py-5">
            <v-icon icon="mdi-sitemap-outline" size="x-large" class="mb-2" />
            <div>등록된 부서 및 조직 정보가 없습니다.</div>
          </div>

          <div
            v-else
            class="org-tree-canvas"
            :style="{ transform: `scale(${zoomLevel})`, transformOrigin: 'top center' }"
          >
            <div class="org-roots-wrapper p-2">
              <OrgTreeNode
                v-for="root in orgTree"
                :key="root.id"
                :node="root"
                :search-term="searchTerm"
                :collapsed-nodes="collapsedNodes"
                @toggle-collapse="toggleCollapse"
                @select-dept="onSelectDept"
              />
            </div>
          </div>
        </div>

        <!-- 2. 부서별 카드 그리드 뷰 -->
        <div v-else class="row g-3 pb-5">
          <div v-if="!comStore.allDepartList.length" class="col-12 text-center text-muted py-5">
            등록된 부서가 없습니다.
          </div>
          <div v-for="dept in comStore.allDepartList" :key="dept.pk" class="col-md-6 col-lg-4">
            <div
              class="card h-100 shadow-sm border cursor-pointer hover-card"
              @click="
                onSelectDept({
                  id: dept.pk || 0,
                  name: dept.name,
                  level: dept.level || 1,
                  task: dept.task,
                  manager_name: dept.manager_name,
                  members: getDeptMembers(dept),
                  children: [],
                })
              "
            >
              <div
                class="card-header bg-more-light d-flex align-items-center justify-content-between py-2"
              >
                <span class="fw-bold">{{ dept.name }}</span>
                <span class="badge bg-secondary">Lv.{{ dept.level || 1 }}</span>
              </div>
              <div class="card-body p-3">
                <div class="d-flex align-items-center justify-content-between mb-2">
                  <span class="small text-muted">
                    <v-icon icon="mdi-account-tie" size="x-small" class="me-1 text-primary" />
                    책임자: <strong>{{ dept.manager_name || '미지정' }}</strong>
                  </span>
                  <span class="badge bg-light text-dark border">
                    {{ getDeptMembers(dept).length }}명
                  </span>
                </div>
                <div
                  v-if="dept.task"
                  class="small text-muted text-truncate mb-2"
                  :title="dept.task"
                >
                  {{ dept.task }}
                </div>
                <div class="border-top pt-2 mt-2 d-flex justify-content-between align-items-center">
                  <span class="small text-primary fw-medium">부서원 목록 보기</span>
                  <v-icon icon="mdi-chevron-right" size="small" class="text-muted" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </CCardBody>
    </ContentBody>

    <!-- 부서원 명단 모달 -->
    <DeptMembersModal v-model:visible="isModalVisible" :node="selectedDeptNode" />
  </ComHrAuthGuard>
</template>

<style scoped>
.org-chart-viewport {
  width: 100%;
  min-height: 520px;
  overflow: auto;
  padding: 2rem 1rem;
  background-color: #f8fafc;
  border-radius: 0.5rem;
  border: 1px dashed #cbd5e1;
  display: flex;
  justify-content: center;
}
.dark-theme .org-chart-viewport {
  background-color: #282933;
  border-color: #374151;
}

.org-tree-canvas {
  transition: transform 0.2s ease-in-out;
  display: inline-block;
  padding: 1rem;
}

.org-roots-wrapper {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  gap: 2rem;
}

.hover-card {
  transition: all 0.2s ease-in-out;
}

.hover-card:hover {
  transform: translateY(-3px);
  border-color: #0d6efd !important;
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.08) !important;
}

.cursor-pointer {
  cursor: pointer;
}
</style>
