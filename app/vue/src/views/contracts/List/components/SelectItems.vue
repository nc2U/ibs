<script lang="ts" setup>
import { computed, type PropType } from 'vue'

const props = defineProps({
  unitSet: { type: Boolean, default: false },
  visible: { type: Boolean, default: false },
  printItems: {
    type: Array as PropType<string[]>,
    default: () => ['1', '3', '4', '5', '8', '13', '14'],
  },
})

const emit = defineEmits(['update:print-items', 'print-items'])

const selectedItems = computed({
  get: () => props.printItems,
  set: (val: string[]) => {
    emit('update:print-items', val)
    emit('print-items', val)
  },
})
</script>

<template>
  <CCollapse :visible="visible" class="bg-more-light border">
    <v-container class="m-0" fluid>
      <v-row class="my-checkbox d-flex py-2">
        <v-checkbox-btn
          id="printItems1"
          v-model="selectedItems"
          label="일련번호"
          value="1"
          inline
          color="grey"
          readonly
          hide-details
          class="me-2"
        />
        <v-checkbox-btn
          id="printItems2"
          v-model="selectedItems"
          label="등록상태"
          value="2"
          inline
          color="indigo"
          hide-details
          class="me-2"
        />
        <v-checkbox-btn
          id="printItems3"
          v-model="selectedItems"
          label="차수"
          value="3"
          inline
          color="indigo"
          hide-details
          class="me-2"
        />
        <v-checkbox-btn
          id="printItems4"
          v-model="selectedItems"
          label="타입"
          value="4"
          inline
          color="indigo"
          hide-details
          class="me-2"
        />
        <v-checkbox-btn
          id="printItems5"
          v-model="selectedItems"
          label="계약자"
          value="5"
          inline
          color="indigo"
          hide-details
          class="me-2"
        />
        <v-checkbox-btn
          v-if="unitSet"
          id="printItems6"
          v-model="selectedItems"
          label="동호수"
          value="6-7"
          inline
          color="indigo"
          hide-details
          class="me-2"
        />
        <v-checkbox-btn
          id="printItems8"
          v-model="selectedItems"
          label="가입계약일"
          value="8"
          inline
          color="indigo"
          hide-details
          class="me-2"
        />
        <v-checkbox-btn
          id="printItems9"
          v-model="selectedItems"
          label="공급계약일"
          value="9"
          inline
          color="indigo"
          hide-details
          class="me-2"
        />
        <v-checkbox-btn
          id="printItems10"
          v-model="selectedItems"
          label="건물가"
          value="10"
          inline
          color="indigo"
          hide-details
          class="me-2"
        />
        <v-checkbox-btn
          id="printItems11"
          v-model="selectedItems"
          label="대지가"
          value="11"
          inline
          color="indigo"
          hide-details
          class="me-2"
        />
        <v-checkbox-btn
          id="printItems12"
          v-model="selectedItems"
          label="부가세"
          value="12"
          inline
          color="indigo"
          hide-details
          class="me-2"
        />
        <v-checkbox-btn
          id="printItems13"
          v-model="selectedItems"
          label="공급가액"
          value="13"
          inline
          color="indigo"
          hide-details
          class="me-2"
        />
        <v-checkbox-btn
          id="printItems14"
          v-model="selectedItems"
          label="납입금합계"
          value="14"
          inline
          color="indigo"
          hide-details
          class="me-2"
        />
        <v-checkbox-btn
          id="printItems15"
          v-model="selectedItems"
          label="생년월일"
          value="15"
          inline
          color="indigo"
          hide-details
          class="me-2"
        />
        <v-checkbox-btn
          id="printItems16"
          v-model="selectedItems"
          label="연락처[1]"
          value="16"
          inline
          color="indigo"
          hide-details
          class="me-2"
        />
        <v-checkbox-btn
          id="printItems17"
          v-model="selectedItems"
          label="연락처[2]"
          value="17"
          inline
          color="indigo"
          hide-details
          class="me-2"
        />
        <v-checkbox-btn
          id="printItems18"
          v-model="selectedItems"
          label="연락처[3]"
          value="18"
          inline
          color="indigo"
          hide-details
          class="me-2"
        />
        <v-checkbox-btn
          id="printItems19"
          v-model="selectedItems"
          label="이메일"
          value="19"
          inline
          color="indigo"
          hide-details
          class="me-2"
        />
        <v-checkbox-btn
          id="printItems20"
          v-model="selectedItems"
          label="주소[등본]"
          value="20-21-22-23"
          inline
          color="indigo"
          hide-details
          class="me-2"
        />
        <v-checkbox-btn
          id="printItems24"
          v-model="selectedItems"
          label="주소[우편]"
          value="24-25-26-27"
          inline
          color="indigo"
          hide-details
          class="me-2"
        />
        <v-checkbox-btn
          id="printItems28"
          v-model="selectedItems"
          label="비고"
          value="28"
          inline
          color="indigo"
          hide-details
          class="me-2"
        />
      </v-row>
    </v-container>
  </CCollapse>
</template>

<style lang="scss" scoped>
:deep(.my-checkbox .v-label) {
  font-size: 1em !important;
}
</style>
