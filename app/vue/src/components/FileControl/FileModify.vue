<script lang="ts" setup>
import { AlertSecondary } from '@/utils/cssMixins.ts'
import type { RFile } from './components/RegFile.vue'
import RegFile from './components/RegFile.vue'
import { CRow } from '@coreui/vue'

const props = defineProps({ files: { type: Array, default: () => [] } })

const emit = defineEmits(['file-delete', 'file-change'])

const devideUri = (uri: string) => {
  const devidedUri = decodeURI(uri).split('media/')
  return [devidedUri[0] + 'media/', devidedUri[1]]
}
</script>

<template>
  <CRow v-if="files && files.length" class="px-2">
    <CAlert :color="AlertSecondary">
      <small>{{ devideUri((files as RFile[])[0]?.file ?? ' ')[0] }}</small>
      <CCol v-for="(file, i) in files as RFile[]" :key="file.pk" xs="12" color="primary">
        <RegFile
          :file="file"
          :file-name="devideUri(file.file)[1]"
          @file-delete="emit('file-delete', $event)"
          @file-change="emit('file-change', $event)"
        />
      </CCol>
    </CAlert>
  </CRow>
</template>
