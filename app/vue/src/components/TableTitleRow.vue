<script lang="ts" setup>
import ExcelExport from '@/components/DownLoad/ExcelExport.vue'
import PdfExport from '@/components/DownLoad/PdfExport.vue'

interface Props {
  color?: string
  title?: string
  excel?: boolean
  pdf?: boolean
  url?: string
  filename?: string
  disabled?: boolean
}

withDefaults(defineProps<Props>(), {
  color: 'indigo',
  title: '',
  excel: false,
  pdf: false,
  url: '',
  filename: '',
  disabled: false,
})
</script>

<template>
  <v-row class="justify-end my-1 pe-2">
    <v-col class="my-0 py-1 d-flex align-center">
      <slot name="title">
        <template v-if="title">
          <v-icon icon="mdi-arrow-right-bold-box" :color="color" class="me-1" />
          <h6 class="d-inline-block mb-0 fw-bold" style="font-size: 1em">
            {{ title }}
          </h6>
        </template>
      </slot>
    </v-col>

    <slot />

    <ExcelExport v-if="excel" :url="url" :filename="filename" :disabled="disabled" />
    <PdfExport v-if="pdf" :url="url" :filename="filename" :disabled="disabled" />

    <slot name="tail" />
  </v-row>
</template>
