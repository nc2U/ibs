<script lang="ts" setup>
import { useDownload } from '@/composables/useDownload'

const props = defineProps({
  url: { type: String, default: '' },
  filename: { type: String, default: '' },
  disabled: Boolean,
})

const { downloadExcel } = useDownload()

const handleDownload = () => {
  if (!props.disabled && props.url) {
    // URL에서 파일명 추출 또는 기본값 사용
    const fileName = props.filename ? props.filename : `document_${Date.now()}.xlsx`
    downloadExcel(props.url, fileName)
  }
}
</script>

<template>
  <v-btn
    size="small"
    @click="handleDownload"
    flat
    :disabled="props.disabled"
    class="mt-1 mx-3"
    style="text-decoration: none"
  >
    <v-icon icon="mdi-microsoft-excel" color="green" class="mr-2" />
    Excel Export
    <v-icon icon="mdi-download" color="grey" class="ml-2" />
  </v-btn>
</template>
