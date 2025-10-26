<script lang="ts" setup>
import { computed } from 'vue'
import { useProjectData } from '@/store/pinia/project_data'
import { useContract } from '@/store/pinia/contract'
import { numFormat } from '@/utils/baseMixins'
import { TableSecondary, TableSuccess, TablePrimary } from '@/utils/cssMixins'

const pDataStore = useProjectData()
const simpleTypes = computed(() => pDataStore.simpleTypes)
const unitSum = computed(() => pDataStore.unitSummary)

const contStore = useContract()
const contSum = computed(() => contStore.contSum)
const subsSum = computed(() => contStore.subsSum)
</script>

<template>
  <CRow>
    <CCol lg="5">
      <CTable hover responsive bordered align="middle">
        <colgroup>
          <col style="width: 25%" />
          <col style="width: 25%" />
          <col style="width: 25%" />
          <col style="width: 25%" />
        </colgroup>
        <CTableBody>
          <CTableRow>
            <CTableHeaderCell :color="TableSecondary"> 총세대수 </CTableHeaderCell>
            <CTableDataCell class="text-right" colspan="3">
              {{ numFormat(unitSum.totalNum) }}
            </CTableDataCell>
          </CTableRow>

          <CTableRow>
            <CTableHeaderCell :color="TableSuccess">청약세대</CTableHeaderCell>
            <CTableDataCell class="text-right">
              {{ numFormat(subsSum) }}
            </CTableDataCell>
            <CTableHeaderCell :color="TablePrimary">계약세대</CTableHeaderCell>
            <CTableDataCell class="text-right">
              {{ numFormat(contSum) }}
            </CTableDataCell>
          </CTableRow>

          <CTableRow>
            <CTableHeaderCell :color="TableSecondary"> 동호미배정 세대 </CTableHeaderCell>
            <CTableDataCell class="text-right">
              {{ numFormat(subsSum + contSum - (unitSum.contNum + unitSum.appNum)) }}
            </CTableDataCell>
            <CTableHeaderCell :color="TableSecondary"> 홀딩세대 </CTableHeaderCell>
            <CTableDataCell class="text-right">
              {{ numFormat(unitSum.holdNum) }}
            </CTableDataCell>
          </CTableRow>

          <CTableRow>
            <CTableHeaderCell :color="TableSecondary">합계</CTableHeaderCell>
            <CTableDataCell class="text-right">
              {{ numFormat(subsSum + contSum) }}
            </CTableDataCell>
            <CTableHeaderCell :color="TableSecondary"> 잔여세대 </CTableHeaderCell>
            <CTableDataCell class="text-right">
              {{ numFormat(unitSum.totalNum - unitSum.holdNum - (subsSum + contSum)) }}
            </CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>
    </CCol>
    <CCol lg="7">
      <span v-for="type in simpleTypes" :key="type.pk" class="mr-3">
        <v-icon icon="mdi mdi-square" size="small" :color="type.color" />
        {{ type.name }}
      </span>
    </CCol>
  </CRow>
</template>
