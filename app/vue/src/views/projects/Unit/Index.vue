<script lang="ts" setup>
import { ref, computed, onBeforeMount } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import { pageTitle, navMenu } from '@/views/projects/_menu/headermixin5'
import { useProject } from '@/store/pinia/project'
import { type HouseUnit, type Project } from '@/store/types/project'
import { type CreateUnit, useProjectData } from '@/store/pinia/project_data'
import { message } from '@/utils/helper'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ProjectAuthGuard from '@/components/AuthGuard/ProjectAuthGuard.vue'
import UnitController from '@/views/projects/Unit/components/UnitController.vue'
import UnitTable from '@/views/projects/Unit/components/UnitTable.vue'

const alertModal = ref()
const refUnitController = ref()

const bldgPk = ref<null | number>(null)
const bldgName = ref('')

const projStore = useProject()
const project = computed(() => (projStore.project as Project)?.pk)

const pDataStore = useProjectData()
const numUnitByType = computed(() => pDataStore.numUnitByType)
const simpleUnits = computed(() => pDataStore.simpleUnits)

const fetchTypeList = (projId: number) => pDataStore.fetchTypeList(projId)
const fetchFloorTypeList = (projId: number) => pDataStore.fetchFloorTypeList(projId)
const fetchBuildingList = (projId: number) => pDataStore.fetchBuildingList(projId)
const fetchHouseUnitList = (projId: number, bldg?: number) =>
  pDataStore.fetchHouseUnitList(projId, bldg)

const createBuilding = (payload: any) => pDataStore.createBuilding(payload)
const createUnit = (payload: CreateUnit) => pDataStore.createUnit(payload)
const patchUnit = (payload: HouseUnit & { bldg: number }) => pDataStore.patchUnit(payload)
const deleteUnit = (pk: number, proj: number, type: number) => pDataStore.deleteUnit(pk, proj, type)

const bldgSelect = (bldg: { pk: number; name: string }) => {
  if (!!bldg.pk && project.value) fetchHouseUnitList(project.value, bldg.pk)
  else pDataStore.houseUnitList = []
  bldgPk.value = bldg.pk
  bldgName.value = bldg.name
}

type OriginalUnit = {
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
  if (!!project.value) createBuilding({ project: project.value, name: dong })
}

const unitRegister = (payload: OriginalUnit) => {
  if (!!project.value) {
    const unit_type = payload.type
    const building_unit = payload.building
    const bldg_line = payload.line
    const midWord = bldg_line < 10 ? '0' : ''
    const size = payload.maxFloor - payload.minFloor + 1
    const range = (size: number, min: number): number[] =>
      [...Array(size).keys()].map(key => key + min)
    const between = (x: number, min: number, max: number): boolean => x >= min && x <= max // 주어진 x가 범위 내에 있늕지 확인하는 변수
    const getCode = (num: number, digit: number) => {
      const prefix = '0'.repeat(digit - `${num}`.length)
      const typeStr = payload.typeName.replace(/[^0-9a-zA-Z]/g, '')
      const typeDigit = payload.maxLength - typeStr.length
      const suffix = typeDigit >= 1 ? '0'.repeat(typeDigit - 1) + '1' : ''
      return `${typeStr}${suffix}${prefix}${num}`
    }

    let num = numUnitByType.value // 해당 타입의 개수 구하기

    const isExist = range(size, payload.minFloor).map(i =>
      simpleUnits.value
        .filter((u: { line: number }) => u.line === bldg_line)
        .map((u: { floor: number }) => u.floor)
        .includes(i),
    ) // 들록하려는 호수가 기존에 등록되어 있어 중복되고 있지 않은지 확인

    if (isExist.includes(true)) {
      // 중복되어 있는 경우 경고 후 로직 중단
      alert('해당 범위의 호수 중 이미 등록되어 있는 유니트가 있습니다.')
      return
    } else {
      // 중복되어 있지 않은 경우 로직 진행
      const inputUnits = range(size, payload.minFloor).map(i => ({
        floor_no: i,
        name: `${i < 0 ? `B${i * -1}` : i}${midWord}${bldg_line}`,
        floor_type: payload.floors
          .filter((f: { start: number; end: number }) => between(i, f.start, f.end))
          .map((f: { pk: number }) => f.pk)[0],
        unit_code: getCode((num += 1), `${payload.maxUnits}`.length),
      })) // 입력할 유닛 데이터 배열 생성

      inputUnits.forEach(unit => {
        createUnit({
          ...{
            project: Number(project.value),
            unit_type,
            building_unit,
            bldg_line,
          },
          ...unit,
        })
      }) // 생성된 배열을 디비에 등록
      fetchHouseUnitList(project.value, building_unit).then(() => message())
    }
  }
}

const onUpdate = (payload: HouseUnit) =>
  !!bldgPk.value
    ? patchUnit({
        ...payload,
        ...{
          project: project.value || projStore.initProjId,
          bldg: bldgPk.value,
        },
      })
    : alert('동(건물)을 선택하세요!')

const onDelete = (payload: { pk: number; type: number }) =>
  deleteUnit(payload.pk, project.value || projStore.initProjId, payload.type)

const dataSetup = (pk: number) => {
  fetchTypeList(pk)
  fetchFloorTypeList(pk)
  fetchBuildingList(pk)
}

const dataReset = () => {
  pDataStore.unitTypeList = []
  pDataStore.floorTypeList = []
  pDataStore.buildingList = []
  pDataStore.houseUnitList = []
}

const projSelect = (target: number | null) => {
  if (refUnitController.value) refUnitController.value.projReset()
  dataReset()
  if (!!target) dataSetup(target)
}

onBeforeMount(() => {
  dataSetup(project.value || projStore.initProjId)
  pDataStore.houseUnitList = []
})

const loading = ref(true)
onBeforeRouteLeave(async () => {
  dataReset()
  loading.value = false
})
</script>

<template>
  <ProjectAuthGuard>
    <Loading v-model:active="loading" />
    <ContentHeader
      :page-title="pageTitle"
      :nav-menu="navMenu"
      selector="ProjectSelect"
      @proj-select="projSelect"
    />

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

    <AlertModal ref="alertModal" />
  </ProjectAuthGuard>
</template>
