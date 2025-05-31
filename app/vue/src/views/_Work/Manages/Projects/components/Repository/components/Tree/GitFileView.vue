<script lang="ts" setup>
import { type PropType, ref } from 'vue'
import hljs from 'highlight.js'
import { btnLight } from '@/utils/cssMixins.ts'
// import 'highlight.js/styles/github.css'
// import { hljs } from 'diff2html/lib/ui/js/highlight.js-slim'

defineProps({
  fileData: {
    type: Object as PropType<{
      path: string
      sha: string
      content: string
    }>,
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

  <v-btn :color="btnLight" size="small" @click="emit('file-view-close')" class="mb-5">
    목록으로
  </v-btn>

  <v-card class="mb-5">
    <v-card-title>{{ fileData.path }}</v-card-title>
    <v-card-text>
      <pre><code ref="codeBlock" class="language-js">{{ fileData.content }}</code></pre>
    </v-card-text>
  </v-card>

  <v-btn :color="btnLight" size="small" @click="emit('file-view-close')" class="mb-5">
    목록으로
  </v-btn>
</template>
