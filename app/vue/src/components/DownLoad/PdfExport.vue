<script lang="ts" setup>
import { computed } from 'vue'
import { useDownload } from '@/utils/useDownload.ts'

interface Props {
  url?: string
  filename?: string
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  url: '',
  filename: '',
  disabled: false,
})

const { downloadPDF } = useDownload()

const isDisabled = computed(() => props.disabled || !props.url)

const handleDownload = () => {
  if (!isDisabled.value && props.url) {
    // URL에서 파일명 추출 또는 기본값 사용
    const fileName = props.filename ? props.filename : `document_${Date.now()}.pdf`
    downloadPDF(props.url, fileName)
  }
}
</script>

<template>
  <v-btn
    size="small"
    @click="handleDownload"
    flat
    :disabled="isDisabled"
    variant="tonal"
    class="mt-1 mx-3"
    style="text-decoration: none"
  >
    <v-icon icon="mdi-file-pdf-box" color="red" class="mr-2" />
    Pdf Export
    <v-icon icon="mdi-download" color="grey" class="ml-2" />
  </v-btn>
</template>
