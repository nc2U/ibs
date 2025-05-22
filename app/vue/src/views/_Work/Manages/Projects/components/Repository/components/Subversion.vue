<script lang="ts" setup>
import { ref } from 'vue'
import { elapsedTime } from '@/utils/baseMixins.ts'

defineProps({
  branches: { type: Array, default: () => [] },
  tags: { type: Array, default: () => [] },
  trunk: { type: Object, default: () => null },
})

const branchFold = ref(false)
const tagFold = ref(false)
const trunkFold = ref(false)
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>
        <span><router-link to="">SVN</router-link></span>
        <!--        <span v-if="1 == 2">/ <router-link to="">branches</router-link></span>-->
        <!--        <span v-if="1 == 2">/ <router-link to="">aaa</router-link></span>-->
      </h5>
    </CCol>
  </CRow>
  {{ trunk }}
  <CRow class="mb-5">
    <CCol>
      <CTable hover striped small responsive>
        <colgroup>
          <col style="width: 25%" />
          <col style="width: 6%" />
          <col style="width: 6%" />
          <col style="width: 14%" />
          <col style="width: 14%" />
          <col style="width: 35%" />
        </colgroup>
        <CTableHead>
          <CTableRow class="text-center">
            <CTableHeaderCell>이름</CTableHeaderCell>
            <CTableHeaderCell>크기</CTableHeaderCell>
            <CTableHeaderCell>리비전</CTableHeaderCell>
            <CTableHeaderCell>마지막 수정일</CTableHeaderCell>
            <CTableHeaderCell>저자</CTableHeaderCell>
            <CTableHeaderCell>설명</CTableHeaderCell>
          </CTableRow>
        </CTableHead>
        <CTableBody>
          <CTableRow>
            <CTableDataCell>
              <v-icon
                :icon="`mdi-chevron-${branchFold ? 'down' : 'right'}`"
                size="16"
                class="pointer mr-1"
                @click="branchFold = !branchFold"
              />
              <v-icon icon="mdi-folder" color="#EFD2A8" size="16" class="pointer mr-1" />
              <router-link to="">branches</router-link>
            </CTableDataCell>
            <CTableDataCell class="text-right"></CTableDataCell>
            <CTableDataCell class="text-center">
              <router-link to="">10123</router-link>
            </CTableDataCell>
            <CTableDataCell class="text-right">6일</CTableDataCell>
            <CTableDataCell class="text-center">Austin Kho</CTableDataCell>
            <CTableDataCell> #127 fetch_commits.py update</CTableDataCell>
          </CTableRow>
          <CTableRow v-if="branchFold" v-for="branch in branches as any[]" :key="branch">
            <CTableDataCell class="pl-5">
              <v-icon icon="mdi-chevron-right" size="16" class="pointer mr-1" />
              {{ branch.name }}
            </CTableDataCell>
            <CTableDataCell></CTableDataCell>
            <CTableDataCell></CTableDataCell>
            <CTableDataCell></CTableDataCell>
            <CTableDataCell></CTableDataCell>
            <CTableDataCell></CTableDataCell>
          </CTableRow>
          <CTableRow>
            <CTableDataCell>
              <v-icon
                :icon="`mdi-chevron-${tagFold ? 'down' : 'right'}`"
                size="16"
                class="pointer mr-1"
                @click="tagFold = !tagFold"
              />
              <v-icon icon="mdi-folder" color="#EFD2A8" size="16" class="pointer mr-1" />
              <router-link to="">tags</router-link>
            </CTableDataCell>
            <CTableDataCell class="text-right"></CTableDataCell>
            <CTableDataCell class="text-center">
              <router-link to="">10124</router-link>
            </CTableDataCell>
            <CTableDataCell class="text-right">약 한달</CTableDataCell>
            <CTableDataCell class="text-center">Austin Kho</CTableDataCell>
            <CTableDataCell> #127 view diff update</CTableDataCell>
          </CTableRow>
          <CTableRow v-if="tagFold" v-for="(tag, i) in tags" :key="i">
            <CTableDataCell class="pl-5">{{ tag.name }}</CTableDataCell>
            <CTableDataCell></CTableDataCell>
            <CTableDataCell></CTableDataCell>
            <CTableDataCell></CTableDataCell>
            <CTableDataCell></CTableDataCell>
            <CTableDataCell></CTableDataCell>
          </CTableRow>
          <CTableRow>
            <CTableDataCell>
              <v-icon
                :icon="`mdi-chevron-${trunkFold ? 'down' : 'right'}`"
                size="16"
                class="pointer mr-1"
                @click="trunkFold = !trunkFold"
              />
              <v-icon icon="mdi-folder" color="#EFD2A8" size="16" class="pointer mr-1" />
              <router-link to="">trunk</router-link>
            </CTableDataCell>
            <CTableDataCell class="text-right"></CTableDataCell>
            <CTableDataCell class="text-center">
              <router-link to="">10125</router-link>
            </CTableDataCell>
            <CTableDataCell class="text-right">4일</CTableDataCell>
            <CTableDataCell class="text-center">Austin Kho</CTableDataCell>
            <CTableDataCell> package update</CTableDataCell>
          </CTableRow>
          <CTableRow v-if="trunkFold" v-for="i in 5" :key="i">
            <CTableDataCell class="pl-5">trunk {{ i }}</CTableDataCell>
            <CTableDataCell></CTableDataCell>
            <CTableDataCell></CTableDataCell>
            <CTableDataCell></CTableDataCell>
            <CTableDataCell></CTableDataCell>
            <CTableDataCell></CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>
    </CCol>
  </CRow>
</template>
