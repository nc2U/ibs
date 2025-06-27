<script lang="ts" setup>
import { computed, onMounted, type PropType, ref, watch } from 'vue'
import type { Dag } from '@/store/types/work_git_repo.ts'
import * as d3 from 'd3'

const props = defineProps({
  dags: { type: Object as PropType<Record<string, Dag>>, required: true },
  repo: { type: Number, required: true },
})

const graphContainer = ref<SVGSVGElement | null>(null)

const commits = computed<Dag[]>(() => Object.values(props.dags))

const curvedPath = (x1: number, y1: number, x2: number, y2: number): string => {
  const midX = (x1 + x2) / 2
  return d3.line().curve(d3.curveBasis)([
    [x1, y1],
    [midX, y1],
    [midX, y2],
    [x2, y2],
  ])!
}

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

const renderGraph = () => {
  if (!graphContainer.value) return

  // SVG 초기화
  d3.select(graphContainer.value).selectAll('*').remove()
  const svg = d3
    .select(graphContainer.value)
    .attr('width', width.value)
    .attr('height', height.value)

  // 연결선 데이터
  const links: { source: Dag; target: Dag | { x: number; y: number } }[] = []
  commits.value.forEach(commit => {
    commit.parents.forEach(parentSha => {
      const parentCoord = shaToCoord.value[parentSha]
      if (parentCoord) {
        // 페이지 내 부모
        links.push({ source: commit, target: { x: parentCoord.x, y: parentCoord.y } })
      } else {
        // 페이지 밖 부모: 그래프 하단까지 직선
        links.push({
          source: commit,
          target: { x: commit.space * xGap + xOffset, y: height.value - 10 },
        })
      }
    })
  })

  // 연결선 렌더링
  svg
    .selectAll('.link')
    .data(links)
    .enter()
    .append('path')
    .attr('d', d => {
      const x1 = d.source.space * xGap + xOffset
      const y1 = shaToCoord.value[d.source.sha].y
      const x2 = d.target.x
      const y2 = d.target.y
      const path = d3.path()
      path.moveTo(x1, y1)
      if (d.source.space === Math.round((d.target.x - xOffset) / xGap)) {
        // 동일 레인: 직선
        path.lineTo(x2, y2)
      } else {
        // 다른 레인: 베지어 곡선
        path.bezierCurveTo(x1, y1 + (y2 - y1) / 2, x2, y2 - (y2 - y1) / 2, x2, y2)
      }
      return path.toString()
    })
    .attr('stroke', '#BA0000')
    .attr('fill', 'none')
    .attr('stroke-width', 1.5)

  // 커밋 노드 렌더링
  svg
    .selectAll('.node')
    .data(commits.value)
    .enter()
    .append('circle')
    .attr('cx', d => d.space * xGap + xOffset)
    .attr('cy', d => shaToCoord.value[d.sha].y)
    .attr('r', 3)
    .attr('fill', '#BA0000')
    .append('title')
    .text(d => d.branches?.join(', ') || '')

  // 클릭 오버레이
  svg
    .selectAll('.node-overlay')
    .data(commits.value)
    .enter()
    .append('circle')
    .attr('cx', d => d.space * xGap + xOffset)
    .attr('cy', d => shaToCoord.value[d.sha].y)
    .attr('r', 10)
    .attr('fill', 'transparent')
    .attr('cursor', 'pointer')
    .on('click', (event, d) => {
      window.location.href = `/projects/ibs/repository/ibs/revisions/${d.sha}`
    })
}

onMounted(renderGraph)
watch(commits, renderGraph, { deep: true })
watch(() => window.innerWidth, renderGraph)
</script>

<template>
  <svg ref="graphContainer" class="revision-graph pl-3"></svg>
  <!--  <svg :width="width" :height="height" class="revision-graph pl-3">-->
  <!--    <g v-for="(commit, index) in commits" :key="commit.sha">-->
  <!--      &lt;!&ndash; 커밋 노드 &ndash;&gt;-->
  <!--      <circle-->
  <!--        :cx="commit.space * xGap + xOffset"-->
  <!--        :cy="index * yGap + yOffset"-->
  <!--        r="3"-->
  <!--        fill="#BA0000"-->
  <!--      />-->

  <!--      &lt;!&ndash; 부모와 연결선 &ndash;&gt;-->
  <!--      &lt;!&ndash;      v-if="shaToCoord[parent]"&ndash;&gt;-->
  <!--      &lt;!&ndash;      <line&ndash;&gt;-->
  <!--      &lt;!&ndash;        v-for="parent in commit.parents"&ndash;&gt;-->
  <!--      &lt;!&ndash;        :x1="commit.space * xGap + xOffset"&ndash;&gt;-->
  <!--      &lt;!&ndash;        :y1="index * yGap + yOffset"&ndash;&gt;-->
  <!--      &lt;!&ndash;        :x2="shaToCoord[parent]?.x ?? 10"&ndash;&gt;-->
  <!--      &lt;!&ndash;        :y2="shaToCoord[parent]?.y ?? height - 100"&ndash;&gt;-->
  <!--      &lt;!&ndash;        stroke="#BA0000"&ndash;&gt;-->
  <!--      &lt;!&ndash;      />&ndash;&gt;-->
  <!--      <path-->
  <!--        v-for="parent in commit.parents"-->
  <!--        :key="`${commit.sha}-${parent}`"-->
  <!--        :d="-->
  <!--          curvedPath(-->
  <!--            commit.space * xGap + xOffset,-->
  <!--            index * yGap + yOffset,-->
  <!--            shaToCoord[parent]?.x ?? 10,-->
  <!--            shaToCoord[parent]?.y ?? height - 100,-->
  <!--          )-->
  <!--        "-->
  <!--        stroke="#BA0000"-->
  <!--        fill="none"-->
  <!--      />-->

  <!--      &lt;!&ndash;      <text&ndash;&gt;-->
  <!--      &lt;!&ndash;        :x="commit.space * xGap + xOffset + 10"&ndash;&gt;-->
  <!--      &lt;!&ndash;        :y="index * yGap + yOffset + 3"&ndash;&gt;-->
  <!--      &lt;!&ndash;        font-size="10"&ndash;&gt;-->
  <!--      &lt;!&ndash;        fill="black"&ndash;&gt;-->
  <!--      &lt;!&ndash;      >&ndash;&gt;-->
  <!--      &lt;!&ndash;        {{ commit.space }}&ndash;&gt;-->
  <!--      &lt;!&ndash;      </text>&ndash;&gt;-->
  <!--    </g>-->
  <!--  </svg>-->
</template>

<style lang="scss" scoped>
.revision-graph {
  padding-top: 26px;
  position: absolute;
  min-width: 1px;
}
</style>
