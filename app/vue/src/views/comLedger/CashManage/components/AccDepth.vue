<script lang="ts" setup>
import { ref, computed } from 'vue'
import { useComCash } from '@/store/pinia/comCash'
import { cutString } from '@/utils/baseMixins'
import AlertModal from '@/components/Modals/AlertModal.vue'

const emit = defineEmits(['patch-d3-hide'])

const refDAccount = ref()

const useComCashStore = useComCash()
const listAccD1List = computed(() => useComCashStore.listAccD1List)
const listAccD2List = computed(() => useComCashStore.listAccD2List)
const listAccD3List = computed(() => useComCashStore.listAccD3List)

const patchD3Hide = (pk: number, is_hide: boolean) => emit('patch-d3-hide', { pk, is_hide })

const callModal = () => refDAccount.value.callModal()

defineExpose({ callModal })
</script>

<template>
  <AlertModal ref="refDAccount" size="lg">
    <template #header> 계정 분류 보기</template>
    <template #default>
      <CAccordion>
        <CAccordionItem v-for="d1 in listAccD1List" :key="d1.pk" :item-key="d1.pk">
          <CAccordionHeader>
            {{ `[${d1.code}] ${d1.name} (${d1.description})` }}
          </CAccordionHeader>
          <CAccordionBody class="pl-3">
            <CAccordion>
              <CAccordionItem
                v-for="d2 in listAccD2List.filter(a => a.d1 === d1.pk)"
                :key="d2.pk"
                :item-key="d2.pk"
              >
                <CAccordionHeader>
                  [{{ d2.code }}] {{ d2.name }} - ({{ d2.description }})
                </CAccordionHeader>
                <CAccordionBody class="pl-3">
                  <CRow
                    v-for="d3 in listAccD3List.filter(a => a.d2 === d2.pk)"
                    :key="d3.pk"
                    class="pl-3 mb-2"
                  >
                    <CCol lg="10">
                      [{{ d3.code }}] {{ d3.name }} ::
                      {{ cutString(d3.description, 32) }}
                    </CCol>
                    <CCol lg="2" class="text-right">
                      <CFormCheck
                        :id="d3.code"
                        :checked="d3.is_hide"
                        label="미사용"
                        @change="patchD3Hide(d3.pk, $event.target.checked)"
                      />
                      <v-tooltip activator="parent" location="start">
                        입출금 등록 시 이 계정 항목을 숨길
                      </v-tooltip>
                    </CCol>
                  </CRow>
                </CAccordionBody>
              </CAccordionItem>
            </CAccordion>
          </CAccordionBody>
        </CAccordionItem>
      </CAccordion>
    </template>
    <template #footer></template>
  </AlertModal>
</template>
