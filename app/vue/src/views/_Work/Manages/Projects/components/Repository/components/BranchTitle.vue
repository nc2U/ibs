<script lang="ts" setup>
import { type PropType, ref } from 'vue'
import { cutString, elapsedTime } from '@/utils/baseMixins.ts'
import type { BranchInfo } from '@/store/types/work_github.ts'

defineProps({
  indent: { type: Boolean, default: false },
  versionName: { type: String, default: 'master' },
  latest: { type: Object as PropType<BranchInfo>, default: () => null },
})

const emit = defineEmits(['update-fold'])

const isFold = ref(false)

const updateFold = () => {
  isFold.value = !isFold.value
  emit('update-fold')
}
</script>

<template>
  <CTableRow>
    <CTableDataCell :class="{ 'pl-5': indent }">
      <span @click="updateFold">
        <v-icon :icon="`mdi-chevron-${isFold ? 'down' : 'right'}`" size="16" class="pointer mr-1" />
        <v-icon icon="mdi-folder" color="#EFD2A8" size="16" class="pointer mr-1" />
        <router-link to="">{{ versionName }}</router-link>
      </span>
    </CTableDataCell>
    <CTableDataCell class="text-right"></CTableDataCell>
    <CTableDataCell class="text-center">
      <router-link to="">{{ cutString(latest?.commit.sha, 5, '') }}</router-link>
    </CTableDataCell>
    <CTableDataCell class="text-right">
      {{ elapsedTime(latest?.commit.date) }}
    </CTableDataCell>
    <CTableDataCell class="text-center">{{ latest?.commit.author }}</CTableDataCell>
    <CTableDataCell>{{ latest?.commit.message }}</CTableDataCell>
  </CTableRow>
</template>
