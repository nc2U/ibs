<script lang="ts" setup>
import type { PropType } from 'vue'
import type { IssueProject } from '@/store/types/work_project.ts'

defineProps({
  name: { type: String, default: '새 아이템' },
  to: { type: Object, default: undefined },
  icon: { type: String, default: 'mdi-plus-circle' },
  color: { type: String, default: 'primary' },
  iconColor: { type: String, default: 'success' },

  myProjects: { type: Array as PropType<IssueProject[]>, default: () => [] },
  projectTo: { type: Object, default: undefined },
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
  >
    <template v-slot:prepend>
      <v-icon :color="iconColor"></v-icon>
    </template>
    {{ name }}

    <v-menu v-if="myProjects.length" activator="parent">
      <v-list density="compact" nav>
        <v-list-item
          v-for="proj in myProjects"
          :key="proj.slug"
          :to="{ ...projectTo, ...{ params: { projId: proj.slug } } }"
          :style="{ paddingLeft: `${(proj.depth || 0) * 12}px` }"
          :class="{ child: proj.depth }"
          class="no-underline"
        >
          <v-list-item-title>{{ proj.name }}</v-list-item-title>
        </v-list-item>
      </v-list>
    </v-menu>
  </v-btn>
</template>

<style lang="scss" scoped>
.child::before {
  content: '»';
  margin-right: 6px;
  color: #666666;
}
</style>
