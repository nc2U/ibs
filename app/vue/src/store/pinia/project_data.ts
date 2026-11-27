import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import {
  type UnitType,
  type UnitFloorType,
  type BuildingUnit,
  type AllHouseUnit,
  type HouseUnit,
  type OptionItem,
} from '@/store/types/project'
import api from '@/api'
import { errorHandle, message } from '@/utils/helper'

export type CreateUnit = {
  project: number
  unit_type: number
  building_unit: number
  bldg_line: number
  floor_no: number
  name: string
  floor_type: number
  unit_code: string
}

export const useProjectData = defineStore('projectData', () => {
  // states & getters
  const unitTypeList = ref<UnitType[]>([])
  const simpleTypes = computed(() =>
    unitTypeList.value
      ? unitTypeList.value.map((t: UnitType) => ({
          pk: t.pk,
          name: t.name,
          color: t.color,
        }))
      : [],
  )
  const getTypes = computed(() =>
    unitTypeList.value.map(t => ({
      value: t.pk,
      label: t.name,
    })),
  )

  // actions
  const fetchTypeList = (projId: number, sort?: '1' | '2' | '3' | '4' | '5' | '6') =>
    api
      .get(`/type/?project=${projId}&sort=${sort || ''}`)
      .then(res => {
        unitTypeList.value = res.data.results
      })
      .catch(err => errorHandle(err))

  const createType = (payload: UnitType) =>
    api
      .post(`/type/`, payload)
      .then(res => fetchTypeList(res.data.project).then(() => message()))
      .catch(err => errorHandle(err))

  const updateType = (payload: UnitType) =>
    api
      .put(`/type/${payload.pk}/`, payload)
      .then(res => fetchTypeList(res.data.project).then(() => message()))
      .catch(err => errorHandle(err))

  const deleteType = (pk: number, project: number) =>
    api
      .delete(`/type/${pk}/`)
      .then(() =>
        fetchTypeList(project).then(() =>
          message('warning', '알림!', '해당 오브젝트가 삭제되었습니다.'),
        ),
      )
      .catch(err => errorHandle(err))

  // states & getters
  const floorTypeList = ref<UnitFloorType[]>([])
  const simpleFloors = computed(() =>
    floorTypeList.value
      ? floorTypeList.value.map((f: UnitFloorType) => ({
          pk: f.pk,
          start: f.start_floor,
          end: f.end_floor,
          name: f.alias_name,
        }))
      : [],
  )
  const getFloorTypes = computed(() =>
    floorTypeList.value.map(f => ({ value: f.pk, label: f.alias_name })),
  )

  // actions
  const fetchFloorTypeList = (projId: number, sort?: '1' | '2' | '3' | '4' | '5' | '6') =>
    api
      .get(`/floor/?project=${projId}&sort=${sort || ''}`)
      .then(res => (floorTypeList.value = res.data.results))
      .catch(err => errorHandle(err))

  const createFloorType = (payload: UnitFloorType) =>
    api
      .post(`/floor/`, payload)
      .then(res => fetchFloorTypeList(res.data.project).then(() => message()))
      .catch(err => errorHandle(err))

  const updateFloorType = (payload: UnitFloorType) =>
    api
      .put(`/floor/${payload.pk}/`, payload)
      .then(res => fetchFloorTypeList(res.data.project).then(() => message()))
      .catch(err => errorHandle(err))

  const deleteFloorType = (pk: number, project: number) =>
    api
      .delete(`/floor/${pk}/`)
      .then(() =>
        fetchFloorTypeList(project).then(() =>
          message('warning', '알림!', '해당 오브젝트가 삭제되었습니다.'),
        ),
      )
      .catch(err => errorHandle(err))

  // states & getters
  const buildingList = ref<BuildingUnit[]>([])

  // actions
  const fetchBuildingList = (projId: number) =>
    api
      .get(`/bldg/?project=${projId}`)
      .then(res => (buildingList.value = res.data.results))
      .catch(err => errorHandle(err))

  const createBuilding = (payload: BuildingUnit) =>
    api
      .post(`/bldg/`, payload)
      .then(res => fetchBuildingList(res.data.project).then(() => message()))
      .catch(err => errorHandle(err))

  const updateBuilding = (payload: BuildingUnit) =>
    api
      .put(`/bldg/${payload.pk}/`, payload)
      .then(res => fetchBuildingList(res.data.project).then(() => message()))
      .catch(err => errorHandle(err))

  const deleteBuilding = (pk: number, project: number) =>
    api
      .delete(`/bldg/${pk}/`)
      .then(() =>
        fetchBuildingList(project).then(() =>
          message('warning', '알림!', '해당 오브젝트가 삭제되었습니다.'),
        ),
      )
      .catch(err => errorHandle(err))

  // states & getters
  const houseUnitList = ref<AllHouseUnit[]>([])
  const isLoading = ref(false)
  const simpleUnits = computed(() =>
    houseUnitList.value
      ? houseUnitList.value.map(u => ({
          bldg: u.building_unit,
          color: simpleTypes.value
            .filter(t => t.pk === u.unit_type?.pk)
            .map((t: { color: string }) => t.color)[0],
          name: u.name,
          key_unit: u.key_unit,
          line: u.bldg_line,
          floor: u.floor_no,
          is_hold: u.is_hold,
          hold_reason: u.hold_reason,
        }))
      : [],
  )
  const mallExcludedUnits = computed(() =>
    houseUnitList.value.filter(u => u.unit_type?.sort && u.unit_type.sort < '5'),
  )
  const summarizeUnits = (units: typeof houseUnitList.value) => ({
    totalNum: units.length,
    holdNum: units.filter(u => u.is_hold).length,
    appNum: units.filter(u => u.key_unit?.contract?.contractor?.status === '1').length,
    contNum: units.filter(u =>
      ['2', '3'].includes(u.key_unit?.contract?.contractor?.status ?? ''),
    ).length,
  })
  const unitSummary = computed(() => summarizeUnits(mallExcludedUnits.value))
  const allUnitSummary = computed(() => summarizeUnits(houseUnitList.value))
  const numUnitByType = ref(0)

  // actions
  const fetchHouseUnitList = async (project: number, bldg?: number) => {
    isLoading.value = true
    let apiUri = `/all-house-unit/?building_unit__project=${project}`
    if (bldg) apiUri += `&building_unit=${bldg}`
    return await api
      .get(apiUri)
      .then(res => {
        houseUnitList.value = res.data.results
        isLoading.value = false
      })
      .catch(err => errorHandle(err))
  }

  const fetchNumUnitByType = (project: number, unit_type: number) =>
    api
      .get(`/house-unit/?building_unit__project=${project || ''}&unit_type=${unit_type}`)
      .then(res => (numUnitByType.value = res.data.count))
      .catch(err => errorHandle(err))

  const createUnit = async (payload: CreateUnit) => {
    const { project, unit_type, ...restPayload } = payload
    const { unit_code, ...unitPayload } = restPayload
    const houseUnits = { ...{ project, unit_type }, ...unitPayload, unit_code }

    await api.post(`/house-unit/`, houseUnits).catch(err => errorHandle(err))
    await fetchNumUnitByType(project, unit_type)
  }

  const updateUnit = async (payload: HouseUnit) => {
    const { pk, project, ...unitData } = payload
    return await api
      .put(`/house-unit/${pk}/`, unitData)
      .then(res => fetchNumUnitByType(project, res.data.unit_type).then(() => message()))
      .catch(err => errorHandle(err))
  }

  const patchUnit = async (payload: HouseUnit & { bldg: number }) => {
    const { pk, project, bldg, ...unitData } = payload
    return await api
      .put(`/house-unit/${pk}/`, unitData)
      .then(() => fetchHouseUnitList(project, bldg).then(() => message()))
      .catch(err => errorHandle(err))
  }

  const deleteUnit = (pk: number, project: number, unit_type: number) =>
    api
      .delete(`/house-unit/${pk}/`)
      .then(() =>
        fetchNumUnitByType(project, unit_type).then(() =>
          message('warning', '알림!', '해당 오브젝트가 삭제되었습니다.'),
        ),
      )
      .catch(err => errorHandle(err))

  // states & getters
  const optionItemList = ref<OptionItem[]>([])
  // const optionItem = ref()

  const fetchOptionItemList = (proj: number) =>
    api
      .get(`/option-item/?project=${proj}`)
      .then(res => (optionItemList.value = res.data.results))
      .catch(err => errorHandle(err))
  // const fetchOptionItem = (pk: number) => api.get(`/option-item/${pk}/`)

  const createOptionItem = (payload: OptionItem) =>
    api
      .post(`/option-item/`, payload)
      .then(res => fetchOptionItemList(res.data.project).then(() => message()))
      .catch(err => errorHandle(err))
  const updateOptionItem = (payload: OptionItem) =>
    api
      .put(`/option-item/${payload.pk}/`, payload)
      .then(res => fetchOptionItemList(res.data.project).then(() => message()))
      .catch(err => errorHandle(err))
  const deleteOptionItem = (pk: number, proj: number) =>
    api
      .delete(`/option-item/${pk}/`)
      .then(() =>
        fetchOptionItemList(proj).then(() =>
          message('warning', '알림!', '해당 오브젝트가 삭제되었습니다.'),
        ),
      )
      .catch(err => errorHandle(err))

  return {
    unitTypeList,
    simpleTypes,
    getTypes,
    fetchTypeList,
    createType,
    updateType,
    deleteType,

    floorTypeList,
    simpleFloors,
    getFloorTypes,
    fetchFloorTypeList,
    createFloorType,
    updateFloorType,
    deleteFloorType,

    buildingList,
    fetchBuildingList,
    createBuilding,
    updateBuilding,
    deleteBuilding,

    houseUnitList,
    isLoading,
    simpleUnits,
    unitSummary,
    allUnitSummary,
    numUnitByType,
    fetchHouseUnitList,
    fetchNumUnitByType,

    createUnit,
    updateUnit,
    patchUnit,
    deleteUnit,

    optionItemList,
    // optionItem,

    fetchOptionItemList,
    // fetchOptionItem,
    createOptionItem,
    updateOptionItem,
    deleteOptionItem,
  }
})
