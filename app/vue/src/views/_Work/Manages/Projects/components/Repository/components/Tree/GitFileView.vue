<script lang="ts" setup>
import { computed, type PropType, ref, watch } from 'vue'
import { btnSecondary } from '@/utils/cssMixins.ts'
import type { FileInfo } from '@/store/types/work_github.ts'
import sanitizeHtml from 'sanitize-html'

const props = defineProps({
  fileData: {
    type: Object as PropType<FileInfo>,
    required: true,
  },
})

const emit = defineEmits(['file-view-close'])
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>
        <router-link to="">Git 저장소</router-link>
        / {{ fileData.path }}
      </h5>
    </CCol>
  </CRow>

  <CRow class="my-4">
    <CCol>
      <v-btn size="small" variant="outlined" :color="btnSecondary" @click="emit('file-view-close')">
        돌아가기
      </v-btn>
    </CCol>
  </CRow>

  <CRow>
    <CCol class="file-content">
      <div class="file-viewer">
        <table>
          <tr class="bg-indigo-accent-3">
            <td class="px-5 strong">{{ fileData.path }}</td>
            <td>SHA: {{ fileData.sha }}</td>
            <td>Size: {{ fileData.size }} bytes</td>
          </tr>
        </table>
        <pre v-if="fileData.content" class="code-block"><code>{{ fileData.content }}</code></pre>
        <p v-else>Loading file...</p>
      </div>
    </CCol>
  </CRow>

  <CRow class="mt-4 mb-5">
    <CCol>
      <v-btn size="small" variant="outlined" :color="btnSecondary" @click="emit('file-view-close')"
        >돌아가기
      </v-btn>
    </CCol>
  </CRow>
</template>

<style lang="scss" scoped>
.code-block {
  background: #f8f8f8;
  padding: 1em;
  white-space: pre-wrap;
  font-family: monospace;
  border: 1px solid #ddd;
  border-radius: 4px;
}
</style>
