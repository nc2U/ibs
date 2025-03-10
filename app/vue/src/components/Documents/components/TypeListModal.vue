<script lang="ts" setup>
import { ref, computed, type PropType, onBeforeMount, onUpdated, nextTick } from 'vue'
import type { DocType } from '@/store/types/docs'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({
  nowType: { type: Number, default: null },
  // nowProject: { type: Number, default: null },
  docTypeList: { type: Array as PropType<DocType[]>, default: () => [] },
  isCopy: { type: Boolean, default: false },
})

const emit = defineEmits(['copy-post', 'move-post'])

const refListModal = ref()

const doc_type = ref<number | null>(null)
const project = ref<number | null>(null)

const formCheck = computed(() => {
  const a = doc_type.value == props.nowType
  // const b = project.value == props.nowProject
  return a // && b
})

const onSubmit = () => {
  if (props.isCopy) emit('copy-post', doc_type.value, project.value ?? undefined)
  else emit('move-post', doc_type.value, project.value ?? undefined)
  refListModal.value.close()
}

const callModal = () => refListModal.value.callModal()

defineExpose({ callModal })

onBeforeMount(() => {
  // if (props.nowProject) project.value = props.nowProject
})

onUpdated(() => {
  if (props.nowType) doc_type.value = props.nowType
  // if (props.nowProject) project.value = props.nowProject
})
</script>

<template>
  <AlertModal ref="refListModal" size="lg">
    <template #header> 게시물 {{ isCopy ? '복사' : '이동' }}</template>
    <template #default>
      <!--      <CRow class="mb-3">-->
      <!--        <CFormLabel for="staticEmail" class="col-sm-3 col-form-label pl-5">-->
      <!--          본사 / 프로젝트 선택-->
      <!--        </CFormLabel>-->
      <!--        <div class="col-sm-9">-->
      <!--          <CFormSelect v-model="project" :disabled="doc_type === 1">-->
      <!--            <option value="">본사 게시물</option>-->
      <!--            <option v-for="p in projSelectList" :value="p.value" :key="p.value">-->
      <!--              {{ p.label }}-->
      <!--            </option>-->
      <!--          </CFormSelect>-->
      <!--        </div>-->
      <!--      </CRow>-->
      <CTable v-if="docTypeList.length" striped class="mt-3 border-top-1">
        <colgroup>
          <col style="width: 80%" />
          <col style="width: 20%" />
        </colgroup>
        <CTableBody>
          <CTableRow v-for="obj in docTypeList" :key="obj.pk" :item-key="obj.pk">
            <CTableDataCell>
              <div class="form-check">
                <input
                  v-model="doc_type"
                  :id="`type_${obj.pk}`"
                  :value="obj.pk"
                  type="radio"
                  class="form-check-input"
                  style="margin-top: 6px"
                  :disabled="nowType === obj.pk"
                />
                <label :for="`doc_type_${obj.pk}`" class="form-label form-check-label">
                  {{ obj.name }}
                </label>
              </div>
            </CTableDataCell>
            <CTableDataCell class="text-center">
              <CBadge v-if="nowType === obj.pk" color="warning">현재</CBadge>
            </CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>

      <CRow v-else class="text-center">
        <CCol class="py-5">등록된 문서 유형이 없습니다.</CCol>
      </CRow>
    </template>
    <template #footer>
      <CButton :color="isCopy ? 'warning' : 'danger'" @click="onSubmit" :disabled="formCheck">
        문서 {{ isCopy ? '복사' : '이동' }}
      </CButton>
      <CButton color="light" @click="refListModal.close()">닫기</CButton>
    </template>
  </AlertModal>
</template>
