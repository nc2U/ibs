import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ProjectFilter, selectProject } from '@/store/types/work_project.ts'

export const useProjectFilter = defineStore('projectFilter', () => {
  // 1. 활성화된 검색 조건 태그 및 체크박스 필드
  const searchCond = ref<string[]>(['status'])
  const enabledFields = ref<string[]>(['status'])

  // 2. 연산자 조건
  const defaultCond: Record<string, any> = {
    status: 'is',
    project: 'is',
    parent: 'all',
    is_public: 'is',
    created: 'is',
    updated: 'is',
    name: 'contains',
    description: 'contains',
  }
  const cond = ref<Record<string, any>>({ ...defaultCond })

  // 3. 폼 입력값
  const defaultForm: ProjectFilter & Record<string, any> = {
    status: '1',
    is_public: '1',
    created_date: '',
    created_date2: '',
    updated_date: '',
    updated_date2: '',
    name: '',
    description: '',
    bookmark: undefined,
    my_project: undefined,
  }
  const form = ref<ProjectFilter & Record<string, any>>({ ...defaultForm })

  // 4. 셀렉트 UI 바인딩용 보조 상태 (내 워크스페이스/즐겨찾기/닫힘 및 상위 워크스페이스 선택)
  const selectedProjectVal = ref<number | string>('')
  const selectedParentVal = ref<number | string>('')

  // 5. 필터 페이로드 생성 로직
  const buildFilterPayload = (allReadableProjects: selectProject[] = []): ProjectFilter => {
    const filterData = {} as ProjectFilter & Record<string, any>

    if (enabledFields.value.includes('status')) {
      if (cond.value.status === 'is') filterData.status = form.value.status
      else if (cond.value.status === 'exclude') filterData.status__exclude = form.value.status
    }

    enabledFields.value.forEach(key => {
      if (key === 'status') return

      const operator = cond.value[key]
      const val = form.value[key]

      if (key === 'project') {
        if (selectedProjectVal.value === '') {
          if (operator === 'is') filterData.my_project = true
          else if (operator === 'exclude') filterData.my_project = false
        } else if (selectedProjectVal.value === 'bookmark') {
          delete filterData.status
          delete filterData.status__exclude
          if (operator === 'is') filterData.bookmark = true
          else if (operator === 'exclude') filterData.bookmark = false
        } else if (selectedProjectVal.value === 'closed') {
          delete filterData.status
          delete filterData.status__exclude
          if (operator === 'is') filterData.status = '2'
          else if (operator === 'exclude') filterData.status__exclude = '2'
        } else {
          delete filterData.status
          delete filterData.status__exclude
          const selectedProj = allReadableProjects.find(
            p => p.value === Number(selectedProjectVal.value),
          )
          const projectVal = selectedProj ? selectedProj.slug : String(selectedProjectVal.value)
          if (operator === 'is') filterData.project = projectVal
          else if (operator === 'exclude') filterData.project__exclude = projectVal
        }
      } else if (key === 'parent') {
        if (operator === 'all') {
          filterData.parent__isnull = false
        } else if (operator === 'none') {
          filterData.parent__isnull = true
        } else if (operator === 'is') {
          const selectedParent = allReadableProjects.find(
            p => p.value === Number(selectedParentVal.value),
          )
          filterData.parent = selectedParent ? selectedParent.slug : String(selectedParentVal.value)
        } else if (operator === 'exclude') {
          const selectedParent = allReadableProjects.find(
            p => p.value === Number(selectedParentVal.value),
          )
          filterData.parent__exclude = selectedParent
            ? selectedParent.slug
            : String(selectedParentVal.value)
        }
      } else if (key === 'is_public') {
        if (operator === 'is') filterData.is_public = form.value.is_public
        else if (operator === 'exclude') filterData.is_public__exclude = form.value.is_public
      } else if (key === 'name' || key === 'description') {
        if (operator === 'none') {
          filterData[`${key}__isnull`] = true
        } else if (operator === 'any') {
          filterData[`${key}__isnull`] = false
        } else if (val) {
          if (operator === 'contains') filterData[key] = val
          else if (operator === 'exclude') filterData[`${key}__exclude`] = val
          else if (operator === 'startswith') filterData[`${key}__startswith`] = val
          else if (operator === 'endswith') filterData[`${key}__endswith`] = val
        }
      } else if (key === 'created' || key === 'updated') {
        const fieldPrefix = key === 'created' ? 'created' : 'updated'
        const minVal = form.value[`${fieldPrefix}_date`]
        const maxVal = form.value[`${fieldPrefix}_date2`]
        const targetFrom = key === 'created' ? 'from_created' : 'from_updated'
        const targetTo = key === 'created' ? 'to_created' : 'to_updated'

        if (operator === 'is' && minVal) {
          filterData[targetFrom] = minVal
          filterData[targetTo] = minVal
        } else if (operator === 'gte' && minVal) {
          filterData[targetFrom] = minVal
        } else if (operator === 'lte' && minVal) {
          filterData[targetTo] = minVal
        } else if (operator === 'between' && minVal && maxVal) {
          filterData[targetFrom] = minVal
          filterData[targetTo] = maxVal
        }
      }
    })

    if (form.value.bookmark !== undefined) filterData.bookmark = form.value.bookmark
    if (form.value.my_project !== undefined) filterData.my_project = form.value.my_project

    return filterData
  }

  // 6. 초기화
  const resetFilter = (allReadableProjects: selectProject[] = []) => {
    searchCond.value = ['status']
    enabledFields.value = ['status']
    cond.value = { ...defaultCond }
    form.value = { ...defaultForm }
    selectedProjectVal.value = ''
    if (allReadableProjects.length) {
      selectedParentVal.value = allReadableProjects[0]?.value
    }
    return buildFilterPayload(allReadableProjects)
  }

  // 7. 저장된 쿼리 복원
  const applySavedQuery = (query: any, allReadableProjects: selectProject[] = []) => {
    if (!query || !query.filters) return null

    const f = query.filters
    searchCond.value = ['status']
    enabledFields.value = ['status']
    cond.value = { ...defaultCond }
    form.value = { ...defaultForm }
    selectedProjectVal.value = ''
    if (allReadableProjects.length) {
      selectedParentVal.value = allReadableProjects[0]?.value
    }

    if (f.searchCond) {
      searchCond.value = [...f.searchCond]
      enabledFields.value = [...f.searchCond]
    }
    if (f.cond) cond.value = { ...cond.value, ...f.cond }
    if (f.form) {
      form.value = { ...form.value, ...f.form }
      if (f.form.project !== undefined) selectedProjectVal.value = f.form.project
      if (f.form.parent !== undefined) selectedParentVal.value = f.form.parent
    } else {
      if (f.bookmark !== undefined) {
        form.value.bookmark = f.bookmark
        if (f.bookmark) {
          if (!searchCond.value.includes('project')) searchCond.value.push('project')
          if (!enabledFields.value.includes('project')) enabledFields.value.push('project')
          cond.value.project = 'is'
          selectedProjectVal.value = 'bookmark'
        }
      }
      if (f.my_project !== undefined) {
        form.value.my_project = f.my_project
        if (f.my_project) {
          if (!searchCond.value.includes('project')) searchCond.value.push('project')
          if (!enabledFields.value.includes('project')) enabledFields.value.push('project')
          cond.value.project = 'is'
          selectedProjectVal.value = ''
        }
      }
    }

    return buildFilterPayload(allReadableProjects)
  }

  return {
    searchCond,
    enabledFields,
    cond,
    form,
    selectedProjectVal,
    selectedParentVal,
    buildFilterPayload,
    resetFilter,
    applySavedQuery,
  }
})
