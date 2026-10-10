<script lang="ts" setup>
import type { Link } from '@/store/types/docs.ts'
import { AlertSecondary } from '@/utils/cssMixins.ts'
import RegLink from './components/RegLink.vue'

interface Props {
  links?: Link[]
}

withDefaults(defineProps<Props>(), {
  links: () => [],
})

const emit = defineEmits<{
  (e: 'enable-store', event: Event): void
  (e: 'link-change', payload: { pk: number; link: string }): void
  (e: 'link-delete', payload: { pk: number; del: boolean }): void
}>()
</script>

<template>
  <CRow v-if="links && links.length" class="px-2">
    <CAlert :color="AlertSecondary">
      <CCol>
        <CInputGroup v-for="link in links" :key="link.pk" class="mb-2">
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
