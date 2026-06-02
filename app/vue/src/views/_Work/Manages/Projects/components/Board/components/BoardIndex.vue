<script lang="ts" setup>
import { type PropType } from 'vue'
import { useRoute } from 'vue-router'
import type { Board } from '@/store/types/board'

defineProps({
  boardList: { type: Array as PropType<Board[]>, default: () => [] },
})

const route = useRoute()
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>게시판</h5>
    </CCol>
  </CRow>

  <CTable hover responsive align="middle">
    <colgroup>
      <col style="width: 30%" />
      <col style="width: 40%" />
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col style="width: 10%" />
    </colgroup>
    <CTableHead>
      <CTableRow color="light" class="text-center">
        <CTableHeaderCell scope="col">게시판</CTableHeaderCell>
        <CTableHeaderCell scope="col">설명</CTableHeaderCell>
        <CTableHeaderCell scope="col">주제</CTableHeaderCell>
        <CTableHeaderCell scope="col">글</CTableHeaderCell>
        <CTableHeaderCell scope="col">최근 게시물</CTableHeaderCell>
      </CTableRow>
    </CTableHead>
    <CTableBody>
      <CTableRow v-for="brd in boardList" :key="brd.pk as number">
        <CTableDataCell class="pl-4">
          <router-link
            :to="{
              name: '(게시판) - 보기',
              params: { projId: route.params.projId, brdId: brd.pk },
            }"
            class="bold"
          >
            {{ brd.name }}
          </router-link>
        </CTableDataCell>
        <CTableDataCell>{{ brd.description }}</CTableDataCell>
        <CTableDataCell class="text-center">-</CTableDataCell>
        <CTableDataCell class="text-center">-</CTableDataCell>
        <CTableDataCell class="text-center form-text">-</CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>

<style lang="scss" scoped>
.bold {
  font-weight: bold;
}
</style>
