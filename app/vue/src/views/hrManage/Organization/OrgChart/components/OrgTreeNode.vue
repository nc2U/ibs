<script setup lang="ts">
import { computed } from 'vue'
import type { Staff } from '@/store/types/company.ts'

export interface OrgNode {
  id: number
  name: string
  level: number
  task?: string | null
  manager_name?: string | null
  leader?: Staff | null
  members: Staff[]
  children: OrgNode[]
  collapsed?: boolean
}

const props = defineProps<{
  node: OrgNode
  searchTerm?: string
  collapsedNodes: Set<number>
}>()

const emit = defineEmits<{
  (e: 'toggle-collapse', id: number): void
  (e: 'select-dept', node: OrgNode): void
  (e: 'select-staff', staff: Staff): void
}>()

const isCollapsed = computed(() => props.collapsedNodes.has(props.node.id))
const hasChildren = computed(() => props.node.children && props.node.children.length > 0)

// 검색어 일치 여부 판별
const isMatch = computed(() => {
  if (!props.searchTerm) return false
  const q = props.searchTerm.toLowerCase()
  const deptMatch = props.node.name.toLowerCase().includes(q)
  const leaderMatch = (props.node.manager_name ?? '').toLowerCase().includes(q)
  const memberMatch = props.node.members.some(
    m =>
      m.name.toLowerCase().includes(q) ||
      (m.duty ?? '').toLowerCase().includes(q) ||
      (m.position ?? '').toLowerCase().includes(q),
  )
  return deptMatch || leaderMatch || memberMatch
})

// 레벨별 테마 클래스
const levelColorClass = computed(() => {
  switch (props.node.level) {
    case 1:
      return 'level-1'
    case 2:
      return 'level-2'
    case 3:
      return 'level-3'
    default:
      return 'level-default'
  }
})

const levelBadgeClass = computed(() => {
  switch (props.node.level) {
    case 1:
      return 'bg-navy text-white'
    case 2:
      return 'bg-teal text-white'
    case 3:
      return 'bg-slate text-white'
    default:
      return 'bg-secondary text-white'
  }
})
</script>

<template>
  <div class="org-tree-branch">
    <!-- 부서 카드 본체 (직각 디자인 & 넉넉한 내부 여백) -->
    <div
      class="org-node-card"
      :class="[levelColorClass, { 'node-matched': isMatch }]"
      @click="emit('select-dept', node)"
    >
      <!-- 1. 상단 메타 헤더: 레벨 및 인원수 -->
      <div class="node-header d-flex align-items-center justify-content-between">
        <span class="level-tag" :class="levelBadgeClass"> Lv.{{ node.level }} </span>
        <span class="member-count-badge">
          <v-icon icon="mdi-account-group-outline" size="12" class="me-1" />
          {{ node.members.length }}명
        </span>
      </div>

      <!-- 2. 부서명 -->
      <div class="node-title text-truncate" :title="node.name">
        {{ node.name }}
      </div>

      <!-- 3. 부서장 / 책임자 영역 -->
      <div class="node-leader-box d-flex align-items-center justify-content-between">
        <span class="leader-label">
          <v-icon icon="mdi-account-tie" size="13" class="me-1 text-secondary" />
          책임자
        </span>
        <div class="leader-content text-truncate">
          <template v-if="node.leader">
            <span class="leader-name">{{ node.leader.name }}</span>
            <span v-if="node.leader.duty" class="leader-duty ms-1">({{ node.leader.duty }})</span>
          </template>
          <template v-else-if="node.manager_name">
            <span class="leader-name">{{ node.manager_name }}</span>
          </template>
          <template v-else>
            <span class="leader-empty">미지정</span>
          </template>
        </div>
      </div>

      <!-- 4. 주요 담당 업무 요약 (있는 경우) -->
      <div v-if="node.task" class="node-task-box text-truncate" :title="node.task">
        <v-icon icon="mdi-text-short" size="13" class="me-1 text-muted" />
        <span>{{ node.task }}</span>
      </div>

      <!-- 5. 하위 부서 접기/펼치기 직각 버튼 -->
      <div
        v-if="hasChildren"
        class="toggle-btn-wrapper"
        @click.stop="emit('toggle-collapse', node.id)"
      >
        <button
          class="toggle-btn"
          :class="{ 'is-collapsed': isCollapsed }"
          :title="isCollapsed ? '하위 부서 펼치기' : '하위 부서 접기'"
        >
          <v-icon :icon="isCollapsed ? 'mdi-plus' : 'mdi-minus'" size="12" />
        </button>
      </div>
    </div>

    <!-- 하위 자식 노드 (Tree Children) -->
    <div v-if="hasChildren && !isCollapsed" class="org-children-container">
      <!-- 부모 카드에서 수평 분기선으로 내려가는 상위 수직선 -->
      <div class="children-line"></div>

      <!-- 자식 노드 행 -->
      <div class="children-list">
        <OrgTreeNode
          v-for="child in node.children"
          :key="child.id"
          :node="child"
          :search-term="searchTerm"
          :collapsed-nodes="collapsedNodes"
          @toggle-collapse="emit('toggle-collapse', $event)"
          @select-dept="emit('select-dept', $event)"
          @select-staff="emit('select-staff', $event)"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.org-tree-branch {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  padding: 0 1rem;
}

