<script lang="ts" setup>
import { type PropType, ref } from 'vue'
import type { Commit, Tree } from '@/store/types/work_github.ts'
import { useGithub } from '@/store/pinia/work_github.ts'
import { cutString, elapsedTime, humanizeFileSize } from '@/utils/baseMixins.ts'
import TreeNode from './TreeNode.vue'

defineOptions({ name: 'TreeNode' })
const props = defineProps({
  repo: { type: Number, required: true },
  node: { type: Object as PropType<Tree>, required: true },
  level: { type: Number, default: 0 },
})

const emit = defineEmits(['into-path', 'file-view', 'revision-view'])

const nodeFold = ref(false)
const subTrees = ref([])
const gitStore = useGithub()

const fetchCommitBySha = (sha: string) => gitStore.fetchCommitBySha(sha)
const fetchSubTree = (payload: {
  repo: number
  sha?: string
  path?: string
  branch?: string
  tag?: boolean
}) => gitStore.fetchSubTree(payload)
const fetchFileView = (repo: number, path: string, sha: string) =>
  gitStore.fetchFileView(repo, path, sha)

const toggleFold = async () => {
  if (nodeFold.value === false && !subTrees.value.length)
    subTrees.value = await fetchSubTree({
      repo: props.repo as number,
      sha: props.node?.commit?.sha as string,
      path: props.node?.path as string,
    })
  nodeFold.value = !nodeFold.value
}

const intoPath = () =>
  emit('into-path', {
    path: props.node?.path as string,
    sha: props.node?.commit?.sha as string,
  })

const viewFile = async () =>
  emit('file-view', {
    path: props.node?.path as string,
    sha: props.node?.commit?.sha as string,
  })

const revisionView = async () => {
  await fetchCommitBySha(props.node?.commit?.sha as string)
  emit('revision-view')
}
</script>

<template>
  <CTableRow>
    <CTableDataCell>
      <span v-if="node.type === 'tree'" :style="`padding-left: ${level * 15}px`">
        <v-icon
          :icon="`mdi-chevron-${nodeFold ? 'down' : 'right'}`"
          @click="toggleFold"
          size="16"
          class="pointer mr-1"
        />
        <span @click="intoPath">
          <v-icon icon="mdi-folder" color="#EFD2A8" size="16" class="pointer mr-1" />
          <router-link to="">{{ node.name }}</router-link>
        </span>
      </span>

      <span v-else @click="viewFile">
        <span :style="`padding-left: ${level * 15 + 18}px`">
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
      <router-link to="" @click="revisionView">
        {{ cutString(node.commit?.sha, 8, '') }}
      </router-link>
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
      @into-path="emit('into-path', $event)"
      @file-view="emit('file-view', $event)"
      @revision-view="emit('revision-view', $event)"
    />
  </template>
</template>
