<script lang="ts" setup>
import { computed } from 'vue'
import { TableSecondary } from '@/utils/cssMixins'
import { useContract } from '@/store/pinia/contract'
import { usePerms } from '@/composables/usePerms'
import Required from './Required.vue'

const { can, PERM } = usePerms()
const canProjectUpdate = computed(() => can(PERM.PROJECT_UPDATE))

const contStore = useContract()
const requiredDocsList = computed(() => contStore.requiredDocsList)
</script>

<template>
  <CTable hover responsive>
    <colgroup v-if="canProjectUpdate">
      <col style="width: 12%" />
      <col style="width: 18%" />
      <col style="width: 10%" />
      <col style="width: 14%" />
      <col style="width: 26%" />
      <col style="width: 8%" />
      <col style="width: 12%" />
    </colgroup>
    <colgroup v-else>
      <col style="width: 14%" />
      <col style="width: 20%" />
      <col style="width: 12%" />
      <col style="width: 14%" />
      <col style="width: 30%" />
      <col style="width: 10%" />
    </colgroup>
    <CTableHead :color="TableSecondary" class="text-center">
      <CTableRow>
        <CTableHeaderCell>서류구분</CTableHeaderCell>
        <CTableHeaderCell>서류 유형</CTableHeaderCell>
        <CTableHeaderCell>필요 수량</CTableHeaderCell>
        <CTableHeaderCell>필수 여부</CTableHeaderCell>
        <CTableHeaderCell>설명</CTableHeaderCell>
        <CTableHeaderCell>표시 순서</CTableHeaderCell>
        <CTableHeaderCell v-if="canProjectUpdate">비고</CTableHeaderCell>
      </CTableRow>
    </CTableHead>
    <CTableBody v-if="requiredDocsList.length > 0">
      <Required v-for="doc in requiredDocsList" :key="doc.pk" :required-doc="doc" />
    </CTableBody>

    <CTableBody v-else>
      <CTableRow>
        <CTableDataCell :colspan="canProjectUpdate ? 7 : 6" class="text-center p-5 text-danger">
          등록된 데이터가 없습니다.
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
