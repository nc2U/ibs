<script lang="ts" setup>
import { inject, ref } from 'vue'
import MultiSelect from '@/components/MultiSelect/index.vue'

const getContracts = inject('getContracts')
</script>

<template>
  <MultiSelect mode="single" :options="getContracts" placeholder="계약 정보 선택" />
</template>
