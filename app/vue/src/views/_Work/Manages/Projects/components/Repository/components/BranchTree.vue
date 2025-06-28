<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import type { Repository, Tree } from '@/store/types/work_git_repo.ts'
import { TableSecondary } from '@/utils/cssMixins.ts'
import BranchControl from './HeaderMenu/BranchControl.vue'
import TreeNode from './atomics/TreeNode.vue'

const props = defineProps({
  repo: { type: Object as PropType<Repository>, required: true },
  currPath: { type: String, default: '' },
  currRefs: { type: String, required: true },
  branchTree: { type: Array as PropType<Tree[]>, default: () => [] },
})

const emit = defineEmits(['into-path', 'change-refs'])

const intoPath = (path: string) => {
  const index = currentPath.value.indexOf(path)
  const nowPath = index === -1 ? null : currentPath.value.slice(0, index + 1).join('/')
  emit('into-path', nowPath)
}

const currentPath = computed<string[]>(() => (props.currPath ? props.currPath.split('/') : []))
</script>

<template>
  <CRow class="py-2 mb-2 flex-lg-row flex-column-reverse">
    <CCol class="col-6">
      <h5>
        <router-link to="" @click="emit('into-path', '')">{{ repo?.slug }}</router-link>
        <template v-if="currentPath.length">
          <span v-for="(path, i) in currentPath" :key="i">
            /
            <span v-if="i === currentPath.length - 1">{{ path }}</span>
            <router-link v-else to="" @click="intoPath(path)">{{ path }}</router-link>
          </span>
        </template>
        @ {{ currRefs }}
      </h5>
    </CCol>
    <CCol>
      <BranchControl :curr-refs="currRefs" @change-refs="emit('change-refs', $event)" />
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
          <CTableRow class="text-center" :color="TableSecondary">
            <CTableHeaderCell>이름</CTableHeaderCell>
            <CTableHeaderCell>크기</CTableHeaderCell>
            <CTableHeaderCell>리비전</CTableHeaderCell>
            <CTableHeaderCell>마지막 수정일</CTableHeaderCell>
            <CTableHeaderCell>작성자</CTableHeaderCell>
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
          />
        </CTableBody>
      </CTable>
    </CCol>
  </CRow>
</template>
