<script setup lang="ts">
import { computed } from 'vue'
import { buildGraphData } from './dagUtils'

const props = defineProps<{ dags: Record<string, any>; repo: number }>()
const positions = computed(() => buildGraphData(props.dags))
const width = computed(() => 20)
const height = computed(() => Object.keys(props.dags).length * 30)
</script>

<template>
  <svg :width="width" :height="height" class="revision-graph pl-3">
    <!-- edges -->
    <template v-for="([key, node], i) in Object.entries(dags)" :key="key">
      <line
        v-for="parent in node.parents"
        :key="parent"
        :x1="positions[key]?.x"
        :y1="positions[key]?.y"
        :x2="positions[parent]?.x"
        :y2="i === Object.keys(dags).length - 1 ? positions[parent]?.y - 15 : positions[parent]?.y"
        stroke="#BA0000"
      />
    </template>

    <!-- nodes -->
    <template v-for="([sha, node], index) in Object.entries(dags)" :key="sha">
      <router-link :to="{ name: '(저장소) - 리비전 보기', params: { repoId: repo, sha } }">
        <circle :cx="positions[sha]?.x" :cy="positions[sha]?.y" r="4" fill="#BA0000" />
      </router-link>
      <!--      <text :x="positions[sha]?.x + 30" :y="positions[sha]?.y + 6" font-size="14" fill="#1D69D3">-->
      <!--        <router-link to="">{{ sha.slice(0, 8) }}</router-link>-->
      <!--        {{ positions }}-->
      <!--      </text>-->
    </template>
  </svg>
</template>

<style lang="scss" scoped>
.revision-graph {
  padding-top: 45px;
  position: absolute;
  min-width: 1px;
}
</style>
