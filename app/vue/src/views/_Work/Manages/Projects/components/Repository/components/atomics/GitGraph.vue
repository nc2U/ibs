<script lang="ts" setup>
import { computed, type ComputedRef, inject, onMounted, ref, watch } from 'vue'
import type { Dag } from '@/store/types/work_git_repo.ts'
import { useRouter } from 'vue-router'
import * as d3 from 'd3'

const router = useRouter()

const props = defineProps({
  dags: { type: Object, required: true },
  repo: { type: Number, required: true },
})

const graphContainer = ref<SVGSVGElement | null>(null)

const isDark = inject<ComputedRef<boolean>>('isDark')
const dagColor = computed(() => (isDark?.value ? '#FFECB3' : '#BA0000'))
watch(dagColor, () => renderGraph())

const commits = computed(() => {
  const dags = props.dags as Record<string, Dag>
  const spaceMap = calculateSpace(dags)

  return Object.values(dags).map(dag => ({
    ...dag,
    space: spaceMap[dag.sha] ?? 0,
  }))
})

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

const height = computed(() => commits.value.length * yGap + 5)

const calculateSpace = (dags: Record<string, Dag>): Record<string, number> => {
  const spaceMap: Record<string, number> = {}
  let currentSpace = 0

  const commits = Object.values(dags).sort(
    (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime(),
  ) // 최신순

  for (const commit of commits) {
    const sha = commit.sha
    const parents = commit.parents

    if (!parents.length) {
      spaceMap[sha] = currentSpace++
    } else if (parents.length === 1) {
      const pSha = parents[0]
      const space = spaceMap[sha] ?? currentSpace
      if (!(pSha in spaceMap)) spaceMap[pSha] = space
    } else {
      for (let i = 0; i < parents.length; i++) {
        const pSha = parents[i]
        const space = currentSpace + parents.length - i - 1
        if (!(pSha in spaceMap)) spaceMap[pSha] = space
      }
    }
  }

  return spaceMap
}

const renderGraph = () => {
  if (!graphContainer.value) return

  // SVG 초기화
  d3.select(graphContainer.value).selectAll('*').remove()
  const svg = d3
    .select(graphContainer.value)
    .attr('width', width.value)
    .attr('height', height.value)

  // 연결선 데이터
  const links: { source: Dag; target: Dag | { x: number; y: number }; isLast?: boolean }[] = []
  commits.value.forEach((commit, index) => {
    const isLast = index === commits.value.length - 1

    commit.parents.forEach(pSha => {
      const parentCoord = shaToCoord.value[pSha]
      if (parentCoord) {
        // 페이지 내 부모
        links.push({ source: commit, target: { x: parentCoord.x, y: parentCoord.y } })
      } else {
        // 페이지 밖 부모
        links.push({
          source: commit,
          target: { x: xOffset, y: height.value },
          isLast,
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
      const x2 = (d.target as any)?.x
      const y2 = (d.target as any)?.y
      const path = d3.path()
      path.moveTo(x1, y1)
      if (d.source.space === Math.round(((d.target as any)?.x - xOffset) / xGap)) {
        // 동일 레인: 직선
        path.lineTo(x2, y2)
      } else {
        // 다른 레인: 베지어 곡선
        path.bezierCurveTo(x1, y1 + (y2 - y1) / 2, x2, y2 - (y2 - y1) / 2, x2, y2)
      }
      return path.toString()
    })
    .attr('stroke', dagColor.value)
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
    .attr('fill', dagColor.value)
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
    .on('click', (event, d) =>
      router.push({ name: '(저장소) - 리비전 보기', params: { repoId: props.repo, sha: d.sha } }),
    )
}

onMounted(renderGraph)
watch(commits, renderGraph, { deep: true })
watch(() => window.innerWidth, renderGraph)
</script>

<template>
  <svg ref="graphContainer" class="revision-graph pl-3"></svg>
</template>

<style lang="scss" scoped>
.revision-graph {
  padding-top: 26px;
  position: absolute;
}
</style>
