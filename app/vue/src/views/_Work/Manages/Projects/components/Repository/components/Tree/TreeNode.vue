<script lang="ts" setup>
import { type PropType, ref } from 'vue'
import type { Tree } from '@/store/types/work_github.ts'
import { useGithub } from '@/store/pinia/work_github.ts'
import { cutString, elapsedTime, humanizeFileSize } from '@/utils/baseMixins.ts'
import TreeNode from './TreeNode.vue'

defineOptions({ name: 'TreeNode' })
const props = defineProps({
  repo: { type: Number, required: true },
  node: { type: Object as PropType<Tree>, required: true },
  level: { type: Number, default: 0 },
})

const emit = defineEmits(['file-view'])

const nodeFold = ref(false)

const subTrees = ref([])

const gitStore = useGithub()

const fetchSubTree = (repo: number, sha: string, path: string | null = null) =>
  gitStore.fetchSubTree(repo, sha, path)

const fetchFileView = (repo: number, path: string, sha: string) =>
  gitStore.fetchFileView(repo, path, sha)

const toggleFold = async () => {
  if (nodeFold.value === false && !subTrees.value.length)
    subTrees.value = await fetchSubTree(
      props.repo as number,
      props.node?.commit?.sha as string,
      props.node?.path as string,
    )
  nodeFold.value = !nodeFold.value
}

const viewFile = async () => {
  const fileInfo = await fetchFileView(
    props.repo as number,
    props.node?.path as string,
    props.node?.commit?.sha as string,
  )
  emit('file-view', fileInfo)
}
</script>

<template>
  <CTableRow>
    <CTableDataCell>
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
        <router-link to="">{{ node.name }}</router-link>
      </span>
      <span class="pl-1" @click="viewFile">
        <span v-if="node.type === 'blob'" :style="`padding-left: ${level * 15}px`">
          <v-icon
            :icon="`mdi-file-${node.path.endsWith('.txt') ? 'document-' : ''}outline`"
            color="secondary"
            size="16"
            class="pointer mr-1 mdi-thin"
          />
          <router-link to="">{{ node.name }}</router-link>
        </span>
      </span>
    </CTableDataCell>
    <CTableDataCell class="text-right">
      {{ humanizeFileSize((node as any)?.size) }}
    </CTableDataCell>
    <CTableDataCell class="text-center">
      <router-link to="">{{ cutString(node.commit?.sha, 8, '') }}</router-link>
    </CTableDataCell>
    <CTableDataCell class="text-right">
      {{ elapsedTime(node.commit?.date) }}
    </CTableDataCell>
    <CTableDataCell class="text-center">{{ node.commit?.author }}</CTableDataCell>
    <CTableDataCell>{{ cutString(node.commit?.message, 60) }}</CTableDataCell>
  </CTableRow>

  <template v-if="nodeFold && subTrees">
    <TreeNode
      v-for="(node, i) in subTrees"
      :repo="repo"
      :node="node"
      :level="level + 1"
      :key="i"
      @file-view="emit('file-view', $event)"
    />
  </template>
</template>
