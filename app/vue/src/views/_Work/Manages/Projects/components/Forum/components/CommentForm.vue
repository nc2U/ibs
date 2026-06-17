<script lang="ts" setup>
import { ref } from 'vue'
import MdEditor from '@/components/MdEditor/Index.vue'

const props = defineProps({
  content: { type: String, default: '' },
})

const emit = defineEmits(['submit-comment', 'cancel'])

const commentContent = ref(props.content)

const onSubmit = () => {
  if (commentContent.value.trim()) {
    emit('submit-comment', commentContent.value)
    commentContent.value = ''
  }
}
</script>

<template>
  <div class="comment-form">
    <MdEditor
      v-model="commentContent"
      placeholder="댓글을 입력하세요"
      style="height: 150px"
      class="mb-2"
    />
    <div class="text-right">
      <v-btn
        :color="content ? 'success' : 'primary'"
        size="small"
        variant="flat"
        :disabled="!commentContent.trim()"
        @click="onSubmit"
        class="mr-2"
      >
        {{ content ? '수정' : '등록' }}
      </v-btn>
      <v-btn v-if="content" variant="text" size="small" @click="emit('cancel')">취소</v-btn>
    </div>
  </div>
</template>
