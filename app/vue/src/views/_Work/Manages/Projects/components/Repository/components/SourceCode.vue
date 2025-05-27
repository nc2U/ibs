<script lang="ts" setup>
import { computed, type PropType, ref } from 'vue'
import type { Repository, Tree, CommitInfo } from '@/store/types/work_github.ts'
import VersionTitle from './VersionTitle.vue'
import Versions from './Versions.vue'
import RepoTree from './Tree/RepoTree.vue'

const props = defineProps({
  repo: { type: Object as PropType<Repository>, default: () => null },
  branches: { type: Array as PropType<CommitInfo[]>, default: () => [] },
  tags: { type: Array as PropType<CommitInfo[]>, default: () => [] },
  defName: { type: String, default: 'master' },
  defBranch: { type: Object as PropType<CommitInfo>, default: () => null },
  defTree: { type: Array as PropType<Tree[]>, default: () => [] },
})

const token = computed(() => props.repo?.github_token)

const branchFold = ref(false)
const tagFold = ref(false)
const defFold = ref(false)

const updateFold = (which: 1 | 2 | 3) => {
  if (which === 1) branchFold.value = !branchFold.value
  if (which === 2) tagFold.value = !tagFold.value
  if (which === 3) defFold.value = !defFold.value
}

const getLatestBranch = (branches: CommitInfo[]) => {
  if (branches.length === 0) return
  return branches.reduce((last, curr) => {
    const lastDate = new Date(last.commit.date)
    const currDate = new Date(curr.commit.date)
    return lastDate > currDate ? last : curr
  })
}

const last_branch = computed(() => getLatestBranch(props.branches))
const last_tag = computed(() => getLatestBranch(props.tags))
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>
        <span><router-link to="">Git 저장소</router-link></span>
        <!--        <span v-if="1 == 2">/ <router-link to="">branches</router-link></span>-->
        <!--        <span v-if="1 == 2">/ <router-link to="">aaa</router-link></span>-->
      </h5>
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
          <VersionTitle ver-name="branches" :latest="last_branch" @update-fold="updateFold(1)" />
          <Versions v-if="branchFold" :versions="branches" />
          <!--          <TreeNode v-if="defFold" :trees="defTree" />-->

          <VersionTitle ver-name="tags" :latest="last_tag" @update-fold="updateFold(2)" />
          <Versions v-if="tagFold" :versions="tags" />
          <!--          <TreeNode v-if="defFold" :trees="defTree" />-->

          <VersionTitle :ver-name="defName" :latest="defBranch" @update-fold="updateFold(3)" />
          <RepoTree v-if="defFold" :trees="defTree" />
        </CTableBody>
      </CTable>
    </CCol>
  </CRow>
</template>
