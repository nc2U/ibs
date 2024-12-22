<script setup lang="ts">
import Multiselect from '@vueform/multiselect'
</script>

<template>
  <Multiselect
    mode="tags"
    autocomplete="label"
    :classes="{
      caret: 'multiselect-caret mr-4',
      search: 'form-control multiselect-search',
      tagsSearch: 'multiselect-tags-search',
    }"
    :add-option-on="['enter', 'tab']"
    searchable
  />
  <!--  :attrs="form.court ? {} : { required: true }"-->
</template>
