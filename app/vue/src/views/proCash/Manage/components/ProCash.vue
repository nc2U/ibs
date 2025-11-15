<script lang="ts" setup>
import { ref, computed, type PropType } from 'vue'
import { useStore } from '@/store'
import { useAccount } from '@/store/pinia/account'
import { useProCash } from '@/store/pinia/proCash'
import { write_project_cash } from '@/utils/pageAuth'
import { numFormat, cutString, diffDate } from '@/utils/baseMixins'
import { type ProBankAcc, type ProjectCashBook } from '@/store/types/proCash'
import FormModal from '@/components/Modals/FormModal.vue'
import ProCashForm from '@/views/proCash/Manage/components/ProCashForm.vue'
import Pagination from '@/components/Pagination'
import { CTableDataCell, CTableRow } from '@coreui/vue'

const props = defineProps({
  proCash: { type: Object as PropType<ProjectCashBook>, required: true },
  calculated: { type: String, default: '2000-01-01' },
  isHighlighted: { type: Boolean, default: false },
  hasChildren: { type: Boolean, default: false },
})

const emit = defineEmits(['multi-submit', 'on-delete', 'on-bank-create', 'on-bank-update'])

const updateFormModal = ref()
const proCashStore = useProCash()

// 자식 레코드 토글 상태
const showChildren = ref(false)
const loadingChildren = ref(false)
const childrenPage = ref(1)
const hasMoreChildren = ref(false)
const totalChildren = ref(0)

// 캐시된 자식 레코드 가져오기
const children = computed(() =>
  props.proCash.pk ? proCashStore.getCachedChildren(props.proCash.pk) : [],
)

const sortClass = computed(
  () => ['', 'text-primary', 'text-danger', 'text-info'][props.proCash?.sort || 0],
)

const store = useStore()
const dark = computed(() => store.theme === 'dark')
const rowColor = computed(() => {
  if (props.isHighlighted) return 'warning'
  const { proCash } = props
  if (proCash?.separated) return 'light'
  if (proCash?.is_separate) return 'primary'
  if (proCash?.contract && [1, 5].includes(proCash?.project_account_d3 ?? 0)) return 'info'

  return ''
})

const accountStore = useAccount()
const allowedPeriod = computed(
  () =>
    accountStore.superAuth ||
    (props.proCash?.deal_date &&
      diffDate(props.proCash.deal_date, new Date(props.calculated)) <= 10),
)

const showDetail = () => updateFormModal.value.callModal()

const multiSubmit = (payload: { formData: ProjectCashBook; sepData: ProjectCashBook | null }) =>
  emit('multi-submit', payload)

const onDelete = (payload: { project: number; pk: number }) => emit('on-delete', payload)

const onBankCreate = (payload: ProBankAcc) => emit('on-bank-create', payload)
const onBankUpdate = (payload: ProBankAcc) => emit('on-bank-update', payload)

// 자식 레코드 토글
const toggleChildren = async () => {
  if (!props.proCash.pk) return

  if (!showChildren.value) {
    // 자식 레코드 열기
    showChildren.value = true

    // 캐시에 데이터가 없으면 로드
    if (children.value.length === 0) {
      await loadChildren(1)
    }
  } else {
    // 자식 레코드 닫기
    showChildren.value = false
  }
}

// 자식 레코드 로드
const loadChildren = async (page: number = 1) => {
  if (!props.proCash.pk || loadingChildren.value) return

  try {
    loadingChildren.value = true
    const response = await proCashStore.fetchChildrenRecords(props.proCash.pk, page)

    childrenPage.value = page
    totalChildren.value = response.count
    hasMoreChildren.value = !!response.next
  } catch (error) {
    console.error('자식 레코드 로드 실패:', error)
  } finally {
    loadingChildren.value = false
  }
}

// 페이지 변경 핸들러
const onChildrenPageChange = (page: number) => {
  loadChildren(page)
}

// 총 페이지 수 계산
const childrenTotalPages = computed(() => Math.ceil(totalChildren.value / 15))
</script>

