<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import type { Changed } from '@/store/types/work_git_repo.ts'
import TreeItem from './TreeItem.vue'

const props = defineProps({
  sha: { type: String, required: true },
  changeFiles: { type: Array as PropType<Changed[]>, default: () => [] },
})

const emit = defineEmits(['set-up-to', 'change-refs', 'into-path', 'diff-view'])

interface TreeNode {
  name: string
  path: string
  type?: string
  fileNo?: number
  children?: TreeNode[]
}

const buildTree = (files: Changed[]): TreeNode[] => {
  const root: TreeNode[] = []

  let fileIndex = 0
  for (const file of files) {
    const parts = file.path.split('/')
    let current = root
    let currentPath = ''

    for (let i = 0; i < parts.length; i++) {
      const part = parts[i]
      currentPath = currentPath ? `${currentPath}/${part}` : part

      let node = current.find(n => n.name === part)

      if (!node) {
        node = {
          name: part,
          path: currentPath,
        }

        if (i === parts.length - 1) {
          node.type = file.type // 파일일 경우만 type 저장
          node.fileNo = fileIndex
          fileIndex++
        } else {
          node.children = []
        }

        current.push(node)
      }

      if (node.children) {
        current = node.children
      }
    }
  }

  return root
}

const treeData = computed(() => buildTree(props.changeFiles))
</script>

<template>
  <CRow class="text-right">
    <CCol>
      <span class="mr-2" style="font-size: 0.8em">
        <v-icon icon="mdi-plus-circle" color="success" size="" /> 추가됨
      </span>
      <span class="mr-2" style="font-size: 0.8em">
        <v-icon icon="mdi-circle" color="warning" size="" /> 변경됨
      </span>
      <span class="mr-2" style="font-size: 0.8em">
        <v-icon icon="mdi-circle" color="info" size="" /> 복사됨
      </span>
      <span class="mr-2" style="font-size: 0.8em">
        <v-icon icon="mdi-circle" color="purple" size="" /> 이름바뀜
      </span>
      <span class="mr-2" style="font-size: 0.8em">
        <v-icon icon="mdi-minus-circle" color="danger" size="" /> 삭제됨
      </span>
    </CCol>
  </CRow>

  <template v-for="(node, index) in treeData" :key="index">
    <TreeItem
      :node="node"
      :sha="sha.substring(0, 8)"
      :depth="0"
      @change-refs="emit('change-refs', $event)"
      @into-path="emit('into-path', { path: $event, sha })"
      @diff-view="emit('diff-view', $event)"
    />
  </template>
</template>
