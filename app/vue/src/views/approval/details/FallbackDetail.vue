<script setup lang="ts">
import { CTable, CTableBody, CTableRow, CTableHeaderCell, CTableDataCell } from '@coreui/vue'

defineProps<{
  content: Record<string, any>
  document?: any
}>()
</script>

<template>
  <div>
    <!-- body 또는 content 단독 텍스트인 경우 -->
    <div
      v-if="content.body || content.content || content.description"
      class="p-3 bg-more-light border rounded mb-3"
      style="white-space: pre-wrap; line-height: 1.6"
    >
      {{ content.body || content.content || content.description }}
    </div>

    <!-- 기타 다중 key-value 필드가 있는 경우 테이블로 렌더링 -->
    <CTable
      v-if="Object.keys(content).some(k => !['body', 'content', 'description'].includes(String(k)))"
      small
      bordered
      responsive
      class="mb-0"
    >
      <CTableBody>
        <CTableRow
          v-for="(val, key) in content"
          :key="key"
          v-show="!['body', 'content', 'description'].includes(String(key))"
        >
          <CTableHeaderCell class="text-center bg-more-light" style="width: 140px">
            {{ String(key) }}
          </CTableHeaderCell>
          <CTableDataCell class="pl-3" style="white-space: pre-wrap">
            {{ typeof val === 'object' ? JSON.stringify(val, null, 2) : String(val) }}
          </CTableDataCell>
        </CTableRow>
      </CTableBody>
    </CTable>

    <div v-if="!Object.keys(content).length" class="text-center text-muted py-3">
      등록된 상세 품의 내용이 없습니다.
    </div>
  </div>
</template>
