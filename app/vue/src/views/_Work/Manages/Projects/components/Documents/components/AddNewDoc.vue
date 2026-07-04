<script lang="ts" setup>
import { computed } from 'vue'
import { usePerms } from '@/composables/usePerms.ts'
import TopCreateButton from '@/views/_Work/components/atomics/TopCreateButton.vue'

const props = defineProps({ projStatus: { type: String, default: '' } })

const { can, PERM } = usePerms()
const canDocsCreate = computed(() => can(PERM.DOCS_CREATE) && props.projStatus !== '9')
</script>

<template>
  <CCol class="text-right">
    <span v-if="canDocsCreate" class="mr-2 form-text">
      <TopCreateButton name="새 문서" :to="{ name: '(문서) - 추가' }" :active="false" />
    </span>
  </CCol>
</template>
