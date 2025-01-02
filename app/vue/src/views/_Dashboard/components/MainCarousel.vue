<script lang="ts" setup>
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
  <CCard class="mb-4" xxl="9">
    <CCardBody>
      <v-carousel cycle height="400" delimiter-icon="mdi-square" show-arrows="hover">
        <v-carousel-item v-for="(img, i) in imgSrc" :key="i" :src="img" cover />
      </v-carousel>
    </CCardBody>
  </CCard>
</template>
