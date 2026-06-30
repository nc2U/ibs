<script lang="ts" setup="">
import { computed, type PropType } from 'vue'
import type { Docs } from '@/store/types/docs'
import { usePerms } from '@/composables/usePerms.ts'
import { cutString, timeFormat } from '@/utils/baseMixins'
import DOMPurify from 'dompurify'

defineProps({ docs: { type: Object as PropType<Docs>, required: true } })

const { can, PERM } = usePerms()
const canDocsRead = computed(() => can(PERM.DOCS_READ))
</script>

<template>
  <v-card variant="flat" border class="mb-2 w-100 docs-item card-white">
    <v-card-text class="pa-3">
      <CRow align="center">
        <CCol sm="8" class="d-flex align-center">
          <v-tooltip
            v-if="docs.is_secret || docs.is_blind"
            location="top"
            :text="docs.is_secret ? '비밀 문서' : '숨김 문서'"
          >
            <template #activator="{ props: tooltipProps }">
              <v-icon
                v-bind="tooltipProps"
                :icon="docs.is_secret ? 'mdi-lock' : 'mdi-eye-off'"
                :color="docs.is_secret ? 'warning' : 'primary'"
                class="mr-2"
              />
            </template>
          </v-tooltip>
          <v-icon v-else icon="mdi-file-document" color="info" class="mr-2" />

          <span v-if="docs.cate_name" class="mr-2" :style="{ color: docs.cate_color || 'inherit' }">
            [{{ docs.cate_name }}]
          </span>
          <router-link
            v-if="canDocsRead"
            :to="{ name: '(문서) - 보기', params: { docId: docs.pk } }"
            class="text-decoration-none font-weight-medium text-body-1"
          >
            {{ cutString(docs.title, 50) }}
          </router-link>
          <span v-else class="d-flex align-center">
            {{ cutString(docs.title, 50) }}
          </span>
          <v-chip
            v-if="docs.is_secret || docs.is_blind"
            label
            size="x-small"
            :color="docs.is_secret ? 'warning' : 'primary'"
            variant="tonal"
            class="ml-2"
          >
            {{ docs.is_secret ? 'SECRET' : 'BLIND' }}
          </v-chip>
        </CCol>
        <CCol sm="4" class="text-right text-grey small">
          <v-icon icon="mdi-clock-outline" size="x-small" class="mr-1" />
          {{ timeFormat(docs.created as string, 'short', '/') }}
        </CCol>
      </CRow>
      <CRow v-if="docs.description" class="mt-2">
        <CCol class="text-body-2 text-muted">
          <div v-html="DOMPurify.sanitize(cutString(docs.description, 120))" />
        </CCol>
      </CRow>
    </v-card-text>
  </v-card>
</template>
