<script lang="ts" setup>
import { ref, computed, type PropType } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from '@/store'
import { useAccount } from '@/store/pinia/account'
import { useComCash } from '@/store/pinia/comCash'
import type { CompanyBank, BankTransaction } from '@/store/types/comLedger'
import type { Project } from '@/store/types/project'
import { write_company_cash } from '@/utils/pageAuth'
import { numFormat, cutString, diffDate } from '@/utils/baseMixins'
import FormModal from '@/components/Modals/FormModal.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'
import CashForm from '@/views/comCash/CashManage/components/CashForm.vue'

const props = defineProps({
  projects: { type: Array as PropType<Project[]>, default: () => [] },
  transaction: { type: Object as PropType<BankTransaction>, required: true },
  calculated: { type: String, default: '2000-01-01' },
  isHighlighted: { type: Boolean, default: false },
  hasChildren: { type: Boolean, default: false },
})

const emit = defineEmits([
  'multi-submit',
  'on-delete',
  'patch-d3-hide',
  'on-bank-create',
  'on-bank-update',
])

const refDelModal = ref()
const refAlertModal = ref()
const updateFormModal = ref()
const comCashStore = useComCash()

const router = useRouter()

// 선택된 거래 (부모 또는 자식)
const selectedCash = ref<BankTransaction | null>(null)

// 자식 레코드 토글 상태
const showChildren = ref(false)
const loadingChildren = ref(false)
const childrenPage = ref(1)
const hasMoreChildren = ref(false)
const totalChildren = ref(0)

// 캐시된 자식 레코드 가져오기
const children = computed(() =>
  props.transaction?.pk ? comCashStore.getCachedChildren(props.transaction.pk) : [],
)

const cls = ref(['text-primary', 'text-danger', 'text-info'])
const sortClass = computed(() => cls.value[(props.transaction?.sort as number) - 1])
const d1Class = computed(
  () => cls.value[((props.transaction?.accounting_entries[0].account_d1 as number) % 3) - 1],
)

const store = useStore()
const dark = computed(() => store.theme === 'dark')
const rowColor = computed(() => {
  let color = ''
  color = dark.value ? '' : color
  // 하이라이트가 우선순위가 가장 높음
  if (props.isHighlighted) {
    color = 'warning'
  } else {
    color = '' // props.transaction?.accounting_entries.length > 1 ? 'primary' : color
    color = '' // props.transaction?.separated ? 'secondary' : color
  }
  return color
})

const accountStore = useAccount()
const allowedPeriod = computed(
  () =>
    accountStore.superAuth ||
    (props.transaction?.deal_date &&
      diffDate(props.transaction.deal_date, new Date(props.calculated)) <= 10),
)

const showDetail = () => {
  selectedCash.value = props.transaction as BankTransaction
  updateFormModal.value.callModal()
}

const showChildDetail = (child: BankTransaction) => {
  selectedCash.value = child
  updateFormModal.value.callModal()
}

const multiSubmit = (payload: { formData: BankTransaction; sepData: BankTransaction | null }) =>
  emit('multi-submit', payload)

const deleteConfirm = () => {
  if (write_company_cash.value)
    if (allowedPeriod.value) refDelModal.value.callModal()
    else
      refAlertModal.value.callModal(
        null,
        '거래일로부터 30일이 경과한 건은 삭제할 수 없습니다. 관리자에게 문의바랍니다.',
      )
  else refAlertModal.value.callModal()
}

const deleteObject = () => {
  emit('on-delete', { company: props.transaction?.company, pk: props.transaction?.pk })
  refDelModal.value.close()
}

const patchD3Hide = (payload: { pk: number; is_hide: boolean }) => emit('patch-d3-hide', payload)

const onBankCreate = (payload: CompanyBank) => emit('on-bank-create', payload)
const onBankUpdate = (payload: CompanyBank) => emit('on-bank-update', payload)

