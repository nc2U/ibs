<script lang="ts" setup>
import { computed } from 'vue'
import { useStore } from '@/store'
import Datepicker from '@vuepic/vue-datepicker'

const model = defineModel<string>()

defineProps({
  disabled: { type: Boolean, default: false },
  readonly: { type: Boolean, default: false },
  required: { type: Boolean, default: false },
  placeholder: { type: String, default: '시간선택' },
})

const store = useStore()
const isDark = computed(() => store.theme === 'dark')

// 12시간 형식으로 표시하기 위한 포맷 함수
const formatTime = (time: string | null): string => {
  if (!time) return ''
  const match = /^(\d{1,2}):(\d{2})/.exec(time.trim())
  if (!match) return time
  const hour = Number(match[1])
  const minutes = match[2]
  if (Number.isNaN(hour)) return time
  const ampm = hour >= 12 ? '오후' : '오전'
  const displayHour = hour % 12 || 12

  return `${ampm} ${displayHour.toString().padStart(2, '0')}:${minutes}`
}
</script>

<template>
  <Datepicker
    v-model="model"
    :dark="isDark"
    :teleport="true"
    :disabled="disabled"
    :readonly="readonly"
    time-picker
    auto-apply
    locale="ko"
    position="left"
    model-type="HH:mm"
    allow-prevent-default
  >
    <template #input-icon>
      <v-icon icon="mdi-clock-outline" class="m-1" size="14" />
    </template>
    <template #dp-input="{ value, onEnter, onTab, onBlur }">
      <input
        :value="formatTime(value)"
        :disabled="disabled"
        readonly
        :required="required"
        :placeholder="placeholder"
        autocomplete="off"
        aria-label="Time picker input"
        class="form-control dp__input dp__input_icon_pad"
        style="padding-left: 20px"
        @keydown.enter="onEnter"
        @keydown.tab="onTab"
        @blur="onBlur"
      />
    </template>
  </Datepicker>
</template>
