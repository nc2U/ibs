<script lang="ts" setup>
import { computed } from 'vue'
import { useProjectData } from '@/store/pinia/project_data'
import { useContract } from '@/store/pinia/contract'
import { numFormat } from '@/utils/baseMixins'
import { TableSecondary, TableSuccess, TablePrimary } from '@/utils/cssMixins'

const pDataStore = useProjectData()
const simpleTypes = computed(() => pDataStore.simpleTypes)
const unitSum = computed(() => pDataStore.unitSummary)
const allUnitSum = computed(() => pDataStore.allUnitSummary)

const contStore = useContract()
const contSum = computed(() => contStore.contSum || 0)
const subsSum = computed(() => contStore.subsSum || 0)

const totalUnits = computed(() => unitSum.value?.totalNum || 0)
const totalHolding = computed(() => unitSum.value?.holdNum || 0)
const sumTotal = computed(() => subsSum.value + contSum.value)
const assignedNum = computed(
  () => (allUnitSum.value?.contNum || 0) + (allUnitSum.value?.appNum || 0),
)
const unassignedNum = computed(() => sumTotal.value - assignedNum.value)
const remainingNum = computed(() => totalUnits.value - totalHolding.value - sumTotal.value)
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
            <CTableDataCell class="text-end" colspan="3">
              {{ numFormat(totalUnits) }}
            </CTableDataCell>
          </CTableRow>

          <CTableRow>
            <CTableHeaderCell :color="TableSuccess">청약세대</CTableHeaderCell>
            <CTableDataCell class="text-end">
              {{ numFormat(subsSum) }}
            </CTableDataCell>
            <CTableHeaderCell :color="TablePrimary">계약세대</CTableHeaderCell>
            <CTableDataCell class="text-end">
              {{ numFormat(contSum) }}
            </CTableDataCell>
          </CTableRow>

          <CTableRow>
            <CTableHeaderCell :color="TableSecondary"> 동호미배정 세대 </CTableHeaderCell>
            <CTableDataCell class="text-end">
              {{ numFormat(unassignedNum) }}
            </CTableDataCell>
            <CTableHeaderCell :color="TableSecondary"> 홀딩세대 </CTableHeaderCell>
            <CTableDataCell class="text-end">
              {{ numFormat(totalHolding) }}
            </CTableDataCell>
          </CTableRow>

          <CTableRow>
            <CTableHeaderCell :color="TableSecondary">합계</CTableHeaderCell>
            <CTableDataCell class="text-end">
              {{ numFormat(sumTotal) }}
            </CTableDataCell>
            <CTableHeaderCell :color="TableSecondary"> 잔여세대 </CTableHeaderCell>
            <CTableDataCell class="text-end">
              {{ numFormat(remainingNum) }}
            </CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>
    </CCol>
    <CCol lg="7">
      <span v-for="type in simpleTypes" :key="type.pk" class="me-3">
        <v-icon icon="mdi-square" size="small" :color="type.color" />
        {{ type.name }}
      </span>
    </CCol>
  </CRow>
</template>
