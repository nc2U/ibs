<script lang="ts" setup>
import type { PropType } from 'vue'
import type { RouteLocationRaw } from 'vue-router'
import type { selectProject } from '@/store/types/work_project'

type Variant = 'flat' | 'text' | 'elevated' | 'outlined' | 'plain' | 'tonal' | undefined

defineProps({
  name: { type: String, default: '새 아이템' },
  to: { type: [String, Object] as PropType<RouteLocationRaw>, default: undefined },
  icon: { type: String, default: 'mdi-plus-circle' },
  color: { type: String, default: 'primary' },
  iconColor: { type: String, default: 'success' },
  variant: { type: String as PropType<Variant>, default: 'text' },

  projectList: { type: Array as PropType<selectProject[]>, default: () => [] },
  projectTo: {
    type: Object as PropType<Record<string, unknown>>,
    default: undefined,
  },
  fontSize: { type: String, default: '0.98' },
})

const buildProjectTo = (projectTo: Record<string, unknown> | undefined, slug: string) => {
  const existingParams =
    projectTo && typeof projectTo.params === 'object' && projectTo.params !== null
      ? (projectTo.params as Record<string, unknown>)
      : {}
  return {
    ...(projectTo || {}),
    params: { ...existingParams, projId: slug },
  } as RouteLocationRaw
}
</script>

<template>
  <v-btn
    :to="to"
    :prepend-icon="icon"
    :color="color"
    :variant="variant"
    size="small"
    class="no-underline"
    :style="`font-size: ${fontSize}em`"
  >
    <template v-slot:prepend>
      <v-icon :color="iconColor"></v-icon>
    </template>
    {{ name }}

    <v-menu v-if="projectList.length" activator="parent">
      <v-list density="compact" nav>
        <v-list-item
          v-for="proj in projectList"
          :key="proj.slug"
          :to="buildProjectTo(projectTo, proj.slug)"
          class="no-underline"
        >
          <v-list-item-title>{{ proj.label }}</v-list-item-title>
        </v-list-item>
      </v-list>
    </v-menu>
  </v-btn>
</template>
