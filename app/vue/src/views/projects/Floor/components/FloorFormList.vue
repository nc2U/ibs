<script lang="ts" setup>
import { computed } from 'vue'
import { useProjectData } from '@/store/pinia/project_data'
import { usePerms } from '@/composables/usePerms.ts'
import { type UnitFloorType } from '@/store/types/project'
import { TableSecondary } from '@/utils/cssMixins'
import Floor from '@/views/projects/Floor/components/Floor.vue'

const emit = defineEmits(['on-update', 'on-delete'])

const { can, PERM } = usePerms()
const canProjectUpdate = computed(() => can(PERM.PROJECT_UPDATE))

const projectData = useProjectData()
const floorTypeList = computed(() => projectData.floorTypeList)

const onUpdateFloor = (payload: UnitFloorType) => emit('on-update', payload)
const onDeleteFloor = (pk: number) => emit('on-delete', pk)
</script>

<template>
  <CTable hover responsive>
    <colgroup>
      <col style="width: 18%" />
      <col style="width: 18%" />
      <col style="width: 18%" />
      <col style="width: 18%" />
      <col style="width: 18%" />
      <col v-if="canProjectUpdate" style="width: 10%" />
    </colgroup>
    <CTableHead :color="TableSecondary" class="text-center">
      <CTableRow>
        <CTableHeaderCell>타입종류</CTableHeaderCell>
        <CTableHeaderCell>시작 층</CTableHeaderCell>
        <CTableHeaderCell>종료 층</CTableHeaderCell>
        <CTableHeaderCell>방향/위치(옵션)</CTableHeaderCell>
        <CTableHeaderCell>층별 범위 명칭</CTableHeaderCell>
        <CTableHeaderCell v-if="canProjectUpdate">비 고</CTableHeaderCell>
      </CTableRow>
    </CTableHead>
    <CTableBody v-if="floorTypeList.length > 0">
      <Floor
        v-for="floor in floorTypeList"
        :key="floor.pk"
        :floor="floor"
        @on-update="onUpdateFloor"
        @on-delete="onDeleteFloor"
      />
    </CTableBody>

    <CTableBody v-else>
      <CTableRow>
        <CTableDataCell :colspan="canProjectUpdate ? 6 : 5" class="text-center p-5 text-danger">
          등록된 데이터가 없습니다.
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
