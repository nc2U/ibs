<script lang="ts" setup>
import { computed } from 'vue'
import { AlertSecondary } from '@/utils/cssMixins.ts'
import type { RFile } from './components/RegFile.vue'
import RegFile from './components/RegFile.vue'

interface Props {
  files?: RFile[]
}

const props = withDefaults(defineProps<Props>(), {
  files: () => [],
})

const emit = defineEmits<{
  (e: 'file-delete', payload: { pk: number; del: boolean }): void
  (e: 'file-change', payload: { pk: number; file: File }): void
}>()

const basePath = computed(() => {
  const first = props.files[0]?.file
  if (!first) return ''
  let decoded = first
  try {
    decoded = decodeURI(first)
  } catch {
    // 잘못 인코딩된 URI는 원본 문자열 그대로 사용
  }
  if (decoded.includes('media/')) {
    return decoded.split('media/')[0] + 'media/'
  }
  return ''
})
</script>

<template>
  <CRow v-if="files && files.length" class="px-2">
    <CAlert :color="AlertSecondary">
      <small v-if="basePath">{{ basePath }}</small>
      <CCol v-for="file in files" :key="file.pk ?? file.file_name" xs="12">
        <RegFile
          :file="file"
          @file-delete="emit('file-delete', $event)"
          @file-change="emit('file-change', $event)"
        />
      </CCol>
    </CAlert>
  </CRow>
</template>
