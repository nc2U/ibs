<script lang="ts" setup>
import { computed } from 'vue'
import { write_project } from '@/utils/pageAuth'
import { useProjectData } from '@/store/pinia/project_data'
import { type OptionItem } from '@/store/types/project'
import { TableSecondary } from '@/utils/cssMixins'
import PaidOption from '@/views/projects/PaidOption/components/PaidOption.vue'

const emit = defineEmits(['on-update', 'on-delete'])

const projectDataStore = useProjectData()
const optionItemList = computed(() => projectDataStore.optionItemList)

const onUpdateOption = (payload: OptionItem) => emit('on-update', payload)
const onDeleteOption = (pk: number) => emit('on-delete', pk)
</script>

<template>
  <CTable hover responsive>
    <colgroup>
      <col style="width: 14%" />
      <col style="width: 10%" />
      <col style="width: 14%" />
      <col style="width: 14%" />
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col v-if="write_project" style="width: 8%" />
    </colgroup>
    <CTableHead :color="TableSecondary" class="text-center">
      <CTableRow>
        <CTableHeaderCell>타입구분</CTableHeaderCell>
        <CTableHeaderCell>품목 코드</CTableHeaderCell>
        <CTableHeaderCell>품목 이름</CTableHeaderCell>
        <CTableHeaderCell>세부 옵션</CTableHeaderCell>
        <CTableHeaderCell>제조사</CTableHeaderCell>
        <CTableHeaderCell>옵션 가격</CTableHeaderCell>
        <CTableHeaderCell>계약금</CTableHeaderCell>
        <CTableHeaderCell>잔 금</CTableHeaderCell>
        <CTableHeaderCell v-if="write_project">비 고</CTableHeaderCell>
      </CTableRow>
    </CTableHead>
    <CTableBody v-if="optionItemList.length > 0">
      <PaidOption
        v-for="opt in optionItemList"
        :key="opt.pk"
        :option-item="opt"
        @on-update="onUpdateOption"
        @on-delete="onDeleteOption"
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
