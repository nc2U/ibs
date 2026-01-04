<script lang="ts" setup>
import { ref, computed } from 'vue'
import { useProCash } from '@/store/pinia/proCash'
import { type ProBankAcc } from '@/store/types/proCash'
import AlertModal from '@/components/Modals/AlertModal.vue'
import BankAccForm from './BankAccForm.vue'

const emit = defineEmits(['on-bank-create', 'on-bank-update'])

const refComBankAcc = ref()
const bankAccAdd = ref(false)

const proCashStore = useProCash()
const allProBankAccList = computed(() => proCashStore.allProBankAccountList)

const onBankCreate = (payload: ProBankAcc) => emit('on-bank-create', payload)
const onBankUpdate = (payload: ProBankAcc) => emit('on-bank-update', payload)

const callModal = () => refComBankAcc.value.callModal()

defineExpose({ callModal })
</script>

<template>
  <AlertModal ref="refComBankAcc" size="lg">
    <template #header> 프로젝트 거래 계좌 관리</template>
    <template #default>
      <CAccordion class="mb-3">
        <CAccordionItem v-for="bank in allProBankAccList" :key="bank.pk" :item-key="bank.pk">
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