// 자식 레코드 토글
const toggleChildren = async () => {
  if (!props.transaction?.pk) return

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
  if (!props.transaction?.pk || loadingChildren.value) return

  try {
    loadingChildren.value = true
    const response = await comCashStore.fetchChildrenRecords(props.transaction.pk, page)

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
  <template v-if="transaction">
    <!-- 부모 레코드 행 -->
    <CTableRow
      class="text-center"
      :color="rowColor"
      :style="transaction.accounting_entries.length > 1 ? 'font-weight: bold;' : ''"
      :data-cash-id="transaction.pk"
    >
      <CTableDataCell>
        <!--        &lt;!&ndash; 자식이 있으면 토글 버튼 표시 &ndash;&gt;-->
        <!--        <div class="d-flex align-items-center justify-content-center">-->
        <!--          <v-btn-->
        <!--            v-if="hasChildren"-->
        <!--            size="x-small"-->
        <!--            variant="text"-->
        <!--            icon-->
        <!--            @click="toggleChildren"-->
        <!--            class="mr-1"-->
        <!--          >-->
        <!--            <v-btn-->
        <!--              :icon="showChildren ? 'mdi-chevron-down' : 'mdi-chevron-right'"-->
        <!--              variant="tonal"-->
        <!--              size="sm"-->
        <!--            />-->
        <!--          </v-btn>-->
        <span class="text-primary">{{ transaction.deal_date }}</span>
        <!--        </div>-->
      </CTableDataCell>
      <CTableDataCell class="text-left">
        {{ transaction.note }}
      </CTableDataCell>
      <CTableDataCell class="text-left">
        <span v-if="transaction.bank_account_name">
          {{ cutString(transaction.bank_account_name, 10) }}
        </span>
      </CTableDataCell>
      <!--      <CTableDataCell :class="sortClass">-->
      <!--        {{ transaction.sort_name }}-->
      <!--      </CTableDataCell>-->
      <CTableDataCell class="text-left truncate">
        <span v-if="transaction.content">
          {{ cutString(transaction.content, 15) }}
        </span>
      </CTableDataCell>
      <CTableDataCell
        class="text-right"
        :class="transaction.sort === 1 ? 'text-success strong' : ''"
      >
        {{ transaction.sort === 1 ? '+' : '-' }}{{ numFormat(transaction.amount || 0) }}
      </CTableDataCell>
      <CTableDataCell colspan="6" class="bg-yellow-lighten-5">
        <CTable small class="m-0 p-0">
          <colgroup>
            <col style="width: 10%" />
            <col style="width: 18%" />
            <col style="width: 22%" />
            <col style="width: 20%" />
            <col style="width: 18%" />
            <col style="width: 12%" />
          </colgroup>
          <CTableRow
            v-for="entry in transaction.accounting_entries"
            :key="entry.pk"
            class="text-center"
          >
            <CTableDataCell :class="d1Class">
              {{ entry.account_d1_name }}
            </CTableDataCell>
            <CTableDataCell>
              {{ entry.account_d2_name }}
            </CTableDataCell>
            <CTableDataCell class="text-left"> {{ entry.trader }} </CTableDataCell>
            <CTableDataCell
              class="text-right"
              :class="transaction.sort === 1 ? 'text-success strong' : ''"
            >
              {{ transaction.sort === 1 ? '+' : '-' }}{{ numFormat(entry.amount) }}
            </CTableDataCell>
            <CTableDataCell> {{ entry.evidence_type_display }} </CTableDataCell>
            <CTableDataCell v-if="write_company_cash">
              <v-icon
                icon="mdi-pencil"
                size="18"
                @click="
                  router.push({
                    name: '본사 거래 내역 - 수정',
                    params: { transId: transaction.pk },
                  })
                "
                class="pointer edit-icon-hover"
              />
            </CTableDataCell>
          </CTableRow>
        </CTable>
      </CTableDataCell>
    </CTableRow>

    <!--    &lt;!&ndash; 자식 레코드 표시 영역 &ndash;&gt;-->
    <!--    <CTableRow v-if="showChildren && hasChildren">-->
    <!--      <CTableDataCell :colspan="write_company_cash ? 11 : 10" class="p-0">-->
    <!--        <div class="p-0">-->
    <!--          &lt;!&ndash; 로딩 중 &ndash;&gt;-->
    <!--          <div v-if="loadingChildren && children.length === 0" class="text-center py-3">-->
    <!--            <v-progress-circular indeterminate color="primary" size="24"></v-progress-circular>-->
    <!--            <span class="ml-2">자식 레코드 로딩 중...</span>-->
    <!--          </div>-->

    <!--          &lt;!&ndash; 자식 레코드 테이블 &ndash;&gt;-->
    <!--          <CTable v-else-if="children.length > 0" bordered small class="mb-0">-->
    <!--            <colgroup>-->
    <!--              <col style="width: 8%" />-->
    <!--              <col style="width: 5%" />-->
    <!--              <col style="width: 10%" />-->
    <!--              <col style="width: 11%" />-->
    <!--              <col style="width: 15%" />-->
    <!--              <col style="width: 10%" />-->
    <!--              <col style="width: 10%" />-->
    <!--              <col style="width: 5%" />-->
    <!--              <col style="width: 9%" />-->
    <!--              <col style="width: 11%" />-->
    <!--              <col style="width: 6%" />-->
    <!--            </colgroup>-->
    <!--            <CTableBody>-->
    <!--              <CTableRow v-for="child in children" :key="child.pk" class="text-center">-->
    <!--                <CTableDataCell class="accent">{{ child.deal_date }}</CTableDataCell>-->
    <!--                <CTableDataCell-->
    <!--                  :class="['text-primary', 'text-danger', 'text-info'][(child?.sort ?? 1) - 1]"-->
    <!--                  class="accent"-->
    <!--                >-->
    <!--                  {{ child?.sort_desc }}-->
    <!--                </CTableDataCell>-->
    <!--                <CTableDataCell class="accent"></CTableDataCell>-->
    <!--                <CTableDataCell class="text-left accent">-->
    <!--                  <span>{{ cutString(child.trader, 8) }}</span>-->
    <!--                </CTableDataCell>-->
    <!--                <CTableDataCell class="text-left accent">-->
    <!--                  <span>{{ cutString(child.content, 15) }}</span>-->
    <!--                </CTableDataCell>-->
    <!--                <CTableDataCell class="text-right" :color="dark ? '' : 'primary'">-->
    <!--                  {{ numFormat(child.income || 0) }}-->
    <!--                </CTableDataCell>-->
    <!--                <CTableDataCell class="text-right" :color="dark ? '' : 'danger'">-->
    <!--                  {{ numFormat(child.outlay || 0) }}-->
    <!--                </CTableDataCell>-->
    <!--                <CTableDataCell-->
    <!--                  :class="-->
    <!--                    ['text-primary', 'text-danger', 'text-info'][((child?.account_d1 ?? 1) % 3) - 1]-->
    <!--                  "-->
    <!--                  class="accent"-->
    <!--                >-->
    <!--                  {{ child.account_d1_desc }}-->
    <!--                </CTableDataCell>-->
    <!--                <CTableDataCell class="text-left accent">-->
    <!--                  <span v-if="child.account_d3_desc">-->
    <!--                    {{ cutString(child.account_d3_desc, 9) }}-->
    <!--                  </span>-->
    <!--                </CTableDataCell>-->
    <!--                <CTableDataCell class="accent">{{ child.evidence_desc }}</CTableDataCell>-->
    <!--                <CTableDataCell v-if="write_company_cash" class="accent">-->
    <!--                  <v-btn-->
    <!--                    color="info"-->
    <!--                    size="x-small"-->
    <!--                    @click="showChildDetail(child)"-->
    <!--                    :disabled="!allowedPeriod"-->
    <!--                  >-->
    <!--                    확인-->
    <!--                  </v-btn>-->
    <!--                </CTableDataCell>-->
    <!--              </CTableRow>-->
    <!--            </CTableBody>-->
    <!--          </CTable>-->

    <!--          &lt;!&ndash; 페이지네이션 &ndash;&gt;-->
    <!--          <v-pagination-->
    <!--            v-if="children.length > 0 && childrenTotalPages > 1"-->
    <!--            v-model="childrenPage"-->
    <!--            :length="childrenTotalPages"-->
    <!--            :total-visible="7"-->
    <!--            density="compact"-->
    <!--            rounded="2"-->
    <!--            class="mt-4"-->
    <!--            @update:model-value="onChildrenPageChange"-->
    <!--          />-->

    <!--          &lt;!&ndash; 자식 레코드가 없을 때 &ndash;&gt;-->
    <!--          <div v-if="!loadingChildren && children.length === 0" class="text-center py-3 text-muted">-->
    <!--            분리 항목이 없습니다.-->
    <!--          </div>-->
    <!--        </div>-->
    <!--      </CTableDataCell>-->
    <!--    </CTableRow>-->
  </template>

  <FormModal ref="updateFormModal" size="lg">
    <template #header>본사 입출금 거래 건별 수정</template>
    <template #default>
      <CashForm
        :transaction="selectedCash || transaction"
        :projects="projects"
        @multi-submit="multiSubmit"
        @on-delete="deleteConfirm"
        @patch-d3-hide="patchD3Hide"
        @on-bank-create="onBankCreate"
        @on-bank-update="onBankUpdate"
        @close="updateFormModal.close()"
      />
    </template>
  </FormModal>

  <ConfirmModal ref="refDelModal">
    <template #header> 입출금 거래 정보 삭제</template>
    <template #default>
      삭제한 데이터는 복구할 수 없습니다. 해당 입출금 거래 정보를 삭제하시겠습니까?
    </template>
    <template #footer>
      <v-btn color="warning" size="small" @click="deleteObject">삭제</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>

<style scoped>
/* 기본적으로 수정 아이콘 숨김 */
.edit-icon-hover {
  opacity: 0;
  transition: opacity 0.2s ease;
}

/* 내부 테이블 행에 hover 시 아이콘 표시 */
.table tbody tr:hover .edit-icon-hover {
  opacity: 1;
}
</style>
