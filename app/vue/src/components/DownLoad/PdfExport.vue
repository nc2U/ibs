<script lang="ts" setup>
const props = defineProps({
  url: { type: String, default: '' },
  disabled: Boolean,
})
</script>

<template>
  <v-btn
    size="small"
    :href="props.url as string"
    flat
    :disabled="props.disabled"
    class="mt-1 mx-3"
    style="text-decoration: none"
  >
    <v-icon icon="mdi-file-pdf-box" color="red" class="mr-2" />
    Pdf Export
    <v-icon icon="mdi-download" color="grey" class="ml-2" />
  </v-btn>
</template>
