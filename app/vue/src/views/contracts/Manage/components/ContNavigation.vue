<script lang="ts" setup>
import { computed, inject } from 'vue'
import { useRoute, useRouter } from 'vue-router'

defineProps({
  contOn: { type: Boolean, default: false },
  contractor: { type: Number, default: null },
})

const [route, router] = [useRoute(), useRouter()]

const isDark = inject('isDark')

const isRegister = computed(
  () => route.name === '계약 상세 관리' || route.name === '계약 상세 보기',
)
const isSuccession = computed(
  () => route.name === '권리 의무 승계' || route.name === '권리 의무 승계 보기',
)
const isRelease = computed(() => route.name === '계약 해지 관리' || route.name === '계약 해지 보기')
</script>

<template>
  <v-btn-group density="compact" role="group" aria-label="Basic example" class="mb-3">
    <v-btn
      :color="isRegister ? 'primary' : 'light'"
      :variant="isRegister || !isDark ? 'elevated' : 'tonal'"
      :disabled="!contOn || !contractor"
      @click="
        router.push({
          name: '계약 상세 보기',
          params: { contractorId: contractor },
        })
      "
    >
      계약 상세 관리
    </v-btn>
    <v-btn
      :color="isSuccession ? 'success' : 'light'"
      :variant="isSuccession || !isDark ? 'elevated' : 'tonal'"
      :disabled="!contOn || !contractor"
      @click="
        router.push({
          name: '권리 의무 승계 보기',
          params: { contractorId: contractor },
        })
      "
    >
      권리 의무 승계
    </v-btn>
    <v-btn
      :color="isRelease ? 'warning' : 'light'"
      :variant="isRelease || !isDark ? 'elevated' : 'tonal'"
      :disabled="!contractor"
      @click="
        router.push({
          name: '계약 해지 보기',
          params: { contractorId: contractor },
        })
      "
    >
      계약 해지 관리
    </v-btn>
  </v-btn-group>
</template>
