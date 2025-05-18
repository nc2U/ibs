<script lang="ts" setup>
import { ref } from 'vue'
import { btnSecondary } from '@/utils/cssMixins.ts'

defineProps({
  headCommit: { type: Number, required: true },
  baseCommit: { type: Number, required: true },
})

const emit = defineEmits(['get-back'])

const viewSort = ref<'1' | '2'>('1')

const getBack = () => emit('get-back')
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>리비전 {{ headCommit }} : {{ baseCommit }}</h5>
    </CCol>
  </CRow>

  <CRow>
    <CCol>
      차이접 보기 :
      <CFormCheck
        type="radio"
        name="viewChoice"
        id="c1"
        label="두줄로"
        value="1"
        inline
        v-model="viewSort"
      />
      <CFormCheck
        type="radio"
        name="viewChoice"
        id="c2"
        label="한줄로"
        value="2"
        inline
        v-model="viewSort"
      />
    </CCol>
  </CRow>

  <CRow>
    <CCol>
      <CTable>
        <colgroup>
          <col style="width: 2%" />
          <col v-if="viewSort === '2'" style="width: 48%" />
          <col style="width: 2%" />
          <col :style="{ width: viewSort === '1' ? 96 : 48 + '%' }" />
        </colgroup>
        <CTableHead>
          <CTableRow>
            <CTableHeaderCell :colspan="viewSort === '1' ? 3 : 4">
              {{ 'a' }}
            </CTableHeaderCell>
          </CTableRow>
        </CTableHead>
        <CTableBody>
          <CTableRow>
            <CTableDataCell>{{ headCommit }}</CTableDataCell>
            <CTableDataCell v-if="viewSort === '2'">asdf</CTableDataCell>
            <CTableDataCell>{{ baseCommit }}</CTableDataCell>
            <CTableDataCell>asdf</CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>
    </CCol>
  </CRow>

  <CRow class="mt-3">
    <CCol>
      <v-btn size="small" variant="outlined" :color="btnSecondary" @click="getBack">돌아가기</v-btn>
    </CCol>
  </CRow>
</template>
