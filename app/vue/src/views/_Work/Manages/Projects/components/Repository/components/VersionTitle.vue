<script lang="ts" setup>
import { type PropType, ref } from 'vue'
import { elapsedTime } from '@/utils/baseMixins.ts'
import type { TreeNodeType } from '@/store/types/work_github.ts'

defineProps({
  verName: { type: String, default: 'master' },
  latest: { type: Object as PropType<TreeNodeType>, default: () => null },
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
    <CTableDataCell>
      <v-icon
        :icon="`mdi-chevron-${isFold ? 'down' : 'right'}`"
        size="16"
        class="pointer mr-1"
        @click="updateFold"
      />
      <v-icon icon="mdi-folder" color="#EFD2A8" size="16" class="pointer mr-1" />
      <router-link to="">{{ verName }}</router-link>
    </CTableDataCell>
    <CTableDataCell class="text-right"></CTableDataCell>
    <CTableDataCell class="text-center">
      <router-link to="">{{ latest?.commit.sha }}</router-link>
    </CTableDataCell>
    <CTableDataCell class="text-right">
      {{ elapsedTime(latest?.commit.date) }}
    </CTableDataCell>
    <CTableDataCell class="text-center">{{ latest?.commit.author }}</CTableDataCell>
    <CTableDataCell>{{ latest?.commit.message }}</CTableDataCell>
  </CTableRow>
</template>
