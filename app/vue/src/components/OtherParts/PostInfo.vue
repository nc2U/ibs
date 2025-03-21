<script lang="ts" setup="">
import { type PropType } from 'vue'
import { toPrint } from '@/utils/docsMixins'
import { timeFormat } from '@/utils/baseMixins'
import type { Docs } from '@/store/types/docs'

defineProps({ docs: { type: Object as PropType<Docs>, required: true } })
</script>

<template>
  <CRow class="text-blue-grey mb-5">
    <CCol>
      <small class="mr-3">작성자 : {{ docs.user?.username }}</small>
      <small class="mr-2">
        <v-icon icon="mdi-eye" size="sm" />
        <span class="ml-1">{{ docs.hit }}</span>
      </small>
      <!--      <small class="mr-2">-->
      <!--        <v-icon icon="mdi-heart" size="sm" />-->
      <!--        <span class="ml-1">{{ docs.like }}</span>-->
      <!--      </small>-->
      <small class="mr-2 text-btn" @click="toPrint(docs.title)">
        <v-icon icon="mdi-printer" size="sm" />
        <span class="ml-1">프린트</span>
      </small>
    </CCol>

    <CCol class="text-right" md="3">
      <small>
        <v-icon icon="mdi-calendar-clock" size="small" />
        <span class="ml-2">{{ timeFormat(docs.created ?? '') }}</span>
      </small>
    </CCol>
  </CRow>
</template>
