<script lang="ts" setup>
import { computed } from 'vue'
import { useProjectData } from '@/store/pinia/project_data'
import { usePerms } from '@/composables/usePerms'
import type { HouseUnitUpdatePayload } from '@/store/types/project'
import Unit from '@/views/projects/Unit/components/Unit.vue'
import UnitForm from './UnitForm.vue'

defineProps({ bldgName: { type: String, default: '' } })
const emit = defineEmits<{
  (e: 'on-update', payload: HouseUnitUpdatePayload): void
  (e: 'on-delete', payload: { pk: number; type: number }): void
}>()

const { can, PERM } = usePerms()
const canProjectUpdate = computed(() => can(PERM.PROJECT_UPDATE))

const proDataStore = useProjectData()
const units = computed(() => proDataStore.simpleUnits)
const floorList = computed(() => [...new Set(units.value.map(u => u.floor))].sort((a, b) => b - a))
const lineList = computed(() => [...new Set(units.value.map(u => u.line))].sort((a, b) => a - b))
const houseUnitList = computed(() => proDataStore.houseUnitList)

const unitCol = computed(() => (lineList.value.length > 8 ? 12 : 5))
const formCol = computed(() => (lineList.value.length > 8 ? 12 : 7))

const unitMap = computed(() => {
  const map = new Map<string, (typeof units.value)[number]>()
  for (const u of units.value) {
    map.set(`${u.line}-${u.floor}`, u)
  }
  return map
})

const getUnit = (line: number, floor: number) => unitMap.value.get(`${line}-${floor}`) ?? null

const onUpdate = (payload: HouseUnitUpdatePayload) => emit('on-update', payload)
const onDelete = (payload: { pk: number; type: number }) => emit('on-delete', payload)
</script>

<template>
  <CContainer fluid>
    <CRow v-if="units.length === 0">
      <CCol class="text-center p-5 text-danger">등록된 데이터가 없습니다.</CCol>
    </CRow>

    <CRow v-else>
      <CCol :lg="unitCol" class="p-5">
        <CRow v-for="i in floorList" :key="i">
          <Unit
            v-for="line in lineList"
            :key="`${line}-${i}`"
            :unit="getUnit(line, i)"
            :floor="i"
            :line="line"
          />
        </CRow>
        <CRow v-if="lineList.length">
          <div
            class="text-center build-base"
            :style="{
              width: `${60 * lineList.length}px`,
            }"
          >
            {{ bldgName }}동
          </div>
        </CRow>
      </CCol>

      <CCol :lg="formCol">
        <CTable hover responsive align="middle">
          <colgroup>
            <col style="width: 11%" />
            <col style="width: 15%" />
            <col style="width: 10%" />
            <col style="width: 11%" />
            <col style="width: 9%" />
            <col style="width: 10%" />
            <col style="width: 6%" />
            <col :style="{ width: canProjectUpdate ? '18%' : '28%' }" />
            <col v-if="canProjectUpdate" style="width: 10%" />
          </colgroup>
          <CTableHead>
            <CTableRow class="text-center">
              <CTableHeaderCell>타입</CTableHeaderCell>
              <CTableHeaderCell>층범위타입</CTableHeaderCell>
              <CTableHeaderCell>동</CTableHeaderCell>
              <CTableHeaderCell>호수</CTableHeaderCell>
              <CTableHeaderCell>라인</CTableHeaderCell>
              <CTableHeaderCell>층수</CTableHeaderCell>
              <CTableHeaderCell>홀딩여부</CTableHeaderCell>
              <CTableHeaderCell>홀딩사유</CTableHeaderCell>
              <CTableHeaderCell v-if="canProjectUpdate">비고</CTableHeaderCell>
            </CTableRow>
          </CTableHead>

          <CTableBody>
            <UnitForm
              v-for="unit in houseUnitList"
              :key="unit.pk"
              :unit="unit"
              @on-update="onUpdate"
              @on-delete="onDelete"
            />
          </CTableBody>
        </CTable>
      </CCol>
    </CRow>
  </CContainer>
</template>

<style lang="scss" scoped>
.build-base {
  height: 36px;
  background: #777;
  color: white;
  line-height: 36px;
  vertical-align: middle;
}
</style>
