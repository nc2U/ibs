<script lang="ts" setup>
import { computed } from 'vue'
import { useProjectData } from '@/store/pinia/project_data'
import { TableSecondary } from '@/utils/cssMixins'
import { usePerms } from '@/composables/usePerms.ts'
import { type BuildingUnit } from '@/store/types/project'
import Building from '@/views/projects/Building/components/Building.vue'

const emit = defineEmits(['on-update', 'on-delete'])

const { can, PERM } = usePerms()
const canProjectUpdate = computed(() => can(PERM.PROJECT_UPDATE))

const projectDataStore = useProjectData()
const buildingList = computed(() => projectDataStore.buildingList)

const onUpdateBuilding = (payload: BuildingUnit) => emit('on-update', payload)
const onDeleteBuilding = (pk: number) => emit('on-delete', pk)
</script>

<template>
  <CTable hover responsive>
    <colgroup>
      <col style="width: 50%" />
      <col v-if="canProjectUpdate" style="width: 50%" />
    </colgroup>
    <CTableHead :color="TableSecondary" class="text-center">
      <CTableRow>
        <CTableHeaderCell>동(건물)이름</CTableHeaderCell>
        <CTableHeaderCell v-if="canProjectUpdate">비 고</CTableHeaderCell>
      </CTableRow>
    </CTableHead>
    <CTableBody v-if="buildingList.length > 0">
      <Building
        v-for="building in buildingList"
        :key="building.pk"
        :building="building"
        @on-update="onUpdateBuilding"
        @on-delete="onDeleteBuilding"
      />
    </CTableBody>

    <CTableBody v-else>
      <CTableRow>
        <CTableDataCell :colspan="canProjectUpdate ? 2 : 1" class="text-center p-5 text-danger">
          등록된 데이터가 없습니다.
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
