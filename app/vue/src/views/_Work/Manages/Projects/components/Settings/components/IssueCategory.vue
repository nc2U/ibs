<script lang="ts" setup>
import { ref, type PropType } from 'vue'
import type { SimpleCategory } from '@/store/types/work_issue.ts'
import NoData from '@/views/_Work/components/NoData.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

defineProps({ categories: { type: Array as PropType<SimpleCategory[]>, default: () => [] } })

const emit = defineEmits(['delete-category'])

const RefCateDelConfirm = ref()

const deleteCatePk = ref()

const toDelete = (pk: number) => {
  deleteCatePk.value = pk
  RefCateDelConfirm.value.callModal(
    '',
    '이 업무 범주 삭제를 계속 진행 하시겠습니까?',
    '',
    'warning',
  )
}

const deleteCategory = () => {
  emit('delete-category', deleteCatePk.value)
  RefCateDelConfirm.value.close()
}
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <span class="mr-2 form-text">
        <v-icon icon="mdi-plus-circle" color="success" size="sm" />
        <router-link :to="{ name: '(설정) - 범주추가' }" class="ml-1">새 업무범주</router-link>
      </span>
    </CCol>
  </CRow>

  <NoData v-if="!categories.length" />

  <CRow v-else>
    <CCol>
      <v-divider class="my-0" />
      <CTable small striped responsive hover>
        <colgroup>
          <col style="width: 60%" />
          <col style="width: 30%" />
          <col style="width: 10%" />
        </colgroup>
        <CTableHead>
          <CTableRow class="text-center">
            <CTableHeaderCell>업무 범주</CTableHeaderCell>
            <CTableHeaderCell>담당자</CTableHeaderCell>
            <CTableHeaderCell></CTableHeaderCell>
          </CTableRow>
        </CTableHead>

        <CTableBody>
          <CTableRow v-for="category in categories" :key="category.pk" class="text-center">
            <CTableDataCell class="text-left">{{ category.name }}</CTableDataCell>
            <CTableDataCell>{{ category.assigned_to?.username }}</CTableDataCell>
            <CTableDataCell class="form-text">
              <span class="mr-2">
                <v-icon icon="mdi-pencil" color="amber" size="sm" class="mr-1" />
                <router-link :to="{ name: '(설정) - 범주수정', params: { cateId: category.pk } }">
                  편집
                </router-link>
              </span>
              <span>
                <v-icon icon="mdi-trash-can" color="grey" size="sm" class="mr-1" />
                <router-link to="" @click="toDelete(category.pk)">삭제</router-link>
              </span>
            </CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>
    </CCol>
  </CRow>

  <ConfirmModal ref="RefCateDelConfirm">
    <template #footer>
      <v-btn color="warning" @click="deleteCategory">삭제</v-btn>
    </template>
  </ConfirmModal>
</template>
