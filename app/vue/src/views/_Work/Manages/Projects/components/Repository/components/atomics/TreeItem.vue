<script lang="ts" setup>
import { defineProps, defineEmits } from 'vue'

interface TreeNode {
  name: string
  path: string
  type?: string
  children?: TreeNode[]
  fileNo?: number
}

const props = defineProps<{
  node: TreeNode
  depth: number
}>()

const emit = defineEmits(['into-path', 'diff-view'])
</script>

<template>
  <CRow>
    <CCol :style="`padding-left: ${depth * 20}px`">
      <span v-if="!node.type">
        <v-icon icon="mdi-folder-open" color="#EFD2A8" size="16" class="mr-1" />
        <a href="javascript:void(0)" @click="emit('into-path', node.path)">{{ node.name }}</a>
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
        <router-link :to="{ name: '(저장소) - 파일 보기', params: { path: node.path } }">
          {{ node.name }}
        </router-link>
        <span>
          (<router-link to="" @click.prevent="emit('diff-view', node.fileNo)">
            비교(diff) </router-link
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
      :depth="depth + 1"
      @into-path="emit('into-path', $event)"
      @diff-view="emit('diff-view', $event)"
    />
  </template>
</template>
