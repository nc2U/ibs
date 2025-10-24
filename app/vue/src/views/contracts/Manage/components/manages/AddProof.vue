<script lang="ts" setup>
import { computed, ref } from 'vue'
import { numFormat } from '@/utils/baseMixins.ts'
import { useContract } from '@/store/pinia/contract.ts'

const formNumber = ref(1000)

const contStore = useContract()
const requiredDocsList = computed(() => contStore.requiredDocsList)
</script>

<template>
  <CCard class="mb-3">
    <CCardHeader>
      <strong>구비서류 제출 현황</strong>
    </CCardHeader>
    <CCardBody>
      <CTable hover responsive>
        <colgroup>
          <col style="width: 23%" />
          <col style="width: 10%" />
          <col style="width: 18%" />
          <col style="width: 20%" />
          <col style="width: 10%" />
          <col style="width: 10%" />
        </colgroup>
        <CTableHead>
          <CTableRow class="text-center">
            <CTableHeaderCell>해당서류</CTableHeaderCell>
            <CTableHeaderCell>필요수량</CTableHeaderCell>
            <CTableHeaderCell>필수여부</CTableHeaderCell>
            <CTableHeaderCell>제출수량</CTableHeaderCell>
            <CTableHeaderCell>파일</CTableHeaderCell>
            <CTableHeaderCell>관리</CTableHeaderCell>
          </CTableRow>
        </CTableHead>
        <CTableBody>
          <CTableRow v-for="(doc, i) in requiredDocsList" :key="doc.pk">
            <CTableDataCell>
              {{ doc.document_name }}
              <v-tooltip>{{ doc.description }}</v-tooltip>
            </CTableDataCell>
            <CTableDataCell class="text-center">{{ doc.quantity }}</CTableDataCell>
            <CTableDataCell>{{ doc.required }}</CTableDataCell>
            <CTableDataCell class="text-end" color="info" @dblclick="formNumber = i">
              <span v-if="formNumber !== i">{{ numFormat(1) }}</span>
              <CFormInput
                v-else
                type="number"
                min="0"
                :value="1"
                size="sm"
                style="width: 90px; margin-left: auto; display: block"
                @blur="formNumber = 1000"
                @keydown.enter="formNumber = 1000"
              />
            </CTableDataCell>
            <CTableDataCell class="text-center">
              <v-icon
                v-if="1 == 1"
                icon="mdi-download-box"
                color="primary"
                size="18"
                class="pointer"
              />
              <v-icon
                v-else
                icon="mdi-download-box-outline"
                color="grey"
                size="18"
                class="pointer"
              />
            </CTableDataCell>
            <CTableDataCell class="text-center">
              <v-icon icon="mdi-pencil" color="warning" size="16" class="pointer" />
              <v-icon icon="mdi-trash-can" color="grey" size="16" class="pointer" />
            </CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>
    </CCardBody>
  </CCard>
</template>
