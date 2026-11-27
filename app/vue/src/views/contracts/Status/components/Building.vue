<script lang="ts" setup>
import { ref, computed } from 'vue'
import { useProjectData } from '@/store/pinia/project_data'
import type { SimpleUnit } from './ContractBoard.vue'
import Unit from '@/views/contracts/Status/components/Unit.vue'

const props = defineProps<{
  bldg: number
  maxFloor?: number
  units: SimpleUnit[]
}>()

const maxPiloti = ref(3) // 맥스 피로티 층

const pDataStore = useProjectData()
const buildingList = computed(() => pDataStore.buildingList)

const lineList = computed(() => {
  const lines = [...new Set(props.units.map(u => u.line))]
  return lines.sort((prev, curr) => prev - curr)
})

const floorList = computed(() => {
  const floors = [...new Set(props.units.map(u => u.floor))]
  return floors.sort((prev, curr) => curr - prev)
})

const bldgWidth = computed(() => 40 * lineList.value.length)

// O(1) 유닛 조회를 위한 맵 인덱싱
const unitMap = computed(() => {
  const map = new Map<string, SimpleUnit>()
  for (const u of props.units) {
    map.set(`${u.line}-${u.floor}`, u)
  }
  return map
})

const getUnit = (line: number, floor: number) => unitMap.value.get(`${line}-${floor}`)

const getFirst = (floor: number) => {
  if (floor >= maxPiloti.value) {
    const lines = props.units
      .filter(u => u.floor === floor)
      .map(u => u.line)
      .sort((a, b) => a - b)
    return lines[0] ?? 1
  }
  return 1
}

const bldgName = (bldgId: number) =>
  buildingList.value.find(b => b.pk === bldgId)?.name || String(bldgId)
</script>

<template>
  <CCol class="ms-4 mt-5" :style="{ width: `${bldgWidth}px` }">
    <CRow v-for="i in floorList" :key="i" :style="{ width: `${bldgWidth}px` }">
      <Unit
        v-for="line in lineList"
        :key="line"
        :unit="getUnit(line, i)"
        :floor="i"
        :line="line"
        :max-piloti="maxPiloti"
        :first-line="getFirst(i)"
      />
    </CRow>
    <CRow :style="{ width: `${bldgWidth}px` }">
      <CCol class="text-center build-base">
        <strong>{{ bldgName(bldg) }} 동</strong>
      </CCol>
    </CRow>
  </CCol>
</template>

<style lang="scss" scoped>
.build-base {
  height: 36px;
  background: #666;
  color: white;
  line-height: 36px;
  vertical-align: middle;
  border: solid #555 1px;
}

.dark-theme {
  .build-base {
    background: #333;
  }
}
</style>
