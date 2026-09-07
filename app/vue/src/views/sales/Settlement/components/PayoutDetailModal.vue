<script lang="ts" setup>
import { ref } from 'vue'
import type { CommissionPayout } from '@/store/types/sales'
import FormModal from '@/components/Modals/FormModal.vue'

const modalRef = ref()
const payout = ref<CommissionPayout | null>(null)

const open = (data: CommissionPayout) => {
  payout.value = data
  modalRef.value.callModal()
}

defineExpose({ open })
</script>

<template>
  <FormModal ref="modalRef" size="lg">
    <template #header>개인별 수수료 정산 상세 내역</template>
    <template #default>
      <CModalBody v-if="payout">
        <!-- 기본 인적사항 및 계좌 정보 -->
        <div class="bg-light p-3 rounded mb-3 border">
          <div class="d-flex justify-content-between align-items-center mb-2">
            <div>
              <span class="fs-5 fw-bold text-body mr-2">{{ payout.sales_person_name }}</span>
              <span class="badge bg-primary mr-1">{{ payout.duty_display }}</span>
              <span class="badge bg-secondary">{{ payout.team_name }}</span>
            </div>
            <div>
              <span class="text-muted small mr-1">지급 상태:</span>
              <span class="badge bg-info">{{ payout.pay_status_display }}</span>
            </div>
          </div>
          <div class="small text-secondary">
            <v-icon icon="mdi-bank" size="x-small" class="mr-1" />
            입금 계좌: <strong>{{ payout.bank_name || '-' }}</strong>
            {{ payout.account_number }} (예금주: {{ payout.account_holder }})
          </div>
        </div>

        <!-- 정산 금액 산출 내역 -->
        <div class="row g-2 mb-3 text-center">
          <div class="col-4">
            <div class="border rounded p-2 bg-more-secondary">
              <div class="small text-muted">건당 인센티브 합계</div>
              <div class="fw-bold text-primary fs-6">
                {{ payout.commission_amount.toLocaleString() }}원
              </div>
              <div class="small text-muted">{{ payout.contract_count }}건</div>
            </div>
          </div>
          <div class="col-4">
            <div class="border rounded p-2 bg-more-secondary">
              <div class="small text-muted">기본급 / 일비</div>
              <div class="fw-bold text-body fs-6">{{ payout.base_pay.toLocaleString() }}원</div>
            </div>
          </div>
          <div class="col-4">
            <div class="border rounded p-2 bg-more-secondary">
              <div class="small text-muted">공제/환수액 (차감)</div>
              <div class="fw-bold text-danger fs-6">
                -{{ payout.deduction_amount.toLocaleString() }}원
              </div>
            </div>
          </div>
        </div>

        <!-- 세금 계산 및 실지급액 테이블 -->
        <table class="table table-bordered small text-center mb-3">
          <thead class="table-light">
            <tr>
              <th>지급 총액 (세전)</th>
              <th>사업소득세 (3%)</th>
              <th>지방소득세 (0.3%)</th>
              <th>원천징수 합계 (3.3%)</th>
              <th class="bg-more-secondary text-primary fw-bold">실지급액 (세후)</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td class="fw-bold font-monospace">{{ payout.gross_amount.toLocaleString() }}원</td>
              <td class="text-danger font-monospace">{{ payout.income_tax.toLocaleString() }}원</td>
              <td class="text-danger font-monospace">
                {{ payout.local_income_tax.toLocaleString() }}원
              </td>
              <td class="text-danger fw-bold font-monospace">
                {{ payout.total_tax.toLocaleString() }}원
              </td>
              <td class="bg-more-secondary text-primary fw-bold fs-6 font-monospace">
                {{ payout.net_amount.toLocaleString() }}원
              </td>
            </tr>
          </tbody>
        </table>

        <!-- 포함된 계약 건별 상세 내역 -->
        <div class="border-top pt-3">
          <div class="fw-bold mb-2 text-body">
            <v-icon icon="mdi-format-list-bulleted" size="small" class="mr-1 text-primary" />
            정산 대상 계약 상세 목록 ({{ payout.contract_details?.length ?? 0 }}건)
          </div>
          <div class="table-responsive" style="max-height: 240px; overflow-y: auto">
            <table class="table table-sm table-hover table-bordered small text-center mb-0">
              <thead class="table-light sticky-top">
                <tr>
                  <th>계약 일련번호</th>
                  <th>계약자명</th>
                  <th>수당 구분</th>
                  <th>지급 수수료 (원)</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="c in payout.contract_details" :key="c.id">
                  <td class="font-monospace">{{ c.contract_serial }}</td>
                  <td class="fw-bold">{{ c.contractor_name }}</td>
                  <td>
                    <span class="badge bg-light text-body border">{{ c.role_type_display }}</span>
                  </td>
                  <td class="text-right font-monospace fw-bold text-primary">
                    {{ c.unit_fee.toLocaleString() }}원
                  </td>
                </tr>
                <tr v-if="!payout.contract_details || payout.contract_details.length === 0">
                  <td colspan="4" class="py-3 text-muted">상세 계약 내역이 없습니다.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div v-if="payout.note" class="mt-3 p-2 bg-light rounded small text-muted">
          <strong>메모:</strong> {{ payout.note }}
        </div>
      </CModalBody>
      <CModalFooter>
        <v-btn color="light" size="small" flat @click="modalRef.close()">닫기</v-btn>
      </CModalFooter>
    </template>
  </FormModal>
</template>
