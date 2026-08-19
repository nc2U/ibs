<script setup lang="ts">
import { computed } from 'vue'
import type { Staff } from '@/store/types/company'

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

// 검색어 매칭 여부
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

const levelColorClass = computed(() => {
  switch (props.node.level) {
    case 1:
      return 'border-top-primary bg-primary-subtle'
    case 2:
      return 'border-top-success bg-success-subtle'
    case 3:
      return 'border-top-info bg-info-subtle'
    default:
      return 'border-top-secondary bg-light'
  }
})
</script>

<template>
  <div class="org-tree-branch">
    <!-- 부서 카드 노드 -->
    <div
      class="org-node-card shadow-sm"
      :class="[levelColorClass, { 'node-matched': isMatch }]"
      @click="emit('select-dept', node)"
    >
      <!-- 상단 레벨 뱃지 및 인원수 -->
      <div class="d-flex align-items-center justify-content-between mb-1">
        <span class="badge bg-secondary text-white small" style="font-size: 0.65rem">
          Lv.{{ node.level }}
        </span>
        <span class="badge bg-light text-dark border small" style="font-size: 0.68rem">
          <v-icon icon="mdi-account-group" size="x-small" class="me-1" />{{ node.members.length }}명
        </span>
      </div>

      <!-- 부서명 -->
      <div class="fw-bold fs-6 text-truncate mb-1" :title="node.name">
        {{ node.name }}
      </div>

      <!-- 부서장 / 책임자 -->
      <div class="node-leader small text-muted text-truncate mb-1">
        <v-icon icon="mdi-account-tie" size="x-small" class="me-1 text-primary" />
        <span v-if="node.leader" class="fw-medium text-dark">
          {{ node.leader.name }}
          <small v-if="node.leader.duty" class="text-primary">({{ node.leader.duty }})</small>
        </span>
        <span v-else-if="node.manager_name" class="fw-medium text-dark">
          {{ node.manager_name }}
        </span>
        <span v-else class="text-muted fst-italic">미지정</span>
      </div>

      <!-- 주요 업무 (있는 경우) -->
      <div v-if="node.task" class="node-task text-muted small text-truncate" :title="node.task">
        {{ node.task }}
      </div>

      <!-- 하위 부서 접기/펼치기 토글 버튼 -->
      <div v-if="hasChildren" class="toggle-btn-wrapper" @click.stop="emit('toggle-collapse', node.id)">
        <button class="btn btn-sm btn-light rounded-circle shadow-xs toggle-btn">
          <v-icon :icon="isCollapsed ? 'mdi-plus' : 'mdi-minus'" size="x-small" />
        </button>
      </div>
    </div>

    <!-- 하위 자식 노드들 (Tree Children) -->
    <div v-if="hasChildren && !isCollapsed" class="org-children-container">
      <div class="children-line"></div>
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
  padding: 0 0.75rem;
}

.org-node-card {
  width: 170px;
  min-height: 96px;
  border: 1px solid #dee2e6;
  border-top-width: 4px;
  border-radius: 0.5rem;
  padding: 0.65rem 0.75rem;
  background-color: #ffffff;
  cursor: pointer;
  position: relative;
  transition: all 0.2s ease-in-out;
  text-align: left;
}

.org-node-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.12) !important;
  border-color: #0d6efd;
}

.node-matched {
  border-color: #fd7e14 !important;
  box-shadow: 0 0 0 3px rgba(253, 126, 20, 0.35) !important;
  animation: pulse-border 1.5s infinite;
}

@keyframes pulse-border {
  0% {
    box-shadow: 0 0 0 0 rgba(253, 126, 20, 0.6);
  }
  70% {
    box-shadow: 0 0 0 6px rgba(253, 126, 20, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(253, 126, 20, 0);
  }
}

.border-top-primary {
  border-top-color: #0d6efd !important;
}

.border-top-success {
  border-top-color: #198754 !important;
}

.border-top-info {
  border-top-color: #0dcaf0 !important;
}

.border-top-secondary {
  border-top-color: #6c757d !important;
}

.node-task {
  font-size: 0.7rem;
  line-height: 1.2;
}

.toggle-btn-wrapper {
  position: absolute;
  bottom: -12px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 2;
}

.toggle-btn {
  width: 22px;
  height: 22px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #ced4da;
  background-color: #ffffff;
}

.toggle-btn:hover {
  background-color: #f8f9fa;
  border-color: #0d6efd;
}

/* 계층 트리 연결선 (Tree Connectors) */
.org-children-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  padding-top: 1.5rem;
}

/* 부모 노드에서 아래로 내려오는 수직선 */
.children-line {
  position: absolute;
  top: 0;
  left: 50%;
  width: 2px;
  height: 1.5rem;
  background-color: #cbd5e1;
}

.children-list {
  display: flex;
  position: relative;
  padding-top: 1.25rem;
}

/* 자식 노드들을 가로로 잇는 수평선 */
.children-list::before {
  content: '';
  position: absolute;
  top: 0;
  left: calc(85px + 0.75rem);
  right: calc(85px + 0.75rem);
  height: 2px;
  background-color: #cbd5e1;
}

/* 각 자식 노드 상단 수직 연결선 */
.children-list > .org-tree-branch::before {
  content: '';
  position: absolute;
  top: -1.25rem;
  left: 50%;
  width: 2px;
  height: 1.25rem;
  background-color: #cbd5e1;
}
</style>
