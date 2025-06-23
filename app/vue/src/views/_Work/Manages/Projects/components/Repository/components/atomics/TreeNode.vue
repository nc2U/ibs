<script lang="ts" setup>
import { type PropType, ref } from 'vue'
import type { Tree } from '@/store/types/work_git_repo.ts'
import { useGitRepo } from '@/store/pinia/work_git_repo.ts'
import { cutString, elapsedTime, humanizeFileSize } from '@/utils/baseMixins.ts'
import TreeNode from './TreeNode.vue'

defineOptions({ name: 'TreeNode' })

const props = defineProps({
  repo: { type: Number, required: true },
  node: { type: Object as PropType<Tree>, required: true },
  level: { type: Number, default: 0 },
})

const emit = defineEmits(['into-path', 'revision-view'])

const nodeFold = ref(false)
const subTrees = ref([])

const gitStore = useGitRepo()
const fetchRefTree = (payload: { repo: number; refs: string; path?: string; sub?: boolean }) =>
  gitStore.fetchRefTree({ ...payload, ret: payload.sub ?? false })

const toggleFold = async () => {
  if (nodeFold.value === false && !subTrees.value.length)
    subTrees.value = await fetchRefTree({
      repo: props.repo as number,
      refs: props.node?.commit?.sha || '',
      path: props.node?.path as string,
      sub: true,
    })
  nodeFold.value = !nodeFold.value
}
</script>

<template>
  <CTableRow>
    <CTableDataCell>
      <span v-if="node.type === 'tree'" :style="`padding-left: ${level * 15}px`">
        <v-icon
          :icon="`mdi-chevron-${nodeFold ? 'down' : 'right'}`"
          size="16"
          class="pointer mr-1"
          @click="toggleFold"
        />
        <span @click="emit('into-path', node?.path as string)">
          <v-icon icon="mdi-folder" color="#EFD2A8" size="16" class="pointer mr-1" />
          <router-link to="">{{ node.name }}</router-link>
        </span>
      </span>

      <span v-else>
        <span :style="`padding-left: ${level * 15 + 18}px`">
          <v-icon
            :icon="`mdi-file-${node.path.endsWith('.txt') ? 'document-' : ''}outline`"
            color="secondary"
            size="16"
            class="pointer mr-1 mdi-thin"
          />
          <router-link
            :to="{
              name: '(저장소) - 파일 보기',
              params: { repoId: repo, sha: node.commit?.sha, path: node.path },
            }"
          >
            {{ node.name }}
          </router-link>
        </span>
      </span>
    </CTableDataCell>
    <CTableDataCell class="text-right">
      {{ humanizeFileSize((node as any)?.size) }}
    </CTableDataCell>
    <CTableDataCell class="text-center">
      <router-link
        :to="{
          name: '(저장소) - 리비전 보기',
          params: { repoId: repo, sha: node?.commit?.sha },
        }"
      >
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
    />
  </template>
</template>
