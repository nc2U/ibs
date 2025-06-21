<script lang="ts" setup>
import { defineProps, defineEmits } from 'vue'
import { useRouter } from 'vue-router'
import { useGitRepo } from '@/store/pinia/work_git_repo.ts'

interface TreeNode {
  name: string
  path: string
  type?: string
  children?: TreeNode[]
  fileNo?: number
}

const props = defineProps<{
  node: TreeNode
  sha: string
  depth: number
}>()

const emit = defineEmits(['change-refs', 'into-path', 'diff-view'])

const gitStore = useGitRepo()
const setShaRefs = () => {
  gitStore.setRefsSort('sha')
  gitStore.setCurrRefs(props.sha)
  emit('change-refs', props.sha, true)
}

const intoPath = () => {
  setShaRefs()
  router.push({ name: '(저장소)' })
  emit('into-path', props.node.path)
}

const router = useRouter()
const viewFile = () => {
  setShaRefs()
  router.push({ name: '(저장소) - 파일 보기', params: { path: props.node.path } })
}
</script>

<template>
  <CRow>
    <CCol :style="`padding-left: ${depth * 20}px`">
      <span v-if="!node.type">
        <v-icon icon="mdi-folder-open" color="#EFD2A8" size="16" class="mr-1" />
        <a href="javascript:void(0)" @click="intoPath">{{ node.name }}</a>
      </span>
      <span v-else>
        <v-icon
          class="mr-1"
          :icon="
            {
              A: 'mdi-plus-circle',
              D: 'mdi-minus-circle',
              R: 'mdi-circle',
              C: 'mdi-circle',
              M: 'mdi-circle',
            }[node.type] || 'mdi-circle'
          "
          :color="
            {
              A: 'success',
              D: 'danger',
              R: 'purple',
              C: 'info',
              M: 'warning',
            }[node.type] || 'grey'
          "
          size="11"
        />
        <router-link to="" @click="viewFile"> {{ node.name }} </router-link>
        <span>
          (<router-link to="" @click.prevent="emit('diff-view', node.fileNo)"
            >비교(diff)</router-link
          >)
        </span>
      </span>
    </CCol>
  </CRow>

  <template v-if="node.children">
    <TreeItem
      v-for="(child, i) in node.children"
      :key="i"
      :node="child"
      :sha="sha"
      :depth="depth + 1"
      @into-path="emit('into-path', $event)"
      @diff-view="emit('diff-view', $event)"
    />
  </template>
</template>
