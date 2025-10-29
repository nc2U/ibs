<script lang="ts" setup>
import ExcelExport from '@/components/DownLoad/ExcelExport.vue'
import PdfExport from '@/components/DownLoad/PdfExport.vue'

defineProps({
  color: { type: String, default: 'indigo' },
  title: { type: String, default: '' },
  excel: Boolean,
  pdf: Boolean,
  url: { type: String, default: '' },
  filename: { type: String, default: '' },
  disabled: Boolean,
})
</script>

<template>
  <v-row class="justify-end my-1 pr-2">
    <v-col class="my-0 py-1">
      <v-icon
        v-if="title"
        icon="mdi-arrow-right-bold-box"
        rounded="pill"
        :color="color"
        class="mr-1"
      />
      <h6 class="d-inline-block" style="font-size: 1em; font-weight: bold">
        {{ title }}
      </h6>
    </v-col>

    <slot />

    <ExcelExport v-if="excel" :url="url" :filename="filename" :disabled="disabled" />
    <PdfExport v-if="pdf" :url="url" :filename="filename" :disabled="disabled" />

    <slot name="tail" />
  </v-row>
</template>
