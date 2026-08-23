<script setup lang="ts">
import Multiselect from '@vueform/multiselect'
import type { PropType } from 'vue'

defineProps({
  mode: { type: String as PropType<'single' | 'tags'>, default: 'tags' },
  options: { type: Array, default: () => [] },
})
</script>

<template>
  <Multiselect
    :mode="mode"
    autocomplete="label"
    :classes="{
      caret: 'multiselect-caret mr-4',
      search: 'form-control multiselect-search',
      tagsSearch: 'multiselect-tags-search',
    }"
    :add-option-on="['enter', 'tab']"
    :options="options"
    searchable
  />
  <!--  :attrs="form.court ? {} : { required: true }"-->
</template>
