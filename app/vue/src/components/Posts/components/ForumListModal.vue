<script lang="ts" setup>
import { ref, computed, type PropType, onBeforeMount, onUpdated, nextTick } from 'vue'
import { btnLight } from '@/utils/cssMixins.ts'
import type { Forum } from '@/store/types/forum'
import { useProject } from '@/store/pinia/project'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({
  nowForum: { type: Number, default: null },
  forumList: { type: Array as PropType<Forum[]>, default: () => [] },
  isCopy: { type: Boolean, default: false },
})

const emit = defineEmits(['copy-post', 'move-post'])

const refListModal = ref()

const forum = ref<number | null>(null)
const project = ref<number | null>(null)

const projStore = useProject()
const projSelectList = computed(() => projStore.projSelect)

const formCheck = computed(() => forum.value == props.nowForum)

const onSubmit = () => {
  if (props.isCopy) emit('copy-post', forum.value, project.value ?? undefined)
  else emit('move-post', forum.value, project.value ?? undefined)
  refListModal.value.close()
}

const callModal = () => refListModal.value.callModal()

defineExpose({ callModal })

onBeforeMount(() => {
  if (props.nowForum) forum.value = props.nowForum
})
</script>

<template>
  <AlertModal ref="refListModal" size="lg">
    <template #header> 게시물 {{ isCopy ? '복사' : '이동' }}</template>
    <template #default>
      <CRow class="mb-3">
        <CFormLabel for="staticEmail" class="col-sm-3 col-form-label pl-5">
          본사 / 프로젝트 선택
        </CFormLabel>
        <div class="col-sm-9">
          <CFormSelect v-model="project" :disabled="forum === 1">
            <option value="">본사 게시물</option>
            <option v-for="p in projSelectList" :value="p.value" :key="p.value">
              {{ p.label }}
            </option>
          </CFormSelect>
        </div>
      </CRow>
      <CTable v-if="forumList.length" striped class="mt-3 border-top-1">
        <colgroup>
          <col style="width: 80%" />
          <col style="width: 20%" />
        </colgroup>
        <CTableBody>
          <CTableRow v-for="obj in forumList" :key="obj.pk" :item-key="obj.pk">
            <CTableDataCell>
              <div class="form-check">
                <input
                  v-model="forum"
                  :id="`forum_${obj.pk}`"
                  :value="obj.pk"
                  type="radio"
                  class="form-check-input"
                  style="margin-top: 6px"
                  :disabled="nowForum === obj.pk"
                />
                <!--                  @change="brdChk"-->
                <label :for="`forum_${obj.pk}`" class="form-label form-check-label">
                  {{ obj.name }}
                </label>
              </div>
            </CTableDataCell>
            <CTableDataCell class="text-center">
              <CBadge v-if="nowForum === obj.pk" color="warning">현재</CBadge>
            </CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>

      <CRow v-else class="text-center">
        <CCol class="py-5">등록된 게시판이 없습니다.</CCol>
      </CRow>
    </template>
    <template #footer>
      <v-btn
        :color="isCopy ? 'info' : 'warning'"
        size="small"
        @click="onSubmit"
        :disabled="formCheck"
      >
        게시물 {{ isCopy ? '복사' : '이동' }}
      </v-btn>
      <v-btn :color="btnLight" size="small" @click="refListModal.close()">닫기</v-btn>
    </template>
  </AlertModal>
</template>
