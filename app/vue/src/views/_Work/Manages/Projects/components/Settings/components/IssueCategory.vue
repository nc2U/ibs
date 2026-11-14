<script lang="ts" setup>
import { ref, type PropType } from 'vue'
import { useRoute } from 'vue-router'
import type { SimpleCategory } from '@/store/types/work_issue'
import NoData from '@/components/NoData/Index.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import TextButton from '@/views/_Work/components/atomics/TextButton.vue'

defineProps({ categories: { type: Array as PropType<SimpleCategory[]>, default: () => [] } })

const emit = defineEmits(['delete-category'])

const route = useRoute()

const RefCateDelConfirm = ref<InstanceType<typeof ConfirmModal> | null>(null)

const deleteCatePk = ref<number | null>(null)

const toDelete = (pk: number) => {
  deleteCatePk.value = pk
  RefCateDelConfirm.value?.callModal(
    '',
    '이 업무 범주 삭제를 계속 진행 하시겠습니까?',
    '',
    'warning',
  )
}

const deleteCategory = () => {
  if (deleteCatePk.value) {
    emit('delete-category', deleteCatePk.value)
    RefCateDelConfirm.value?.close()
  }
}
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <span class="mr-2 form-text">
        <TextButton
          name="새 업무범주"
          :to="{ name: '(설정) - 범주추가', params: { projId: route.params.projId } }"
        />
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
            <CTableDataCell>{{ category.name }}</CTableDataCell>
            <CTableDataCell>{{ category.assigned_to?.username }}</CTableDataCell>
            <CTableDataCell class="form-text">
              <span class="mr-2">
                <v-icon icon="mdi-pencil" color="amber" size="sm" class="mr-1" />
                <router-link
                  :to="{
                    name: '(설정) - 범주수정',
                    params: { projId: route.params.projId, cateId: category.pk },
                  }"
                >
                  편집
                </router-link>
              </span>
              <span>
                <v-icon icon="mdi-trash-can" color="grey" size="sm" class="me-1" />
                <a href="#" @click.prevent="toDelete(category.pk)">삭제</a>
              </span>
            </CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>
    </CCol>
  </CRow>

  <ConfirmModal ref="RefCateDelConfirm">
    <template #footer>
      <v-btn color="warning" size="small" @click="deleteCategory">삭제</v-btn>
    </template>
  </ConfirmModal>
</template>
