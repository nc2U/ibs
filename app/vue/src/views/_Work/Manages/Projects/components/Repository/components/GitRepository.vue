<script lang="ts" setup>
import { onMounted, type PropType, ref } from 'vue'
import type { BranchInfo, Repository, Tree } from '@/store/types/work_github.ts'
import BranchMenu from './HeaderMenu/BranchMenu.vue'
// import Branch from './Branch.vue'
// import BranchTitle from './BranchTitle.vue'
import TreeNode from './Tree/TreeNode.vue'

defineProps({
  repo: { type: Object as PropType<Repository>, default: () => null },
  // branches: { type: Array as PropType<BranchInfo[]>, default: () => [] },
  // tags: { type: Array as PropType<BranchInfo[]>, default: () => [] },
  defName: { type: String, default: 'master' },
  defBranch: { type: Object as PropType<BranchInfo>, default: () => null },
  defTree: { type: Array as PropType<Tree[]>, default: () => [] },
})

const emit = defineEmits(['file-view'])

const branchName = ref<string | null>('')

// const branchFold = ref(false)
// const tagFold = ref(false)
// const defFold = ref(false)

// const updateFold = (which: 1 | 2 | 3) => {
//   if (which === 1) branchFold.value = !branchFold.value
//   if (which === 2) tagFold.value = !tagFold.value
//   if (which === 3) defFold.value = !defFold.value
// }

// const getLatestBranch = (branches: BranchInfo[]) => {
//   if (branches.length === 0) return
//   return branches.reduce((last, curr) => {
//     const lastDate = new Date(last.commit.date)
//     const currDate = new Date(curr.commit.date)
//     return lastDate > currDate ? last : curr
//   })
// }

// const last_branch = computed(() => getLatestBranch(props.branches))
// const last_tag = computed(() => getLatestBranch(props.tags))
onMounted(() => {
  branchName.value = 'master'
})
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>
        <router-link to="">{{ 'ibs' }}</router-link>
        @ {{ branchName }}
      </h5>
    </CCol>

    <BranchMenu />
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
          <!--          <BranchTitle version-name="branches" :latest="last_branch" @update-fold="updateFold(1)" />-->
          <!--          <template v-if="branchFold">-->
          <!--            <Branch-->
          <!--              v-for="node in branches"-->
          <!--              :repo="repo.pk as number"-->
          <!--              :node="node"-->
          <!--              @file-view="emit('file-view', $event)"-->
          <!--            />-->
          <!--          </template>-->

          <!--          <BranchTitle version-name="tags" :latest="last_tag" @update-fold="updateFold(2)" />-->
          <!--          <template v-if="tagFold">-->
          <!--            <Branch-->
          <!--              v-for="node in tags"-->
          <!--              :repo="repo.pk as number"-->
          <!--              :node="node"-->
          <!--              @file-view="emit('file-view', $event)"-->
          <!--            />-->
          <!--          </template>-->

          <!--          <BranchTitle :version-name="defName" :latest="defBranch" @update-fold="updateFold(3)" />-->

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
