<script lang="ts" setup>
import { type PropType, ref } from 'vue'
import type { Tree } from '@/store/types/work_github.ts'
import { useGithub } from '@/store/pinia/work_github.ts'
import { elapsedTime, humanizeFileSize } from '@/utils/baseMixins.ts'
import TreeNode from './TreeNode.vue'

defineOptions({ name: 'TreeNode' })
const props = defineProps({
  repo: { type: Number, required: true },
  node: { type: Object as PropType<Tree>, required: true },
  level: { type: Number, default: 0 },
})

const nodeFold = ref(false)

const subTrees = ref([])

const gitStore = useGithub()
const getSubTrees = (repo: number, sha: string) => gitStore.fetchSubTree(repo, sha)

const toggleFold = async () => {
  if (nodeFold.value === false && !subTrees.value.length)
    subTrees.value = await getSubTrees(props.repo as number, props.node.sha)
  nodeFold.value = !nodeFold.value
}
</script>

<template>
  <CTableRow>
    <CTableDataCell class="pl-5">
      <span
        v-if="node.type === 'tree'"
        @click="toggleFold"
        :style="`padding-left: ${level * 15}px`"
      >
        <v-icon
          :icon="`mdi-chevron-${nodeFold ? 'down' : 'right'}`"
          size="16"
          class="pointer mr-1"
        />
        <v-icon icon="mdi-folder" color="#EFD2A8" size="16" class="pointer mr-1" />
        <router-link to="">{{ node.path }}</router-link>
      </span>
      <span class="pl-1">
        <span v-if="node.type === 'blob'" :style="`padding-left: ${level * 15}px`">
          <v-icon
            :icon="`mdi-file-${node.path.endsWith('.txt') ? 'document-' : ''}outline`"
            color="secondary"
            size="16"
            class="pointer mr-1 mdi-thin"
          />
          <router-link to="">{{ node.path }}</router-link>
        </span>
      </span>
    </CTableDataCell>
    <CTableDataCell class="text-right">
      {{ humanizeFileSize((node as any)?.size) }}
    </CTableDataCell>
    <CTableDataCell class="text-center">
      <router-link to="">{{ node.commit?.sha }}</router-link>
    </CTableDataCell>
    <CTableDataCell class="text-right">
      {{ elapsedTime(node.commit?.date) }}
    </CTableDataCell>
    <CTableDataCell class="text-center">{{ node.commit?.author }}</CTableDataCell>
    <CTableDataCell>{{ node.commit?.message }}</CTableDataCell>
  </CTableRow>

  <template v-if="nodeFold && subTrees">
    <TreeNode v-for="(node, i) in subTrees" :repo="repo" :node="node" :level="level + 1" :key="i" />
  </template>
</template>
