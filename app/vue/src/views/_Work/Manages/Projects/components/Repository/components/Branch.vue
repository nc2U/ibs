<script lang="ts" setup>
import { type PropType, ref } from 'vue'
import { useGithub } from '@/store/pinia/work_github.ts'
import type { CommitInfo, Tree } from '@/store/types/work_github.ts'
import TreeNode from './Tree/TreeNode.vue'
import BranchTitle from './BranchTitle.vue'

const props = defineProps({
  repo: { type: Number, required: true },
  node: { type: Object as PropType<CommitInfo>, default: () => null },
})

const level = ref(0)
const nodeFold = ref(false)
const subTrees = ref([])

const gitStore = useGithub()
const getSubTrees = (repo: number, sha: string) => gitStore.fetchSubTree(repo, sha)

const toggleFold = async (node: Tree) => {
  if (nodeFold.value === false && !subTrees.value.length)
    subTrees.value = await getSubTrees(props.repo as number, node?.commit?.sha as string)
  nodeFold.value = !nodeFold.value
}
</script>

<template>
  <BranchTitle :indent="true" :version-name="node.name" :latest="node" @click="toggleFold" />
  <template v-if="nodeFold" class="pl-5">
    <TreeNode
      v-for="node in subTrees"
      :repo="repo as number"
      :node="node"
      :level="level + 1"
      :key="node.sha"
    />
  </template>
</template>
