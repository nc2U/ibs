<script lang="ts" setup>
import { computed } from 'vue'
import { useProjectData } from '@/store/pinia/project_data'
import LazyBuilding from '@/views/contracts/Status/components/LazyBuilding.vue'

import { type KeyUnit } from '@/store/types/project'

export type SimpleUnit = {
  bldg: number
  color: string
  name: string
  key_unit: KeyUnit
  line: number
  floor: number
  is_hold: boolean
  hold_reason: string
}

const pDataStore = useProjectData()
const simpleUnits = computed(() => pDataStore.simpleUnits)

const getBldg = computed(() =>
  [...new Set(simpleUnits.value.map((u: SimpleUnit) => u.bldg))].sort(),
)
const maxFloor = computed(() => Math.max(...simpleUnits.value.map((u: SimpleUnit) => u.floor)))

const getUnits = (bldg: number): SimpleUnit[] =>
  simpleUnits.value.filter((u: SimpleUnit) => u.bldg === bldg)
</script>

<template>
  <CRow v-if="simpleUnits.length === 0">
    <CCol class="text-center p-5 text-danger"> 등록된 데이터가 없습니다.</CCol>
  </CRow>

  <div v-else class="buildings-container">
    <LazyBuilding
      v-for="bldg in getBldg"
      :key="bldg"
      :bldg="bldg"
      :max-floor="maxFloor"
      :units="getUnits(bldg)"
    />
  </div>
</template>

<style scoped>
.buildings-container {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 1rem;
}
</style>
