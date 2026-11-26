<script lang="ts" setup>
import { ref, computed } from 'vue'
import { useComLedger } from '@/store/pinia/comLedger.ts'
import { TableSecondary } from '@/utils/cssMixins'
import AlertModal from '@/components/Modals/AlertModal.vue'

const refDAccount = ref()

const sort = ref<'both' | 'deposit' | 'withdraw'>('both')
const searchQuery = ref('')

const ledgerStore = useComLedger()
const comAccountList = computed(() => ledgerStore.comAccountList)

const computedAccounts = computed(() => {
  if (sort.value === 'both') return comAccountList.value
  return comAccountList.value.filter(
    acc => acc.computed_direction === sort.value || acc.computed_direction === 'both',
  )
})

const searchedAccounts = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return null
  return comAccountList.value
    .filter(acc => acc.depth > 1)
    .filter(
      acc =>
        acc.name.toLowerCase().includes(q) ||
        (acc.description ?? '').toLowerCase().includes(q) ||
        acc.code.toLowerCase().includes(q),
    )
})

const callModal = () => refDAccount.value?.callModal()

defineExpose({ callModal })
</script>

<template>
  <AlertModal ref="refDAccount" size="xl">
    <template #header> 계정 보기</template>
    <template #default>
      <div class="d-flex align-center gap-3 mb-3">
        <v-btn-toggle v-model="sort" mandatory density="compact" variant="tonal">
          <v-btn value="both">전체</v-btn>
          <v-btn value="deposit">입금</v-btn>
          <v-btn value="withdraw">출금</v-btn>
        </v-btn-toggle>
        <v-text-field
          v-model="searchQuery"
          density="compact"
          placeholder="계정 검색..."
          prepend-inner-icon="mdi-magnify"
          clearable
          hide-details
          style="max-width: 300px"
        />
      </div>
      <CTable v-if="!searchQuery" small bordered>
        <colgroup>
          <col style="width: 15%" />
          <col style="width: 60%" />
          <col style="width: 25%" />
        </colgroup>

        <CTableHead :color="TableSecondary">
          <CTableRow>
            <CTableHeaderCell class="ps-2">1차</CTableHeaderCell>
            <CTableHeaderCell class="ps-2">2차</CTableHeaderCell>
            <CTableHeaderCell class="ps-2">3차</CTableHeaderCell>
          </CTableRow>
        </CTableHead>

        <CTableBody>
          <CTableRow v-for="acc in computedAccounts" :key="acc.pk">
            <CTableDataCell class="ps-2">
              <span v-if="acc.depth === 1">
                {{ acc.name }}
                <span v-if="acc.description" class="text-muted">({{ acc.description }})</span>
              </span>
            </CTableDataCell>
            <CTableDataCell class="ps-2">
              <span v-if="acc.depth === 2">
                {{ acc.name }}
                <span v-if="acc.description" class="text-muted">({{ acc.description }})</span>
              </span>
            </CTableDataCell>
            <CTableDataCell class="ps-2">
              <span
                v-if="acc.depth >= 3"
                :style="acc.depth > 3 ? { paddingLeft: `${(acc.depth - 3) * 16}px` } : undefined"
              >
                <span v-if="acc.depth > 3" class="text-muted me-1">└</span>{{ acc.name }}
                <span v-if="acc.description" class="text-muted">({{ acc.description }})</span>
              </span>
            </CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>

      <div v-else style="min-height: 240px">
        <v-divider class="my-4" />
        <CRow v-for="acc in searchedAccounts" :key="acc.pk" class="ps-3 my-3">
          <CCol>
            {{ acc.full_path }}
            <span v-if="acc.description" class="text-muted ms-3">({{ acc.description }})</span>
          </CCol>
        </CRow>
        <div v-if="!searchedAccounts?.length" class="text-center text-muted py-4">
          검색 결과가 없습니다.
        </div>
      </div>
    </template>
    <template #footer></template>
  </AlertModal>
</template>
