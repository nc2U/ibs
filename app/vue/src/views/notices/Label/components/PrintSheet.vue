<script lang="ts" setup>
import { computed } from 'vue'
import type { PostLabel } from '@/store/types/notice'
import { SPECS, type PrintOptions } from '../types'

const props = defineProps<{
  items: PostLabel[]
  options: PrintOptions
}>()


const currentSpec = computed(() => SPECS[props.options.specCode] || SPECS['3107'])

// 시작 위치 오프셋(빈 라벨 칸)을 고려하여 페이지 단위 청크로 분할
const pages = computed(() => {
  const spec = currentSpec.value
  const offset = Math.max(0, (props.options.startOffset || 1) - 1)
  const fullCells: (PostLabel | null)[] = []

  // 시작 오프셋만큼 빈 칸 삽입
  for (let i = 0; i < offset; i++) {
    fullCells.push(null)
  }

  // 실제 라벨 데이터 삽입
  props.items.forEach(item => {
    fullCells.push(item)
  })

  // A4 단위(perPage)로 슬라이스
  const result: (PostLabel | null)[][] = []
  for (let i = 0; i < fullCells.length; i += spec.perPage) {
    const pageCells = fullCells.slice(i, i + spec.perPage)
    // 마지막 페이지 남은 셀을 빈 셀로 채움
    while (pageCells.length < spec.perPage) {
      pageCells.push(null)
    }
    result.push(pageCells)
  }

  return result.length > 0 ? result : [Array(spec.perPage).fill(null)]
})

// 주소 추출 헬퍼
const getZipcode = (item: PostLabel) => {
  if (props.options.addressType === 'dm') return item.dm_zipcode || item.id_zipcode || ''
  if (props.options.addressType === 'id') return item.id_zipcode || ''
  return item.effective_zipcode || ''
}

const getAddress1 = (item: PostLabel) => {
  if (props.options.addressType === 'dm') return item.dm_address1 || item.id_address1 || ''
  if (props.options.addressType === 'id') return item.id_address1 || ''
  return item.effective_address1 || ''
}

const getAddress2 = (item: PostLabel) => {
  if (props.options.addressType === 'dm') {
    const a2 = item.dm_address2 || item.id_address2 || ''
    const a3 = item.dm_address3 || item.id_address3 || ''
    return `${a2} ${a3}`.trim()
  }
  if (props.options.addressType === 'id') {
    return `${item.id_address2 || ''} ${item.id_address3 || ''}`.trim()
  }
  return `${item.effective_address2 || ''} ${item.effective_address3 || ''}`.trim()
}
</script>

<template>
  <div class="print-container">
    <div
      v-for="(page, pageIdx) in pages"
      :key="pageIdx"
      class="print-page"
      :style="{
        paddingTop: currentSpec.marginTop,
        paddingLeft: currentSpec.marginLeft,
      }"
    >
      <div
        class="label-grid"
        :style="{
          gridTemplateColumns: `repeat(${currentSpec.columns}, ${currentSpec.labelWidth})`,
          gridAutoRows: currentSpec.labelHeight,
          columnGap: currentSpec.gapX,
          rowGap: currentSpec.gapY,
        }"
      >
        <div
          v-for="(cell, cellIdx) in page"
          :key="cellIdx"
          class="label-cell"
          :class="{
            'empty-cell': !cell,
            [`font-${options.fontSize}`]: true,
          }"
          :style="{
            width: currentSpec.labelWidth,
            height: currentSpec.labelHeight,
          }"
        >
          <template v-if="cell">
            <div class="cell-inner">
              <!-- 상단: 우편번호 및 동호수 -->
              <div class="cell-header">
                <span class="zipcode-badge">[{{ getZipcode(cell) }}]</span>
                <span v-if="options.showUnitInfo && cell.unit_info" class="unit-tag">
                  {{ cell.unit_info }}
                </span>
              </div>

              <!-- 중단: 기본주소 + 상세주소 -->
              <div class="cell-address">
                <div class="address-line1">{{ getAddress1(cell) }}</div>
                <div v-if="getAddress2(cell)" class="address-line2">{{ getAddress2(cell) }}</div>
              </div>

              <!-- 하단: 수신인 및 호칭 -->
              <div class="cell-recipient">
                <span class="recipient-name">{{ cell.contractor_name }}</span>
                <span v-if="options.honorific" class="recipient-honorific">
                  {{ options.honorific }}
                </span>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 화면 미리보기 모드 */
.print-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  background-color: #f1f5f9;
  padding: 20px 0;
}

.print-page {
  box-sizing: border-box;
  width: 210mm;
  height: 297mm;
  background-color: #ffffff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  position: relative;
  page-break-after: always;
  break-after: page;
  overflow: hidden;
}

.label-grid {
  display: grid;
  width: 100%;
  height: 100%;
}

.label-cell {
  box-sizing: border-box;
  border: 1px dashed #cbd5e1; /* 화면에서는 칸 구분을 위해 점선 표시 */
  padding: 3.5mm 4mm;
  display: flex;
  flex-direction: column;
  justify-content: center;
  overflow: hidden;
  background-color: #ffffff;
  position: relative;
}

.label-cell.empty-cell {
  background-color: #f8fafc;
  opacity: 0.6;
}

.cell-inner {
  display: flex;
  flex-direction: column;
  height: 100%;
  justify-content: space-between;
  line-height: 1.35;
  color: #1e293b;
}

.cell-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.85em;
  font-weight: 600;
  color: #0f172a;
}

.zipcode-badge {
  letter-spacing: 1px;
  font-weight: 700;
}

.unit-tag {
  color: #475569;
  font-size: 0.9em;
}

.cell-address {
  margin: 1.5mm 0;
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.address-line1 {
  font-weight: 500;
  word-break: keep-all;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.address-line2 {
  color: #334155;
  font-size: 0.92em;
  word-break: keep-all;
}

.cell-recipient {
  text-align: right;
  font-weight: 700;
  padding-right: 2mm;
}

.recipient-name {
  font-size: 1.15em;
  letter-spacing: 1px;
}

.recipient-honorific {
  margin-left: 4px;
  font-size: 0.95em;
  font-weight: 500;
}

/* 폰트 크기 변형 */
.font-sm {
  font-size: 8pt;
}
.font-base {
  font-size: 9.5pt;
}
.font-lg {
  font-size: 11pt;
}

/* ═══════════════════════════════════════════════════
   실제 브라우저 인쇄 모드 (@media print)
   - 여백 제거, 라벨 테두리 제거, 정확한 A4 매칭
   ═══════════════════════════════════════════════════ */
@media print {
  @page {
    size: A4 portrait;
    margin: 0; /* 브라우저 기본 헤더/푸터 및 여백 완전 제거 */
  }

  body * {
    visibility: hidden;
  }

  .print-container,
  .print-container * {
    visibility: visible;
  }

  .print-container {
    position: absolute;
    left: 0;
    top: 0;
    width: 100%;
    margin: 0;
    padding: 0;
    background: none;
    gap: 0;
  }

  .print-page {
    box-shadow: none;
    margin: 0;
    page-break-after: always;
    break-after: page;
  }

  .label-cell {
    border: none !important; /* 인쇄 시 라벨 테두리 점선 제거 */
    background: transparent !important;
  }

  .label-cell.empty-cell {
    visibility: hidden;
  }
}
</style>
