<script lang="ts" setup>
import type { PropType } from 'vue'
import type { selectProject } from '@/store/types/work_project.ts'

defineProps({
  name: { type: String, default: '새 아이템' },
  to: { type: Object, default: undefined },
  icon: { type: String, default: 'mdi-plus-circle' },
  color: { type: String, default: 'primary' },
  iconColor: { type: String, default: 'success' },

  projectList: { type: Array as PropType<selectProject[]>, default: () => [] },
  projectTo: { type: Object, default: undefined },
  fontSize: { type: String, default: '0.98' },
})
</script>

<template>
  <v-btn
    :to="to"
    :prepend-icon="icon"
    :color="color"
    variant="text"
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
          :to="{ ...projectTo, ...{ params: { projId: proj.slug } } }"
          class="no-underline"
        >
          <v-list-item-title>{{ proj.label }}</v-list-item-title>
        </v-list-item>
      </v-list>
    </v-menu>
  </v-btn>
</template>