/* ─────────────────────────────────────────────────────────────
   단정하고 품위 있는 직각(Zero Radius) 카드 스타일 (여유로운 패딩 적용)
───────────────────────────────────────────────────────────── */
.org-node-card {
  width: 204px;
  min-height: 112px;
  background-color: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 0 8px 8px 0 !important; /* 직각 엣지 */
  padding: 0.85rem 0.95rem 0.8rem 0.95rem;
  position: relative;
  cursor: pointer;
  text-align: left;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
  z-index: 2;
}

.org-node-card:hover {
  transform: translateY(-2px);
  border-color: #1e40af;
  box-shadow: 0 6px 16px rgba(15, 23, 42, 0.1) !important;
}

/* ── 레벨별 상단 액센트 보더 & 테마 ── */
.level-1 {
  border-top: 4px solid #0f172a; /* 딥 네이비 (Lv.1) */
}
.level-2 {
  border-top: 4px solid #0f766e; /* 딥 틸/에메랄드 (Lv.2) */
}
.level-3 {
  border-top: 4px solid #475569; /* 슬레이트 차콜 (Lv.3) */
}
.level-default {
  border-top: 4px solid #64748b;
}

.bg-navy {
  background-color: #0f172a !important;
}
.bg-teal {
  background-color: #0f766e !important;
}
.bg-slate {
  background-color: #475569 !important;
}

/* ── 헤더 영역 (레벨 태그 & 인원) ── */
.node-header {
  margin-bottom: 0.6rem;
}

.level-tag {
  font-size: 0.68rem;
  font-weight: 700;
  padding: 0.15rem 0.45rem;
  border-radius: 0 !important;
  display: inline-flex;
  align-items: center;
  letter-spacing: 0.03em;
  text-transform: uppercase;
}

.member-count-badge {
  font-size: 0.72rem;
  color: #334155;
  background-color: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 0 !important;
  padding: 0.15rem 0.45rem;
  display: inline-flex;
  align-items: center;
}

/* ── 부서명 ── */
.node-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
  line-height: 1.35;
  margin-bottom: 0.6rem;
}

/* ── 책임자 / 리더 정보 박스 ── */
.node-leader-box {
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 0 !important;
  padding: 0.38rem 0.55rem;
  font-size: 0.76rem;
  margin-bottom: 0.45rem;
}

.leader-label {
  font-size: 0.7rem;
  color: #64748b;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
}

.leader-content {
  max-width: 108px;
  text-align: right;
}

.leader-name {
  color: #0f172a;
  font-weight: 700;
}

.leader-duty {
  font-size: 0.7rem;
  color: #2563eb;
  font-weight: 600;
}

.leader-empty {
  font-size: 0.72rem;
  color: #94a3b8;
}

/* ── 주요 담당 업무 ── */
.node-task-box {
  font-size: 0.72rem;
  color: #64748b;
  line-height: 1.35;
  display: flex;
  align-items: center;
  padding: 0 0.1rem;
}

/* ── 검색어 일치 강조 효과 ── */
.node-matched {
  border-color: #d97706 !important;
  box-shadow: 0 0 0 2px #d97706 !important;
}

/* ── 하위 노드 토글 버튼 (스퀘어) ── */
.toggle-btn-wrapper {
  position: absolute;
  bottom: -10px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 4;
}

.toggle-btn {
  width: 20px;
  height: 20px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #94a3b8;
  border-radius: 0 !important; /* 직각 */
  background-color: #ffffff;
  color: #334155;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
  transition: all 0.15s ease;
}

.toggle-btn:hover {
  background-color: #0f172a;
  border-color: #0f172a;
  color: #ffffff;
}

.toggle-btn.is-collapsed {
  background-color: #f1f5f9;
  border-color: #64748b;
  color: #0f172a;
}

/* ─────────────────────────────────────────────────────────────
   수학적으로 정밀한 순수 계층 트리 연결선 (Pure CSS Tree Connectors)
───────────────────────────────────────────────────────────── */
.org-children-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  width: 100%;
}

/* 부모 노드 카드 아래에서 분기 지점까지 내려가는 수직선 */
.children-line {
  width: 2px;
  height: 20px;
  background-color: #94a3b8;
  margin: 0 auto;
}

/* 자식 브랜치들이 배치되는 행 */
.children-list {
  display: flex;
  justify-content: center;
  position: relative;
  padding: 0;
  margin: 0;
}

/* 자식 브랜치 개별 수신 연결선 (자식 카드 위 20px 여백 및 상단 수직선) */
.children-list > .org-tree-branch {
  position: relative;
  padding-top: 20px;
}

/* 각 자식 노드 상단 수직 연결선 (분기선 -> 자식 카드 상단) */
.children-list > .org-tree-branch::before {
  content: '';
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 2px;
  height: 20px;
  background-color: #94a3b8;
  z-index: 1;
}

/* 자식 노드들을 잇는 수평 분기 버스 라인 */
.children-list > .org-tree-branch::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background-color: #94a3b8;
}

/* 첫 번째 자식 노드: 중심(50%)에서 오른쪽으로만 수평선 확장 */
.children-list > .org-tree-branch:first-child::after {
  left: 50%;
  width: 50%;
}

/* 마지막 자식 노드: 왼쪽에서 중심(50%)까지만 수평선 확장 */
.children-list > .org-tree-branch:last-child::after {
  left: 0;
  width: 50%;
}

/* 외동 자식 노드 (1개일 때): 수평선 제거, 상위-하위 수직 직결 */
.children-list > .org-tree-branch:only-child::after {
  display: none;
}
</style>
