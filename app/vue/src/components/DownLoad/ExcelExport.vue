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

const { downloadExcel } = useDownload()

const isDisabled = computed(() => props.disabled || !props.url)

const handleDownload = () => {
  if (!isDisabled.value && props.url) {
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
    :disabled="isDisabled"
    variant="tonal"
    class="mt-1 mx-3"
    style="text-decoration: none"
  >
    <v-icon icon="mdi-microsoft-excel" color="green" class="mr-2" />
    Excel Export
    <v-icon icon="mdi-download" color="grey" class="ml-2" />
  </v-btn>
</template>
