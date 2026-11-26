<script lang="ts" setup>
import { ref, watch } from 'vue'

const storedTab = Number(localStorage.getItem('comLedgerStatus'))
const tabPanePillsActiveKey = ref([1, 2, 3].includes(storedTab) ? storedTab : 1)

watch(tabPanePillsActiveKey, nVal => localStorage.setItem('comLedgerStatus', String(nVal)))

const emit = defineEmits<{
  (e: 'tab-select', tab: number): void
}>()

const showTab = (num: number) => {
  tabPanePillsActiveKey.value = num
  emit('tab-select', num)
}
</script>

<template>
  <CRow class="mb-3">
    <CCol md="10" lg="7" xl="5">
      <CNav variant="pills" layout="justified">
        <CNavItem>
          <CNavLink
            component="button"
            type="button"
            :active="tabPanePillsActiveKey === 1"
            @click="showTab(1)"
          >
            계좌별 자금현황
          </CNavLink>
        </CNavItem>
        <CNavItem>
          <CNavLink
            component="button"
            type="button"
            :active="tabPanePillsActiveKey === 2"
            @click="showTab(2)"
          >
            당일 입출금내역
          </CNavLink>
        </CNavItem>
        <CNavItem>
          <CNavLink
            component="button"
            type="button"
            :active="tabPanePillsActiveKey === 3"
            @click="showTab(3)"
          >
            월별 자금집계
          </CNavLink>
        </CNavItem>
      </CNav>
    </CCol>
  </CRow>
</template>
