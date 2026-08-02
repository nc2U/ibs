<script lang="ts" setup>
import { computed } from 'vue'
import { useProjectData } from '@/store/pinia/project_data'
import { TableSecondary } from '@/utils/cssMixins'
import { usePerms } from '@/composables/usePerms.ts'
import { type UnitType } from '@/store/types/project'
import Type from '@/views/projects/Type/components/Type.vue'

const emit = defineEmits(['on-update', 'on-delete'])

const { can, PERM } = usePerms()
const canProjectUpdate = computed(() => can(PERM.PROJECT_UPDATE))

const projectDataStore = useProjectData()
const unitTypeList = computed(() => projectDataStore.unitTypeList)

const onUpdateType = (payload: UnitType) => emit('on-update', payload)
const onDeleteType = (pk: number) => emit('on-delete', pk)
</script>

<template>
  <CTable hover responsive>
    <colgroup>
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col style="width: 5%" />
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col v-if="canProjectUpdate" style="width: 10%" />
    </colgroup>
    <CTableHead :color="TableSecondary" class="text-center">
      <CTableRow>
        <CTableHeaderCell>타입종류</CTableHeaderCell>
        <CTableHeaderCell>타입구분</CTableHeaderCell>
        <CTableHeaderCell>타입명칭</CTableHeaderCell>
        <CTableHeaderCell>타입색상</CTableHeaderCell>
        <CTableHeaderCell>전용면적(m<sup>2</sup>)</CTableHeaderCell>
        <CTableHeaderCell>공급면적(m<sup>2</sup>)</CTableHeaderCell>
        <CTableHeaderCell>계약면적(m<sup>2</sup>)</CTableHeaderCell>
        <CTableHeaderCell>평균가격</CTableHeaderCell>
        <CTableHeaderCell>공급가 설정 옵션</CTableHeaderCell>
        <CTableHeaderCell>세대수</CTableHeaderCell>
        <CTableHeaderCell v-if="canProjectUpdate">비 고</CTableHeaderCell>
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
        <CTableDataCell :colspan="canProjectUpdate ? 11 : 10" class="text-center p-5 text-danger">
          등록된 데이터가 없습니다.
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
