<script lang="ts" setup>
import { ref, watch, onMounted } from 'vue'

const props = defineProps({
  unitSet: { type: Boolean, default: false },
  visible: { type: Boolean, default: false },
})

const printItems = ref(['1', '3', '4', '5', '8', '12', '13'])
const emit = defineEmits(['print-items'])

watch(printItems, newVal => {
  emit('print-items', newVal)
})

watch(props, val => {
  if (val.unitSet && !printItems.value.includes('6-7')) printItems.value.splice(4, 0, '6-7')
})

onMounted(() => {
  if (props.unitSet && !printItems.value.includes('6-7')) printItems.value.splice(4, 0, '6-7')
})
</script>

<template>
  <CCollapse :visible="visible" class="bg-grey-lighten-4">
    <v-container class="m-0" fluid>
      <v-row class="my-checkbox d-flex py-2">
        <v-checkbox-btn
          id="printItems1"
          v-model="printItems"
          label="일련번호"
          value="1"
          inline
          color="grey"
          readonly
          hide-details
          class="mr-2"
        />
        <v-checkbox-btn
          id="printItems2"
          v-model="printItems"
          label="등록상태"
          value="2"
          inline
          color="indigo"
          hide-details
          class="mr-2"
        />
        <v-checkbox-btn
          id="printItems3"
          v-model="printItems"
          label="차수"
          value="3"
          inline
          color="indigo"
          hide-details
          class="mr-2"
        />
        <v-checkbox-btn
          id="printItems4"
          v-model="printItems"
          label="타입"
          value="4"
          inline
          color="indigo"
          hide-details
          class="mr-2"
        />
        <v-checkbox-btn
          id="printItems5"
          v-model="printItems"
          label="계약자"
          value="5"
          inline
          color="indigo"
          hide-details
          class="mr-2"
        />
        <v-checkbox-btn
          v-if="unitSet"
          id="printItems6"
          v-model="printItems"
          label="동호수"
          value="6-7"
          inline
          color="indigo"
          hide-details
          class="mr-2"
        />
        <v-checkbox-btn
          id="printItems8"
          v-model="printItems"
          label="계약일자"
          value="8"
          inline
          color="indigo"
          hide-details
          class="mr-2"
        />
        <v-checkbox-btn
          id="printItems9"
          v-model="printItems"
          label="건물가"
          value="9"
          inline
          color="indigo"
          hide-details
          class="mr-2"
        />
        <v-checkbox-btn
          id="printItems9"
          v-model="printItems"
          label="대지가"
          value="10"
          inline
          color="indigo"
          hide-details
          class="mr-2"
        />
        <v-checkbox-btn
          id="printItems9"
          v-model="printItems"
          label="부가세"
          value="11"
          inline
          color="indigo"
          hide-details
          class="mr-2"
        />
        <v-checkbox-btn
          id="printItems9"
          v-model="printItems"
          label="공급가액"
          value="12"
          inline
          color="indigo"
          hide-details
          class="mr-2"
        />
        <v-checkbox-btn
          id="printItems10"
          v-model="printItems"
          label="납입금합계"
          value="13"
          inline
          color="indigo"
          hide-details
          class="mr-2"
        />
        <v-checkbox-btn
          id="printItems11"
          v-model="printItems"
          label="회당계약금"
          value="14"
          inline
          color="indigo"
          hide-details
          class="mr-2"
        />
        <v-checkbox-btn
          id="printItems12"
          v-model="printItems"
          label="회당중도금"
          value="15"
          inline
          color="indigo"
          hide-details
          class="mr-2"
        />
        <v-checkbox-btn
          id="printItems13"
          v-model="printItems"
          label="회당잔금"
          value="16"
          inline
          color="indigo"
          hide-details
          class="mr-2"
        />

        <v-checkbox-btn
          id="printItems14"
          v-model="printItems"
          label="생년월일"
          value="17"
          inline
          color="indigo"
          hide-details
          class="mr-2"
        />
        <v-checkbox-btn
          id="printItems15"
          v-model="printItems"
          label="연락처[1]"
          value="18"
          inline
          color="indigo"
          hide-details
          class="mr-2"
        />
        <v-checkbox-btn
          id="printItems16"
          v-model="printItems"
          label="연락처[2]"
          value="19"
          inline
          color="indigo"
          hide-details
          class="mr-2"
        />
        <v-checkbox-btn
          id="printItems17"
          v-model="printItems"
          label="연락처[3]"
          value="20"
          inline
          color="indigo"
          hide-details
          class="mr-2"
        />
        <v-checkbox-btn
          id="printItems18"
          v-model="printItems"
          label="이메일"
          value="21"
          inline
          color="indigo"
          hide-details
          class="mr-2"
        />
        <v-checkbox-btn
          id="printItems19"
          v-model="printItems"
          label="주소[등본]"
          value="22-23-24-25"
          inline
          color="indigo"
          hide-details
          class="mr-2"
        />
        <v-checkbox-btn
          id="printItems23"
          v-model="printItems"
          label="주소[우편]"
          value="26-27-28-29"
          inline
          color="indigo"
          hide-details
          class="mr-2"
        />
        <v-checkbox-btn
          id="printItems27"
          v-model="printItems"
          label="비고"
          value="30"
          inline
          color="indigo"
          hide-details
          class="mr-2"
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
