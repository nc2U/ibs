<script lang="ts" setup>
import type { PropType } from 'vue'
import type { Tree } from '@/store/types/work_github.ts'
import { elapsedTime, humanizeFileSize } from '@/utils/baseMixins.ts'

defineProps({ trees: { type: Array as PropType<Tree[]>, default: () => [] } })
</script>

<template>
  <CTableRow v-for="tree in trees" :key="tree.sha">
    <CTableDataCell class="pl-5">
      <span v-if="tree.type === 'tree'">
        <v-icon icon="mdi-chevron-right" size="16" class="pointer mr-1" />
        <v-icon icon="mdi-folder" color="#EFD2A8" size="16" class="pointer mr-1" />
      </span>
      <span v-if="tree.type === 'blob'" class="pl-5">
        <v-icon
          :icon="`mdi-file-${tree.path.endsWith('.txt') ? 'document-' : ''}outline`"
          color="secondary"
          size="16"
          class="pointer mr-1 mdi-thin"
        />
      </span>
      <router-link to="">{{ tree.path }}</router-link>
    </CTableDataCell>
    <CTableDataCell class="text-right">
      {{ humanizeFileSize((tree as any)?.size) }}
    </CTableDataCell>
    <CTableDataCell class="text-center">
      <router-link to="">{{ tree.commit?.sha }}</router-link>
    </CTableDataCell>
    <CTableDataCell class="text-right">
      {{ elapsedTime(tree.commit?.date) }}
    </CTableDataCell>
    <CTableDataCell class="text-center">{{ tree.commit?.author }}</CTableDataCell>
    <CTableDataCell>{{ tree.commit?.message }}</CTableDataCell>
  </CTableRow>
</template>
