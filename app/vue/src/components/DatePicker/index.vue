<script lang="ts" setup>
import { ref, computed } from 'vue'
import { useStore } from '@/store'
import { vMaska } from 'maska/vue'
import Datepicker from '@vuepic/vue-datepicker'

defineProps({
  disabled: { type: Boolean, default: false },
  readonly: { type: Boolean, default: false },
  required: { type: Boolean, default: false },
  placeholder: { type: String, default: '날짜선택' },
})

const store = useStore()
const isDark = computed(() => store.theme === 'dark')

const options = ref({ format: 'yyyy-MM-dd' })
</script>

<template>
  <Datepicker
    :dark="isDark"
    :teleport="true"
    :enable-time-picker="false"
    :text-input="options"
    auto-apply
    locale="ko"
    position="left"
    model-type="format"
    format="yyyy-MM-dd"
    allow-prevent-default
  >
    <template #input-icon>
      <v-icon icon="mdi mdi-calendar-blank-outline" class="m-1" size="14" />
    </template>
    <template #dp-input="{ value, onInput, onEnter, onTab, onBlur, onPaste }">
      <input
        v-maska
        :value="value"
        :disabled="disabled"
        :readonly="readonly"
        :required="required"
        :placeholder="placeholder"
        autocomplete="off"
        data-maska="####-##-##"
        aria-label="Datepicker input"
        class="form-control dp__input dp__input_icon_pad"
        style="padding-left: 18px"
        @keydown.enter="onEnter"
        @keydown.tab="onTab"
        @keydown="onInput"
        @keyup="onInput"
        @paste="onPaste"
        @blur="onBlur"
      />
    </template>
  </Datepicker>
</template>
