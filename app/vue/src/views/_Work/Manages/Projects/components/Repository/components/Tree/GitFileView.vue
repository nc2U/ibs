<script lang="ts" setup>
import { ref } from 'vue'
// import hljs from 'highlight.js'
// import 'highlight.js/styles/github.css'
import { hljs } from 'diff2html/lib/ui/js/highlight.js-slim'

const msg = ref('File View')
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>
        <router-link to="">Git 저장소</router-link>
        / README.md
      </h5>
    </CCol>
  </CRow>

  <v-card>
    <v-card-title>{{ fileInfo.path }}</v-card-title>
  </v-card>
</template>
