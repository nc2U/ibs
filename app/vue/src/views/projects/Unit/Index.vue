<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import { pageTitle, navMenu } from '@/views/projects/_menu/headermixin5'
import { useProject } from '@/store/pinia/project'
import type { BuildingUnit, HouseUnitUpdatePayload, Project } from '@/store/types/project'
import { type CreateUnit, useProjectData } from '@/store/pinia/project_data'
import { message } from '@/utils/helper'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ProjectAuthGuard from '@/components/AuthGuard/ProjectAuthGuard.vue'
import UnitController from '@/views/projects/Unit/components/UnitController.vue'
import UnitTable from '@/views/projects/Unit/components/UnitTable.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const refAlertModal = ref()
const refUnitController = ref()

const bldgPk = ref<null | number>(null)
const bldgName = ref('')

const projStore = useProject()
const project = computed(() => (projStore.project as Project | null)?.pk)

const pDataStore = useProjectData()
const numUnitByType = computed(() => pDataStore.numUnitByType)
const simpleUnits = computed(() => pDataStore.simpleUnits)

const fetchTypeList = (projId: number) => pDataStore.fetchTypeList(projId)
const fetchFloorTypeList = (projId: number) => pDataStore.fetchFloorTypeList(projId)
const fetchBuildingList = (projId: number) => pDataStore.fetchBuildingList(projId)
const fetchHouseUnitList = (projId: number, bldg?: number) =>
  pDataStore.fetchHouseUnitList(projId, bldg)

const createBuilding = (payload: { project: number; name: string }) =>
  pDataStore.createBuilding(payload as BuildingUnit)
const createUnit = (payload: CreateUnit) => pDataStore.createUnit(payload)
const patchUnit = (payload: HouseUnitUpdatePayload & { project: number; bldg: number }) =>
  pDataStore.patchUnit(payload)
const deleteUnit = (pk: number, proj: number, type: number) => pDataStore.deleteUnit(pk, proj, type)

const bldgSelect = (bldg: { pk: number; name: string }) => {
  bldgPk.value = bldg.pk
  bldgName.value = bldg.name
  if (bldg.pk && project.value) fetchHouseUnitList(project.value, bldg.pk)
  else pDataStore.houseUnitList = []
}

export type OriginalUnit = {
  type: number
  building: number
  line: number
  minFloor: number
  maxFloor: number
  typeName: string
  maxLength: number
  maxUnits: number
  floors: {
    pk: number
    start: number
    end: number
    name: string
  }[]
}

const dongRegister = (dong: string) => {
  if (project.value) createBuilding({ project: project.value, name: dong })
}

