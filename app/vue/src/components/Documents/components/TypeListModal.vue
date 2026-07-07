<script lang="ts" setup>
import { ref, computed, onUpdated } from 'vue'
import { useDocs } from '@/store/pinia/docs'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({
  nowType: { type: [String, Number], default: null },
  isCopy: { type: Boolean, default: false },
})

const emit = defineEmits(['copy-docs', 'move-docs'])

const docStore = useDocs()
const docTypes = computed(() => docStore.docTypes)

const refListModal = ref()

const doc_type = ref<number | null>(null)
const project = ref<number | null>(null)

const formCheck = computed(() => {
  return doc_type.value === Number(props.nowType)
})

const onSubmit = () => {
  if (props.isCopy) emit('copy-docs', doc_type.value, project.value ?? undefined)
  else emit('move-docs', doc_type.value, project.value ?? undefined)
  refListModal.value.close()
}

const callModal = () => refListModal.value.callModal()

defineExpose({ callModal })

onUpdated(() => {
  if (props.nowType) doc_type.value = Number(props.nowType)
})
</script>

<template>
  <AlertModal ref="refListModal" size="lg">
    <template #header> 게시물 {{ isCopy ? '복사' : '이동' }}</template>
    <template #default>
      <CTable v-if="docTypes.length" striped class="mt-3 border-top-1">
        <colgroup>
          <col style="width: 80%" />
          <col style="width: 20%" />
        </colgroup>
        <CTableBody>
          <CTableRow v-for="obj in docTypes" :key="obj.value" :item-key="obj.value">
            <CTableDataCell>
              <div class="form-check">
                <input
                  v-model="doc_type"
                  :id="`type_${obj.value}`"
                  :value="obj.value"
                  type="radio"
                  class="form-check-input"
                  style="margin-top: 6px"
                  :disabled="Number(nowType) === obj.value"
                />
                <label :for="`doc_type_${obj.value}`" class="form-label form-check-label">
                  {{ obj.label }}
                </label>
              </div>
            </CTableDataCell>
            <CTableDataCell class="text-center">
              <CBadge v-if="Number(nowType) === obj.value" color="warning">현재</CBadge>
            </CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>

      <CRow v-else class="text-center">
        <CCol class="py-5">등록된 문서 유형이 없습니다.</CCol>
      </CRow>
    </template>
    <template #footer>
      <v-btn
        :color="isCopy ? 'info' : 'warning'"
        size="small"
        @click="onSubmit"
        :disabled="formCheck"
      >
        문서 {{ isCopy ? '복사' : '이동' }}
      </v-btn>
      <v-btn color="light" size="small" @click="refListModal.close()" flat>닫기</v-btn>
    </template>
  </AlertModal>
</template>
