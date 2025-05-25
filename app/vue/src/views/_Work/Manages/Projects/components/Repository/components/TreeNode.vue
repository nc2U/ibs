<script lang="ts" setup>
import { type PropType, ref } from 'vue'
import { elapsedTime } from '@/utils/baseMixins.ts'
import type { TreeNodeType } from '@/store/types/work_github.ts'

defineProps({ trees: { type: Array as PropType<TreeNodeType[]>, default: () => [] } })
</script>

<template>
  <CTableRow v-for="tree in trees as any[]" :key="tree">
    <CTableDataCell class="pl-5">
      <v-icon icon="mdi-chevron-right" size="16" class="pointer mr-1" />
      <v-icon icon="mdi-folder" color="#EFD2A8" size="16" class="pointer mr-1" />
      <router-link to="">{{ tree.name }}</router-link>
    </CTableDataCell>
    <CTableDataCell></CTableDataCell>
    <CTableDataCell class="text-center">
      <router-link to="">{{ tree.commit.sha }}</router-link>
    </CTableDataCell>
    <CTableDataCell class="text-right">
      {{ elapsedTime(tree.commit.date) }}
    </CTableDataCell>
    <CTableDataCell class="text-center">{{ tree.commit.author }}</CTableDataCell>
    <CTableDataCell>{{ tree.commit.message }}</CTableDataCell>
  </CTableRow>
</template>
