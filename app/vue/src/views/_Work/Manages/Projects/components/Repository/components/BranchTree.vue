<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import type { BranchInfo, Repository, Tree } from '@/store/types/work_github.ts'
import BranchMenu from './HeaderMenu/BranchMenu.vue'
import TreeNode from './Tree/TreeNode.vue'

const props = defineProps({
  repo: { type: Object as PropType<Repository>, required: true },
  currPath: { type: String, default: null },
  branches: { type: Array as PropType<string[]>, default: () => [] },
  tags: { type: Array as PropType<string[]>, default: () => [] },
  currBranch: { type: String, required: true },
  branchTree: { type: Array as PropType<Tree[]>, default: () => [] },
})

const emit = defineEmits(['into-root', 'into-path', 'file-view', 'change-branch', 'change-tag'])

const currentPath = computed<string[]>(() => (props.currPath ? props.currPath.split('/') : []))
</script>

<template>
  <CRow class="py-2 mb-2 flex-lg-row flex-column-reverse">
    <CCol class="col-6">
      <h5>
        <router-link to="" @click="emit('into-root')">{{ repo?.slug }}</router-link>
        <template v-if="currentPath.length">
          <span v-for="path in currentPath" :key="path"> / {{ path }}</span>
        </template>
        @ {{ currBranch }}
      </h5>
    </CCol>

    <CCol>
      <BranchMenu
        :branches="branches"
        :tags="tags"
        @change-branch="emit('change-branch', $event)"
        @change-tag="emit('change-tag', $event)"
      />
    </CCol>
  </CRow>
  <CRow class="mb-5">
    <CCol>
      <CTable hover striped small responsive>
        <colgroup>
          <col style="width: 25%" />
          <col style="width: 8%" />
          <col style="width: 10%" />
          <col style="width: 8%" />
          <col style="width: 14%" />
          <col style="width: 35%" />
        </colgroup>
        <CTableHead>
          <CTableRow class="text-center">
            <CTableHeaderCell>이름</CTableHeaderCell>
            <CTableHeaderCell>크기</CTableHeaderCell>
            <CTableHeaderCell>리비전</CTableHeaderCell>
            <CTableHeaderCell>마지막 수정일</CTableHeaderCell>
            <CTableHeaderCell>저자</CTableHeaderCell>
            <CTableHeaderCell>설명</CTableHeaderCell>
          </CTableRow>
        </CTableHead>

        <CTableBody>
          <TreeNode
            v-for="node in branchTree"
            :repo="repo.pk as number"
            :node="node"
            :key="node.sha"
            @into-path="emit('into-path', $event)"
            @file-view="emit('file-view', $event)"
          />
        </CTableBody>
      </CTable>
    </CCol>
  </CRow>
</template>
