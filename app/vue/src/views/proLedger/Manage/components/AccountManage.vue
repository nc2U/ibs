<script lang="ts" setup>
import { ref, computed } from 'vue'
import { useProCash } from '@/store/pinia/proCash'
import { cutString } from '@/utils/baseMixins'
import AlertModal from '@/components/Modals/AlertModal.vue'

const refDAccount = ref()

const proCashStore = useProCash()
const allAccD2List = computed(() => proCashStore.allAccD2List)
const allAccD3List = computed(() => proCashStore.allAccD3List)

const callModal = () => refDAccount.value.callModal()

defineExpose({ callModal })
</script>

<template>
  <AlertModal ref="refDAccount" size="lg">
    <template #header> 프로젝트 계정 분류 보기</template>
    <template #default>
      <CAccordion>
        <CAccordionItem v-for="d2 in allAccD2List" :key="d2.pk" :item-key="d2.pk">
          <CAccordionHeader>
            {{ `[${d2.code}] ${d2.name} :: ${cutString(d2.description, 45)}` }}
          </CAccordionHeader>
          <CAccordionBody class="pl-3">
            <CRow
              v-for="d3 in allAccD3List.filter(d => d.d2 === d2.pk)"
              :key="d3.pk"
              class="pl-2 mb-2"
            >
              <CCol>
                [{{ d3.code }}] {{ d3.name }} ::
                {{ cutString(d3.description, 38) }}
              </CCol>
            </CRow>
          </CAccordionBody>
        </CAccordionItem>
      </CAccordion>
    </template>
    <template #footer></template>
  </AlertModal>
</template>
