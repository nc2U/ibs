<script lang="ts" setup>
import { computed } from 'vue'
import { usePerms } from '@/composables/usePerms.ts'

const props = defineProps({ projStatus: { type: String, default: '' } })

const { can, PERM } = usePerms()
const canDocsCreate = computed(() => can(PERM.DOCS_CREATE) && props.projStatus !== '9')
</script>

<template>
  <CCol class="text-right">
    <span v-if="canDocsCreate" class="mr-2 form-text">
      <v-icon icon="mdi-plus-circle" color="success" size="15" class="mr-1" />
      <router-link :to="{ name: '(문서) - 추가' }" class="ml-1">새 문서</router-link>
    </span>
  </CCol>
</template>
