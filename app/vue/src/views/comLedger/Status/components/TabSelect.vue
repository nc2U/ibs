<script lang="ts" setup>
import { ref, watch } from 'vue'

const tabPanePillsActiveKey = ref(Number(localStorage.getItem('comLedgerStatus')) || 1)

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
    <CCol md="8" lg="6" xl="4">
      <CNav variant="pills" layout="justified">
        <CNavItem>
          <CNavLink
            href="#"
            :active="tabPanePillsActiveKey === 1"
            @click.prevent="showTab(1)"
          >
            계좌별 자금현황
          </CNavLink>
        </CNavItem>
        <CNavItem>
          <CNavLink
            href="#"
            :active="tabPanePillsActiveKey === 2"
            @click.prevent="showTab(2)"
          >
            당일 입출금내역
          </CNavLink>
        </CNavItem>
      </CNav>
    </CCol>
  </CRow>
</template>
