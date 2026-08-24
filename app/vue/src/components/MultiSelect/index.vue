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

<style lang="scss" scoped>
:deep(.form-control) {
  border: 1px solid var(--border-color, #d8dbe0);
  background-color: var(--background-color, white);
  color: var(--text-color, inherit);
}

:deep(.form-control:focus) {
  border-color: #86b7fe;
  box-shadow: 0 0 0 0.25rem rgba(114, 114, 114, 0.25);
}

:deep(.form-control.is-invalid) {
  border-color: #dc3545 !important;
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 13 13' width='12' height='12' fill='none' stroke='%23dc3545'%3e%3ccircle cx='6' cy='6' r='4.5' stroke-width='1'/%3e%3cpath d='M6 9h.01M6 3v4' stroke-width='1.5' stroke-linecap='round'/%3e%3c/svg%3e") !important;
  background-repeat: no-repeat !important;
  background-position: right calc(0.375em + 0.1875rem) center !important;
  background-size: calc(0.75em + 0.375rem) calc(0.75em + 0.375rem) !important;
  padding-right: calc(1.5em + 0.75rem) !important;
}

:deep(.form-control.is-valid) {
  border-color: #2eb85c !important;
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 9 9'%3e%3cpath fill='%232eb85c' d='M2.3 6.73L.6 4.53c-.4-1.04.46-1.4 1.1-.8l1.1 1.4 3.4-3.8c.6-.63 1.6-.27 1.2.7l-4 4.6c-.43.5-.8.4-1.1.1z'/%3e%3c/svg%3e") !important;
  background-repeat: no-repeat !important;
  background-position: right calc(0.375em + 0.1875rem) center !important;
  background-size: calc(0.75em + 0.375rem) calc(0.75em + 0.375rem) !important;
  padding-right: calc(1.5em + 0.75rem) !important;
}

:deep(.form-control.is-valid:focus) {
  box-shadow: 0 0 0 0.25rem rgba(46, 184, 92, 0.25) !important;
}
</style>