<template>
  <template v-if="proCash">
    <!-- 부모 레코드 행 -->
    <CTableRow
      class="text-center"
      :color="rowColor"
      :style="proCash.is_separate ? 'font-weight: bold;' : ''"
      :data-procash-id="proCash.pk"
    >
      <CTableDataCell>
        <!-- 자식이 있으면 토글 버튼 표시 -->
        <div class="d-flex align-items-center justify-content-center">
          <v-btn
            v-if="hasChildren"
            size="x-small"
            variant="text"
            icon
            @click="toggleChildren"
            class="mr-1"
          >
            <v-btn
              :icon="showChildren ? 'mdi-chevron-down' : 'mdi-chevron-right'"
              variant="tonal"
              size="sm"
            />
          </v-btn>
          <span>{{ proCash.deal_date }}</span>
        </div>
      </CTableDataCell>
      <CTableDataCell :class="sortClass">
        {{ proCash?.sort_desc }}
      </CTableDataCell>
      <CTableDataCell class="text-left">
        <span v-if="proCash.bank_account_desc">
          {{ cutString(proCash.bank_account_desc, 9) }}
        </span>
      </CTableDataCell>
      <CTableDataCell class="text-left">
        <span v-if="proCash.trader">
          {{ cutString(proCash.trader, 9) }}
        </span>
      </CTableDataCell>
      <CTableDataCell class="text-left">
        <span v-if="proCash.content">
          {{ cutString(proCash.content, 10) }}
        </span>
      </CTableDataCell>
      <CTableDataCell class="text-right" :color="dark ? '' : 'success'">
        {{ numFormat(proCash.income || 0) }}
      </CTableDataCell>
      <CTableDataCell class="text-right" :color="dark ? '' : 'danger'">
        {{ numFormat(proCash.outlay || 0) }}
      </CTableDataCell>
      <CTableDataCell class="text-left">
        {{ proCash.project_account_d2_desc }}
      </CTableDataCell>
      <CTableDataCell class="text-left">
        <span v-if="proCash.project_account_d3_desc">
          {{ cutString(proCash.project_account_d3_desc, 9) }}
        </span>
      </CTableDataCell>

      <CTableDataCell>{{ proCash.evidence_desc }}</CTableDataCell>
      <CTableDataCell v-if="write_project_cash">
        <v-btn color="info" size="x-small" @click="showDetail" :disabled="!allowedPeriod"
          >확인</v-btn
        >
      </CTableDataCell>
    </CTableRow>

    <!-- 자식 레코드 표시 영역 -->
    <CTableRow v-if="showChildren && hasChildren">
      <CTableDataCell :colspan="write_project_cash ? 11 : 10" class="p-0">
        <div class="p-0">
          <!-- 로딩 중 -->
          <div v-if="loadingChildren && children.length === 0" class="text-center py-3">
            <v-progress-circular indeterminate color="primary" size="24"></v-progress-circular>
            <span class="ml-2">자식 레코드 로딩 중...</span>
          </div>

          <!-- 자식 레코드 테이블 -->
          <CTable v-else-if="children.length > 0" bordered small class="mb-0">
            <colgroup>
              <col style="width: 8%" />
              <col style="width: 6%" />
              <col style="width: 11%" />
              <col style="width: 11%" />
              <col style="width: 12%" />
              <col style="width: 10%" />
              <col style="width: 10%" />
              <col style="width: 7%" />
              <col style="width: 10%" />
              <col style="width: 9%" />
              <col style="width: 6%" />
            </colgroup>
            <CTableBody>
              <CTableRow v-for="child in children" :key="child.pk" class="text-center">
                <CTableDataCell>{{ child.deal_date }}</CTableDataCell>
                <CTableDataCell
                  :class="['', 'text-primary', 'text-danger', 'text-info'][child?.sort || 0]"
                >
                  {{ child?.sort_desc }}
                </CTableDataCell>
                <CTableDataCell></CTableDataCell>
                <CTableDataCell class="text-left">
                  <span>{{ cutString(child.trader, 9) }}</span>
                </CTableDataCell>
                <CTableDataCell class="text-left">
                  <span>{{ cutString(child.content, 12) }}</span>
                </CTableDataCell>
                <CTableDataCell class="text-right" :color="dark ? '' : 'success'">
                  {{ numFormat(child.income || 0) }}
                </CTableDataCell>
                <CTableDataCell class="text-right" :color="dark ? '' : 'danger'">
                  {{ numFormat(child.outlay || 0) }}
                </CTableDataCell>
                <CTableDataCell class="text-left">
                  {{ child.project_account_d2_desc }}
                </CTableDataCell>
                <CTableDataCell class="text-left">
                  <span v-if="child.project_account_d3_desc">
                    {{ cutString(child.project_account_d3_desc, 9) }}
                  </span>
                </CTableDataCell>
                <CTableDataCell>{{ child.evidence_desc }}</CTableDataCell>
              </CTableRow>
            </CTableBody>
          </CTable>

          <!-- 페이지네이션 -->
          <v-pagination
            v-if="children.length > 0 && childrenTotalPages > 1"
            v-model="childrenPage"
            :length="childrenTotalPages"
            :total-visible="7"
            density="compact"
            class="mt-4"
            @update:model-value="onChildrenPageChange"
          />

          <!-- 자식 레코드가 없을 때 -->
          <div v-if="!loadingChildren && children.length === 0" class="text-center py-3 text-muted">
            분리 항목이 없습니다.
          </div>
        </div>
      </CTableDataCell>
    </CTableRow>
  </template>

  <FormModal ref="updateFormModal" size="lg">
    <template #header>프로젝트 입출금 거래 건별 관리</template>
    <template #default>
      <ProCashForm
        :pro-cash="proCash"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
        @close="updateFormModal.close()"
        @on-bank-create="onBankCreate"
        @on-bank-update="onBankUpdate"
      />
    </template>
  </FormModal>
</template>
