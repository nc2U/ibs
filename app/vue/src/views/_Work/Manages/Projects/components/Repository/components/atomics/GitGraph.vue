<script setup lang="ts">
import { computed } from 'vue'
import { buildGraphData } from './dagUtils'

const props = defineProps<{ dag: Record<string, any> }>()
const positions = computed(() => buildGraphData(props.dag))
const width = computed(() => 600)
const height = computed(() => Object.keys(props.dag).length * 60)
</script>

<template>
  <svg v-if="dag" :width="width" :height="height">
    <!-- edges -->
    <template v-for="(node, sha) in dag" :key="sha">
      <line
        v-for="parent in node.parents"
        :key="parent"
        :x1="positions[sha]?.x"
        :y1="positions[sha]?.y"
        :x2="positions[parent]?.x"
        :y2="positions[parent]?.y"
        stroke="gray"
      />
    </template>

    <!-- nodes -->
    <template v-for="(node, sha) in dag" :key="sha">
      <circle :cx="positions[sha]?.x" :cy="positions[sha]?.y" r="6" fill="black" />
      <text :x="positions[sha]?.x + 10" :y="positions[sha]?.y + 4" font-size="12" fill="black">
        {{ sha.slice(0, 6) }}
      </text>
    </template>
  </svg>
</template>
