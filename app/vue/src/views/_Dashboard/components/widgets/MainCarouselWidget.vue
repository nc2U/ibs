<script setup lang="ts">
import WidgetWrapper from '../WidgetWrapper.vue'

defineProps<{
  widgetId: string
  title: string
  icon?: string
}>()

const imgSrc = [
  'https://kr.object.iwinv.kr/ibs/media%2Fcarousel/001.jpg',
  'https://kr.object.iwinv.kr/ibs/media%2Fcarousel/002.jpg',
  'https://kr.object.iwinv.kr/ibs/media%2Fcarousel/003.jpg',
  'https://kr.object.iwinv.kr/ibs/media%2Fcarousel/004.jpg',
  'https://kr.object.iwinv.kr/ibs/media%2Fcarousel/007.jpg',
  'https://kr.object.iwinv.kr/ibs/media%2Fcarousel/008.jpg',
  'https://kr.object.iwinv.kr/ibs/media%2Fcarousel/009.jpg',
  'https://kr.object.iwinv.kr/ibs/media%2Fcarousel/010.jpg',
]
</script>

<template>
  <WidgetWrapper :widget-id="widgetId" :title="title" :icon="icon">
    <div class="carousel-widget">
      <v-carousel cycle height="100%" delimiter-icon="mdi-square" show-arrows="hover">
        <v-carousel-item v-for="(img, i) in imgSrc" :key="i" :src="img" cover />
      </v-carousel>
    </div>
  </WidgetWrapper>
</template>

<style scoped>
.carousel-widget {
  height: 100%;
  min-height: 120px;
}

.carousel-widget :deep(.v-carousel) {
  border-radius: 4px;
  overflow: hidden;
}
</style>
