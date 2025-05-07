<script lang="ts" setup>
import { computed } from 'vue'
import { write_project } from '@/utils/pageAuth'
import { useProjectData } from '@/store/pinia/project_data'
import { type UnitType } from '@/store/types/project'
import { TableSecondary } from '@/utils/cssMixins'
import Type from '@/views/projects/Type/components/Type.vue'

const emit = defineEmits(['on-update', 'on-delete'])

const projectDataStore = useProjectData()
const unitTypeList = computed(() => projectDataStore.unitTypeList)

const onUpdateType = (payload: UnitType) => emit('on-update', payload)
const onDeleteType = (pk: number) => emit('on-delete', pk)
</script>

<template>
  <CTable hover responsive>
    <colgroup>
      <col style="width: 11%" />
      <col style="width: 11%" />
      <col style="width: 9%" />
      <col style="width: 12%" />
      <col style="width: 12%" />
      <col style="width: 12%" />
      <col style="width: 13%" />
      <col style="width: 10%" />
      <col v-if="write_project" style="width: 10%" />
    </colgroup>
    <CTableHead :color="TableSecondary" class="text-center">
      <CTableRow>
        <CTableHeaderCell>타입종류</CTableHeaderCell>
        <CTableHeaderCell>타입명칭</CTableHeaderCell>
        <CTableHeaderCell>타입색상</CTableHeaderCell>
        <CTableHeaderCell>전용면적(m<sup>2</sup>)</CTableHeaderCell>
        <CTableHeaderCell>공급면적(m<sup>2</sup>)</CTableHeaderCell>
        <CTableHeaderCell>계약면적(m<sup>2</sup>)</CTableHeaderCell>
        <CTableHeaderCell>평균가격</CTableHeaderCell>
        <CTableHeaderCell>세대수</CTableHeaderCell>
        <CTableHeaderCell v-if="write_project">비 고</CTableHeaderCell>
      </CTableRow>
    </CTableHead>
    <CTableBody v-if="unitTypeList.length > 0">
      <Type
        v-for="type in unitTypeList"
        :key="type.pk"
        :type="type"
        @on-update="onUpdateType"
        @on-delete="onDeleteType"
      />
    </CTableBody>

    <CTableBody v-else>
      <CTableRow>
        <CTableDataCell :colspan="write_project ? 9 : 8" class="text-center p-5 text-danger">
          등록된 데이터가 없습니다.
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
