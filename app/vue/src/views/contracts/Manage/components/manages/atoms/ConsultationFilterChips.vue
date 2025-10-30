<script lang="ts" setup>
// Props
const props = defineProps<{
  modelValue: string
}>()

// Events
const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

// 필터 변경
const setFilter = (value: string) => {
  emit('update:modelValue', value)
}
</script>

<template>
  <div class="mb-3 d-flex gap-2">
    <v-chip
      :color="props.modelValue === '' ? 'primary' : 'default'"
      @click="setFilter('')"
      size="small"
    >
      전체
    </v-chip>
    <v-chip
      :color="props.modelValue === '1' ? 'warning' : 'default'"
      @click="setFilter('1')"
      size="small"
    >
      처리대기
    </v-chip>
    <v-chip
      :color="props.modelValue === '2' ? 'primary' : 'default'"
      @click="setFilter('2')"
      size="small"
    >
      처리중
    </v-chip>
    <v-chip
      :color="props.modelValue === '3' ? 'success' : 'default'"
      @click="setFilter('3')"
      size="small"
    >
      처리완료
    </v-chip>
    <v-chip
      :color="props.modelValue === '4' ? 'secondary' : 'default'"
      @click="setFilter('4')"
      size="small"
    >
      보류
    </v-chip>
  </div>
</template>
