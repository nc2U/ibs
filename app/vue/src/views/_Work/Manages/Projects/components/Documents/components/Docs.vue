<script lang="ts" setup="">
import { type PropType } from 'vue'
import type { Docs } from '@/store/types/docs'
import { cutString, timeFormat } from '@/utils/baseMixins'
import DOMPurify from 'dompurify'

defineProps({ docs: { type: Object as PropType<Docs>, required: true } })
</script>

<template>
  <v-card variant="flat" border class="mb-2 w-100 docs-item">
    <v-card-text class="pa-3">
      <CRow align="center">
        <CCol sm="8" class="d-flex align-center">
          <v-icon icon="mdi-file-document-outline" color="grey" class="mr-2" />
          <router-link
            :to="{ name: '(문서) - 보기', params: { docId: docs.pk } }"
            class="text-decoration-none font-weight-medium text-body-1"
          >
            <span
              v-if="docs.cate_name"
              class="mr-1"
              :style="{ color: docs.cate_color || 'inherit' }"
            >
              [{{ docs.cate_name }}]
            </span>
            {{ cutString(docs.title, 50) }}
          </router-link>
        </CCol>
        <CCol sm="4" class="text-right text-grey small">
          <v-icon icon="mdi-clock-outline" size="x-small" class="mr-1" />
          {{ timeFormat(docs.created as string, true, '/') }}
        </CCol>
      </CRow>
      <CRow v-if="docs.content" class="mt-2">
        <CCol class="text-body-2 text-muted">
          <div v-html="DOMPurify.sanitize(cutString(docs.content, 120))" />
        </CCol>
      </CRow>
    </v-card-text>
  </v-card>
</template>
