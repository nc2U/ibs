<script lang="ts" setup>
import { type PropType, ref } from 'vue'
import { elapsedTime } from '@/utils/baseMixins.ts'
import type { CommitInfo } from '@/store/types/work_github.ts'

defineProps({ versions: { type: Array as PropType<CommitInfo[]>, default: () => [] } })
</script>

<template>
  <CTableRow v-for="version in versions as any[]" :key="version.commit.sha">
    <CTableDataCell class="pl-5">
      <v-icon icon="mdi-chevron-right" size="16" class="pointer mr-1" />
      <v-icon icon="mdi-folder" color="#EFD2A8" size="16" class="pointer mr-1" />
      <router-link to="">{{ version.name }}</router-link>
    </CTableDataCell>
    <CTableDataCell></CTableDataCell>
    <CTableDataCell class="text-center">
      <router-link to="">{{ version.commit.sha }}</router-link>
    </CTableDataCell>
    <CTableDataCell class="text-right">
      {{ elapsedTime(version.commit.date) }}
    </CTableDataCell>
    <CTableDataCell class="text-center">{{ version.commit.author }}</CTableDataCell>
    <CTableDataCell>{{ version.commit.message }}</CTableDataCell>
  </CTableRow>
</template>
