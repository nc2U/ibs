<script lang="ts" setup>
import { type PropType } from 'vue'
import type { BranchInfo, Repository, Tree } from '@/store/types/work_github.ts'
import BranchMenu from './HeaderMenu/BranchMenu.vue'
import TreeNode from './Tree/TreeNode.vue'

defineProps({
  branches: { type: Array as PropType<BranchInfo[]>, default: () => [] },
  tags: { type: Array as PropType<BranchInfo[]>, default: () => [] },
  repo: { type: Object as PropType<Repository>, required: true },
  defName: { type: String, default: 'master' },
  defBranch: { type: Object as PropType<BranchInfo>, required: true },
  defTree: { type: Array as PropType<Tree[]>, default: () => [] },
})

const emit = defineEmits(['file-view'])
</script>

<template>
  <CRow class="py-2 mb-2">
    <CCol col="6">
      <h5>
        <router-link to="">{{ repo?.slug }}</router-link>
        @ {{ defName }}
      </h5>
    </CCol>

    <CCol>
      <BranchMenu :def-branch="defName ?? ''" :branches="branches" :tags="tags" />
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
            v-for="node in defTree"
            :repo="repo.pk as number"
            :node="node"
            :key="node.sha"
            @file-view="emit('file-view', $event)"
          />
        </CTableBody>
      </CTable>
    </CCol>
  </CRow>
</template>
