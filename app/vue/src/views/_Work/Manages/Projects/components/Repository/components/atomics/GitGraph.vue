<script setup lang="ts">
import { computed, type PropType } from 'vue'
import type { Dag } from '@/store/types/work_git_repo.ts'

const props = defineProps({
  dags: {
    type: Object as PropType<Record<string, any>>,
    required: true,
  },
  repo: { type: Number, required: true },
})

const commits = computed<Dag[]>(() => Object.values(props.dags))

const xGap = 20
const yGap = 30
const xOffset = 10
const yOffset = 20

// SHA -> 위치 매핑
const shaToCoord = computed<Record<string, any>>(() => {
  const coord = {}
  commits.value.forEach((commit, index) => {
    coord[commit.sha] = {
      x: commit.space * xGap + xOffset,
      y: index * yGap + yOffset,
    }
  })
  return coord
})

const width = computed(() => {
  const maxSpace = Math.max(...commits.value.map(c => c.space || 0))
  return maxSpace * xGap + 100
})

const height = computed(() => commits.value.length * yGap + 100)
</script>

<template>
  <svg :width="width" :height="height" class="revision-graph pl-3">
    <g v-for="(commit, index) in commits" :key="commit.sha">
      <!-- 커밋 노드 -->
      <circle
        :cx="commit.space * xGap + xOffset"
        :cy="index * yGap + yOffset"
        r="3"
        fill="#BA0000"
      />

      <!-- 부모와 연결선 -->
      <!--      v-if="shaToCoord[parent]"-->
      <line
        v-for="parent in commit.parents"
        :x1="commit.space * xGap + xOffset"
        :y1="index * yGap + yOffset"
        :x2="shaToCoord[parent]?.x ?? 10"
        :y2="shaToCoord[parent]?.y ?? height - 100"
        stroke="#BA0000"
      />

      <!--      <text-->
      <!--        :x="commit.space * xGap + xOffset + 10"-->
      <!--        :y="index * yGap + yOffset + 3"-->
      <!--        font-size="10"-->
      <!--        fill="black"-->
      <!--      >-->
      <!--        {{ commit.space }}-->
      <!--      </text>-->
    </g>
  </svg>
</template>

<style lang="scss" scoped>
.revision-graph {
  padding-top: 26px;
  position: absolute;
  min-width: 1px;
}
</style>