const unitRegister = async (payload: OriginalUnit) => {
  if (!project.value) return

  if (payload.maxFloor < payload.minFloor) {
    refAlertModal.value?.callModal('입력 오류', '종료층은 시작층 이상이어야 합니다.')
    return
  }

  const unit_type = payload.type
  const building_unit = payload.building
  const bldg_line = payload.line
  const midWord = bldg_line < 10 ? '0' : ''
  const size = payload.maxFloor - payload.minFloor + 1
  const range = (size: number, min: number): number[] =>
    [...Array(size).keys()].map(key => key + min)
  const between = (x: number, min: number, max: number): boolean => x >= min && x <= max
  const getCode = (num: number, digit: number) => {
    const safeDigit = Math.max(1, digit)
    const prefix = '0'.repeat(Math.max(0, safeDigit - `${num}`.length))
    const typeStr = payload.typeName.replace(/[^0-9a-zA-Z]/g, '')
    const typeDigit = payload.maxLength - typeStr.length
    const suffix = typeDigit >= 1 ? '0'.repeat(typeDigit - 1) + '1' : ''
    return `${typeStr}${suffix}${prefix}${num}`
  }

  let num = numUnitByType.value // 해당 타입의 개수 구하기

  const existingFloors = simpleUnits.value
    .filter((u: { line: number }) => u.line === bldg_line)
    .map((u: { floor: number }) => u.floor)

  const requestedFloors = range(size, payload.minFloor)
  const isExist = requestedFloors.some(f => existingFloors.includes(f))

  if (isExist) {
    refAlertModal.value?.callModal(
      '중복 호수 알림',
      '해당 범위의 호수 중 이미 등록되어 있는 유니트가 있습니다.',
    )
    return
  }

  // 층타입 매핑 확인
  const inputUnits = requestedFloors.map(i => {
    const matchedFloor = payload.floors.find(f => between(i, f.start, f.end))
    return {
      floor_no: i,
      name: `${i < 0 ? `B${i * -1}` : i}${midWord}${bldg_line}`,
      floor_type: matchedFloor?.pk,
      unit_code: getCode((num += 1), `${payload.maxUnits}`.length),
    }
  })

  const unassigned = inputUnits.filter(u => !u.floor_type)
  if (unassigned.length > 0) {
    refAlertModal.value?.callModal(
      '층별 조건 미설정',
      '해당 범위 중 층별 조건(Floor Type)이 설정되지 않은 층이 있습니다. 먼저 층별 조건을 등록하세요.',
    )
    return
  }

  try {
    await Promise.all(
      inputUnits.map(unit =>
        createUnit({
          project: Number(project.value),
          unit_type,
          building_unit,
          bldg_line,
          floor_no: unit.floor_no,
          name: unit.name,
          floor_type: unit.floor_type as number,
          unit_code: unit.unit_code,
        }),
      ),
    )
    await fetchHouseUnitList(project.value, building_unit)
    message()
  } catch (err) {
    console.error(err)
    await fetchHouseUnitList(project.value, building_unit)
  }
}

const onUpdate = (payload: HouseUnitUpdatePayload) => {
  if (bldgPk.value) {
    const projId = project.value || projStore.currentProject
    if (projId) {
      patchUnit({
        ...payload,
        project: projId,
        bldg: bldgPk.value,
      })
    }
  } else {
    refAlertModal.value?.callModal('선택 알림', '동(건물)을 선택하세요!')
  }
}

const onDelete = async (payload: { pk: number; type: number }) => {
  const proj = project.value || projStore.currentProject
  if (proj) {
    await deleteUnit(payload.pk, proj, payload.type)
    if (bldgPk.value) {
      await fetchHouseUnitList(proj, bldgPk.value)
    }
  }
}

const dataSetup = async (pk: number) => {
  await Promise.all([fetchTypeList(pk), fetchFloorTypeList(pk), fetchBuildingList(pk)])
}

const dataReset = () => {
  pDataStore.unitTypeList = []
  pDataStore.floorTypeList = []
  pDataStore.buildingList = []
  pDataStore.houseUnitList = []
  bldgPk.value = null
  bldgName.value = ''
}

watch(
  () => project.value,
  newProjId => {
    if (refUnitController.value) refUnitController.value.projReset()
    dataReset()
    if (newProjId) dataSetup(newProjId)
  },
)

const loading = ref(true)
onBeforeMount(async () => {
  if (project.value) {
    await dataSetup(project.value)
    pDataStore.houseUnitList = []
  }
  loading.value = false
})

onBeforeRouteLeave(() => {
  dataReset()
})
</script>

<template>
  <ProjectAuthGuard>
    <Loading v-model:active="loading" />
    <ContentHeader :page-title="pageTitle" :nav-menu="navMenu" selector="ProjectSelect" />

    <ContentBody>
      <CCardBody class="pb-5">
        <UnitController
          ref="refUnitController"
          :project="project as number"
          @bldg-select="bldgSelect"
          @dong-register="dongRegister"
          @unit-register="unitRegister"
        />
        <UnitTable :bldg-name="bldgName" @on-update="onUpdate" @on-delete="onDelete" />
      </CCardBody>
    </ContentBody>

    <AlertModal ref="refAlertModal" />
  </ProjectAuthGuard>
</template>
