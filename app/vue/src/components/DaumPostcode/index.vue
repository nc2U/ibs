<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { type AddressData } from '@/components/DaumPostcode/address'
import { useStore } from '@/store'

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
    default: '//t1.daumcdn.net/mapjsapi/bundle/postcode/prod/postcode.v2.js',
  },
})

const emit = defineEmits(['address-callback'])

const element_layer = ref()
const displayVal = ref('none')

const widthVal = computed(() => props.width + 'px')
const heightVal = computed(() => props.height + 'px')
const borderVal = computed(() => props.borderWidth + 'px solid')
const leftVal = computed(
  () =>
    ((window.innerWidth || document.documentElement.clientWidth) - props.width) / 2 -
    props.borderWidth +
    'px',
)
const topVal = computed(
  () =>
    ((window.innerHeight || document.documentElement.clientHeight) - props.height) / 2 -
    props.borderWidth +
    'px',
)
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
  ;(window as any).daum.postcode // { daum: { postcode: { load: (p: () => void) => void } } }
    .load(() => {
      new // {
      //     daum: {
      //       Postcode: (p: {
      //         hideMapBtn: boolean | undefined
      //         maxSuggestItems: number | undefined
      //         pleaseReadGuideTimer: number | undefined
      //         showMoreHName: boolean | undefined
      //         alwaysShowEngAddr: boolean | undefined
      //         submitMode: boolean | undefined
      //         autoResize: boolean | undefined
      //         shorthand: boolean | undefined
      //         hideEngBtn: boolean | undefined
      //         animation: boolean | undefined
      //         useSuggest: boolean | undefined
      //         pleaseReadGuide: number | undefined
      //         width: string
      //         theme: { searchBgColor: string; queryTextColor: string } | null
      //         oncomplete: (data: AddressData) => void
      //         autoMapping: boolean | undefined
      //         height: string
      //       }) => void
      //     }
      //   }
      (window as any).daum.Postcode({
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
      }).embed(element_layer.value)

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
      left: leftVal,
      top: topVal,
    }"
  >
    <img
      id="btnCloseLayer"
      src="//t1.daumcdn.net/postcode/resource/images/close.png"
      alt="닫기 버튼"
      @click="closeLayer"
    />
  </div>
</template>

<style lang="scss" scoped>
#layer {
  position: fixed;
  overflow: hidden;
  z-index: 100;
  -webkit-overflow-scrolling: touch;
}

#btnCloseLayer {
  cursor: pointer;
  position: absolute;
  right: -3px;
  top: -3px;
  z-index: 100;
}
</style>
