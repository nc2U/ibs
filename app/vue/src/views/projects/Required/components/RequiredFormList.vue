<script lang="ts" setup>
import { computed } from 'vue'
import { write_project } from '@/utils/pageAuth'
import { TableSecondary } from '@/utils/cssMixins'
import { useContract } from '@/store/pinia/contract.ts'
import Required from './Required.vue'

const emit = defineEmits(['on-update', 'on-delete'])

const contStore = useContract()
const requiredDocsList = computed(() => contStore.requiredDocsList)
</script>

<template>
  <CTable hover responsive>
    <colgroup>
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col v-if="write_project" style="width: 10%" />
    </colgroup>
    <CTableHead :color="TableSecondary" class="text-center">
      <CTableRow>
        <CTableHeaderCell>서류구분</CTableHeaderCell>
        <CTableHeaderCell>서류 유형</CTableHeaderCell>
        <CTableHeaderCell>필요 수량</CTableHeaderCell>
        <CTableHeaderCell>필수 여부</CTableHeaderCell>
        <CTableHeaderCell>설명</CTableHeaderCell>
        <CTableHeaderCell>표시 순서</CTableHeaderCell>
        <CTableHeaderCell v-if="write_project">비고</CTableHeaderCell>
      </CTableRow>
    </CTableHead>
    <CTableBody v-if="requiredDocsList.length > 0">
      <Required
        v-for="doc in requiredDocsList"
        :key="doc.pk"
        :required-doc="doc"
        @on-update="emit('on-update', $event)"
        @on-delete="emit('on-delete', $event)"
      />
    </CTableBody>

    <CTableBody v-else>
      <CTableRow>
        <CTableDataCell :colspan="write_project ? 7 : 6" class="text-center p-5 text-danger">
          등록된 데이터가 없습니다.
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
