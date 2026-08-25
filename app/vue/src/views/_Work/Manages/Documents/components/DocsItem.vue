<script lang="ts" setup="">
import { computed, type PropType } from 'vue'
import { useRoute } from 'vue-router'
import type { Docs } from '@/store/types/docs'
import { usePerms } from '@/composables/usePerms.ts'
import { cutString, timeFormat } from '@/utils/baseMixins'
import DOMPurify from 'dompurify'

defineProps({ docs: { type: Object as PropType<Docs>, required: true } })

const route = useRoute()

const { can, PERM } = usePerms()
const canDocsRead = computed(() => can(PERM.DOCS_READ))
</script>

<template>
  <v-card
    :to="
      canDocsRead
        ? { name: '(문서) - 보기', params: { projId: docs.project?.slug, docId: docs.pk } }
        : undefined
    "
    border
    class="mb-2 w-100 docs-item card-white no-underline"
    :class="[canDocsRead ? 'pointer' : 'cursor-not-allowed', docs.is_pinned ? 'card-yellow' : '']"
    flat
  >
    <v-card-text class="pa-3">
      <CRow align="center" :class="{ 'pinned-item-bg': docs.is_pinned }">
        <CCol sm="8" class="d-flex align-center">
          <!-- 핀 고정 아이콘 -->
          <v-icon
            v-if="docs.is_pinned"
            icon="mdi-pin"
            color="danger"
            class="mr-2 rotate-45"
            size="small"
          />
          <v-tooltip
            v-if="docs.security_level === '1' || docs.is_blind"
            location="top"
            :text="docs.is_blind ? '숨김 문서' : '1등급 비공개 문서'"
          >
            <template #activator="{ props: tooltipProps }">
              <v-icon
                v-bind="tooltipProps"
                :icon="docs.is_blind ? 'mdi-eye-off' : 'mdi-lock-outline'"
                :color="docs.is_blind ? 'error' : 'warning'"
                size="small"
                class="mr-2"
              />
            </template>
          </v-tooltip>
          <v-icon
            v-else-if="!docs.is_pinned"
            icon="mdi-text-box-plus-outline"
            color="blue-grey-lighten-3"
            class="mr-2"
          />

          <span class="mr-2 text-grey"> [{{ docs.project?.name }}] </span>
          <span v-if="docs.cate_name" class="mr-2" :style="{ color: docs.cate_color || 'inherit' }">
            [{{ docs.cate_name }}]
          </span>
          <span class="d-flex align-center text-primary font-weight-semibold">
            {{ cutString(docs.title, 50) }}
          </span>
          <v-chip
            v-if="docs.is_pinned"
            label
            size="x-small"
            color="amber-darken-3"
            class="ml-2 font-weight-bold text-white"
          >
            고정
          </v-chip>
          <v-chip
            v-if="docs.security_level === '1' || docs.is_blind"
            label
            size="x-small"
            :color="docs.is_blind ? 'error' : 'warning'"
            variant="tonal"
            class="ml-2"
          >
            {{ docs.is_blind ? 'BLIND' : '비공개' }}
          </v-chip>
        </CCol>
        <CCol sm="4" class="text-right text-grey small">
          <v-icon icon="mdi-clock-outline" size="x-small" class="mr-1" />
          {{ timeFormat(docs.created as string, 'min', '/') }}
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

<style scoped>
.pinned-item-bg {
  background-color: rgba(255, 193, 7, 0.05) !important;
  border-color: rgba(255, 193, 7, 0.3) !important;
}

body.dark-theme .pinned-item-bg {
  background-color: rgba(255, 193, 7, 0.02) !important;
  border-color: rgba(255, 193, 7, 0.15) !important;
}

.rotate-45 {
  transform: rotate(45deg);
}
</style>
