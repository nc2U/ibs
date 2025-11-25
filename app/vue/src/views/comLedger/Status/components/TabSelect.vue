<script lang="ts" setup>
import Cookies from 'js-cookie'
import { ref, watch } from 'vue'

const tabPanePillsActiveKey = ref(Number(Cookies.get('comCashStatus')) || 1)

watch(tabPanePillsActiveKey, nVal => Cookies.set('comCashStatus', String(nVal)))

const emit = defineEmits(['tab-select'])

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
            href="javascript:void(0);"
            :active="tabPanePillsActiveKey === 1"
            @click="showTab(1)"
          >
            계좌별 자금현황
          </CNavLink>
        </CNavItem>
        <CNavItem>
          <CNavLink
            href="javascript:void(0);"
            :active="tabPanePillsActiveKey === 2"
            @click="showTab(2)"
          >
            당일 입출금내역
          </CNavLink>
        </CNavItem>
      </CNav>
    </CCol>
  </CRow>
</template>
