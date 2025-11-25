<script lang="ts" setup>
import { ref, computed } from 'vue'
import { useComCash } from '@/store/pinia/comCash'
import type { CompanyBank } from '@/store/types/comCash'
import BankAccForm from './BankAccForm.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const emit = defineEmits(['on-bank-create', 'on-bank-update'])

const comBankAcc = ref()
const bankAccAdd = ref(false)

const comCashStore = useComCash()
const allComBankList = computed(() => comCashStore.allComBankList)

const onBankCreate = (payload: CompanyBank) => emit('on-bank-create', payload)
const onBankUpdate = (payload: CompanyBank) => emit('on-bank-update', payload)

const callModal = () => comBankAcc.value.callModal()

defineExpose({ callModal })
</script>

<template>
  <AlertModal ref="comBankAcc" size="lg">
    <template #header> 본사 거래 계좌 관리</template>
    <template #default>
      <CAccordion class="mb-3">
        <CAccordionItem v-for="bank in allComBankList" :key="bank.pk" :item-key="bank.pk as number">
          <CAccordionHeader>
            {{ `${bank.alias_name}  :: ${bank.number}` }}
          </CAccordionHeader>
          <CAccordionBody class="pl-3">
            <BankAccForm :bank-acc="bank" @on-bank-update="onBankUpdate" />
          </CAccordionBody>
        </CAccordionItem>
      </CAccordion>

      <CRow v-show="bankAccAdd">
        <CCol>
          <h5 class="p-3 bg-light">
            <v-icon icon="mdi-plus-circle" color="primary" class="mr-1" />
            계좌 추가
          </h5>
          <BankAccForm @on-bank-create="onBankCreate" />
        </CCol>
      </CRow>

      <CRow>
        <CCol class="text-right">
          <v-btn
            :prepend-icon="`mdi-${!bankAccAdd ? 'plus' : 'minus'}-circle`"
            variant="text"
            @click="bankAccAdd = !bankAccAdd"
          >
            <template v-slot:prepend>
              <v-icon :color="!bankAccAdd ? 'success' : 'secondary'"></v-icon>
            </template>
            <span v-if="!bankAccAdd">계좌 추가</span>
            <span v-else>추가 취소</span>
          </v-btn>
        </CCol>
      </CRow>
    </template>
    <template #footer></template>
  </AlertModal>
</template>
