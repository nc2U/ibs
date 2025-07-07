<script lang="ts" setup>
import type { Link } from '@/store/types/docs.ts'
import { AlertSecondary } from '@/utils/cssMixins.ts'
import RegLink from './components/RegLink.vue'

defineProps({ links: { type: Array, default: () => [] } })

const emit = defineEmits(['enable-store', 'link-change', 'link-delete'])
</script>

<template>
  <CRow class="px-2">
    <CAlert :color="AlertSecondary">
      <CCol>
        <CInputGroup v-for="(link, i) in links as Link[]" :key="link.pk" class="mb-2">
          <RegLink
            :link="link"
            @enable-store="emit('enable-store', $event)"
            @link-change="emit('link-change', $event)"
            @link-delete="emit('link-delete', $event)"
          />
        </CInputGroup>
      </CCol>
    </CAlert>
  </CRow>
</template>
