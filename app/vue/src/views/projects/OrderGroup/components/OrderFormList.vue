<script lang="ts" setup>
import { computed } from 'vue'
import { write_project } from '@/utils/pageAuth'
import { useContract } from '@/store/pinia/contract'
import { type OrderGroup as og } from '@/store/types/contract'
import { TableSecondary } from '@/utils/cssMixins'
import OrderGroup from './OrderGroup.vue'

const emit = defineEmits(['on-update', 'on-delete'])

const contractStore = useContract()
const orderGroupList = computed(() => contractStore.orderGroupList)

const onUpdateOrder = (payload: og) => emit('on-update', payload)
const onDeleteOrder = (pk: number) => emit('on-delete', pk)
</script>

<template>
  <CTable hover responsive>
    <colgroup>
      <col style="width: 25%" />
      <col style="width: 25%" />
      <col style="width: 25%" />
      <col v-if="write_project" style="width: 25%" />
    </colgroup>
    <CTableHead :color="TableSecondary" class="text-center">
      <CTableRow>
        <CTableHeaderCell>등록차수</CTableHeaderCell>
        <CTableHeaderCell>차수구분</CTableHeaderCell>
        <CTableHeaderCell>차수그룹명</CTableHeaderCell>
        <CTableHeaderCell v-if="write_project">비 고</CTableHeaderCell>
      </CTableRow>
    </CTableHead>
    <CTableBody v-if="orderGroupList.length > 0">
      <OrderGroup
        v-for="order in orderGroupList"
        :key="order.pk"
        :order="order"
        @on-update="onUpdateOrder"
        @on-delete="onDeleteOrder"
      />
    </CTableBody>

    <CTableBody v-else>
      <CTableRow>
        <CTableDataCell :colspan="write_project ? 4 : 3" class="text-center p-5 text-danger">
          등록된 데이터가 없습니다.
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
