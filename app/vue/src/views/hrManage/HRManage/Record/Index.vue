<script lang="ts" setup>
import { computed, onBeforeMount, ref } from 'vue'
import { pageTitle, navMenu1, navMenu2 } from '@/views/hrManage/_menu/headermixin2.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { useAccount } from '@/store/pinia/account.ts'
import ComHrAuthGuard from '@/components/AuthGuard/ComHrAuthGuard.vue'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'

const accStore = useAccount()
const isHrManager = computed(() => accStore.isHrManager)

const navMenu = computed(() => (!isHrManager.value ? navMenu1 : navMenu2))

const comStore = useCompany()

const comSelect = (target: number | null) => {
  comStore.dutyList = []
  // if (!!target) fetchDutyList({ com: target })
}

const loading = ref(true)
onBeforeMount(() => {
  loading.value = false
})
</script>

<template>
  <ComHrAuthGuard>
    <Loading v-model:active="loading" />
    <ContentHeader
      :page-title="pageTitle"
      :nav-menu="navMenu"
      selector="CompanySelect"
      @com-select="comSelect"
    />

    <ContentBody>
      <CCardBody>
        <h3>인사 기록</h3>

        <h6>준비중..</h6>
      </CCardBody>
    </ContentBody>
  </ComHrAuthGuard>
</template>
