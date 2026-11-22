<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { type AddressData } from '@/components/DaumPostcode/address'
import { useStore } from '@/store'
import { message } from '@/utils/helper'

interface DaumPostcodeOptions {
  oncomplete: (data: AddressData) => void
  alwaysShowEngAddr?: boolean
  animation?: boolean
  autoMapping?: boolean
  autoResize?: boolean
  hideEngBtn?: boolean
  hideMapBtn?: boolean
  maxSuggestItems?: number
  pleaseReadGuide?: number
  pleaseReadGuideTimer?: number
  shorthand?: boolean
  showMoreHName?: boolean
  submitMode?: boolean
  theme?: { searchBgColor: string; queryTextColor: string } | null
  useSuggest?: boolean
  width?: string
  height?: string
}

interface DaumPostcodeInstance {
  embed: (el: HTMLElement | undefined, options?: { q?: string }) => void
}

interface DaumPostcodeWindow extends Window {
  daum?: {
    postcode?: { load: (cb: () => void) => void }
    Postcode?: new (options: DaumPostcodeOptions) => DaumPostcodeInstance
  }
}

const store = useStore()

const props = defineProps({
  width: { type: Number, default: 450 },
  height: { type: Number, default: 415 },
  borderWidth: { type: Number, default: 5 },
  autoClose: { type: Boolean, default: false },
  autoResize: { type: Boolean, default: false },
  animation: { type: Boolean, default: false },
  autoMapping: { type: Boolean, default: true },
  shorthand: { type: Boolean, default: true },
  pleaseReadGuide: { type: Number, default: 0 },
  pleaseReadGuideTimer: { type: Number, default: 1.5 },
  maxSuggestItems: { type: Number, default: 8 },
  showMoreHName: { type: Boolean, default: false },
  hideMapBtn: { type: Boolean, default: false },
  hideEngBtn: { type: Boolean, default: false },
  alwaysShowEngAddr: { type: Boolean, default: false },
  submitMode: { type: Boolean, default: true },
  useSuggest: { type: Boolean, default: true },
  componentStyle: { type: Object, default: null },
  defaultQuery: { type: String, default: null },
  scriptUrl: {
    type: String,
    default: '//t1.kakaocdn.net/mapjsapi/bundle/postcode/prod/postcode.v2.js',
  },
})

const emit = defineEmits(['address-callback'])

const element_layer = ref<HTMLElement>()
const displayVal = ref('none')

const widthVal = computed(() => props.width + 'px')
const heightVal = computed(() => props.height + 'px')
const borderVal = computed(() => props.borderWidth + 'px solid')

const theme = computed(() => {
  if (store.theme === 'dark') {
    return {
      searchBgColor: '#2A2B36', //검색창 배경색
      queryTextColor: '#FFFFFF', //검색창 글자색
    }
  } else {
    return null
  }
})

const initiate = (formNum = 1) => {
  const win = window as DaumPostcodeWindow
  const postcodeApi = win.daum?.postcode
  if (!postcodeApi) {
    message('warning', '안내', '주소 검색 스크립트를 불러오는 중입니다. 잠시 후 다시 시도해주세요.')
    return
  }

  postcodeApi.load(() => {
    const PostcodeCtor = (window as DaumPostcodeWindow).daum?.Postcode
    if (!PostcodeCtor) return

    new PostcodeCtor({
      oncomplete: function oncomplete(data: AddressData) {
        emit('address-callback', { ...{ formNum }, ...data })
        displayVal.value = 'none'
      },
      alwaysShowEngAddr: props.alwaysShowEngAddr,
      animation: props.animation,
      autoMapping: props.autoMapping,
      autoResize: props.autoResize,
      hideEngBtn: props.hideEngBtn,
      hideMapBtn: props.hideMapBtn,
      maxSuggestItems: props.maxSuggestItems,
      pleaseReadGuide: props.pleaseReadGuide,
      pleaseReadGuideTimer: props.pleaseReadGuideTimer,
      shorthand: props.shorthand,
      showMoreHName: props.showMoreHName,
      submitMode: props.submitMode,
      theme: theme.value,
      useSuggest: props.useSuggest,
      width: '100%',
      height: '100%',
    }).embed(element_layer.value, props.defaultQuery ? { q: props.defaultQuery } : undefined)

    displayVal.value = 'block'
  })
}

defineExpose({ initiate })

const closeLayer = () => (displayVal.value = 'none')

onMounted(() => {
  const scriptId = 'daum_postcode_script'
  const isExist = !!document.getElementById(scriptId)
  if (!isExist) {
    const script = document.createElement('script')
    script.src = props.scriptUrl as string
    script.id = scriptId
    document.body.appendChild(script)
  }
})
</script>

<template>
  <div
    id="layer"
    ref="element_layer"
    :style="{
      display: displayVal,
      width: widthVal,
      height: heightVal,
      border: borderVal,
    }"
  >
    <img
      id="btnCloseLayer"
      src="//t1.kakaocdn.net/postcode/resource/images/close.png"
      alt="닫기 버튼"
      @click="closeLayer"
    />
  </div>
</template>

<style lang="scss" scoped>
#layer {
  position: fixed;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  max-width: 95vw;
  max-height: 90vh;
  overflow: hidden;
  z-index: 2500;
  -webkit-overflow-scrolling: touch;
}

#btnCloseLayer {
  cursor: pointer;
  position: absolute;
  right: -3px;
  top: -3px;
  z-index: 2501;
}
</style>
