<script lang="ts" setup>
import { ref } from 'vue'
import Comment from './Comment.vue'

const msg = ref('CommentList')
</script>

<template>
  <h6>댓글</h6>

  <Comment />

  <CRow>
    <CCol>
      <router-link to="">댓글 추가</router-link>
    </CCol>
  </CRow>
</template>
