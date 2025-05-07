<script lang="ts" setup>
import { type PropType, ref } from 'vue'
import type { PostCategory } from '@/store/types/board'
import AlertModal from '@/components/Modals/AlertModal.vue'

defineProps({
  nowCate: { type: Number, default: null },
  categoryList: { type: Array as PropType<PostCategory[]>, default: () => [] },
})

const emit = defineEmits(['change-cate'])

const refListModal = ref()

const category = ref<number | null>(null)

const onSubmit = () => {
  emit('change-cate', category.value ?? undefined)
  refListModal.value.close()
}

const callModal = () => refListModal.value.callModal()

defineExpose({ callModal })
</script>

<template>
  <AlertModal ref="refListModal" size="lg">
    <template #header> 카테고리 변경</template>
    <template #default>
      <CTable v-if="categoryList.length" striped class="mt-3 border-top-1">
        <colgroup>
          <col style="width: 80%" />
          <col style="width: 20%" />
        </colgroup>
        <CTableBody>
          <CTableRow v-for="obj in categoryList" :key="obj.pk" :item-key="obj.pk">
            <CTableDataCell>
              <div class="form-check">
                <input
                  v-model="category"
                  :id="`cate_${obj.pk}`"
                  :value="obj.pk"
                  type="radio"
                  class="form-check-input"
                  style="margin-top: 6px"
                  :disabled="nowCate === obj.pk"
                />
                <label class="form-label form-check-label" :for="`cate_${obj.pk}`">
                  {{ obj.name }}
                </label>
              </div>
            </CTableDataCell>
            <CTableDataCell class="text-center">
              <CBadge v-if="nowCate === obj.pk" color="warning">현재</CBadge>
            </CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>

      <CRow v-else class="text-center">
        <CCol class="py-5">해당 게시판에 카테고리가 없습니다.</CCol>
      </CRow>
    </template>
    <template #footer>
      <v-btn color="warning" @click="onSubmit" :disabled="!category">카테고리 변경</v-btn>
      <v-btn color="light" @click="refListModal.close()">닫기</v-btn>
    </template>
  </AlertModal>
</template>
