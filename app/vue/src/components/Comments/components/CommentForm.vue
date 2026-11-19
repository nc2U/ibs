<script lang="ts" setup>
import { reactive, onMounted, watch, type PropType } from 'vue'
import type { Comment as Cm } from '@/store/types/forum'

const props = defineProps({
  post: { type: Number, required: true },
  comment: { type: Object as PropType<Cm>, default: null },
  parent: { type: Number, default: null },
})
const emit = defineEmits(['on-submit'])

const form = reactive<any>({
  pk: undefined,
  post: props.post,
  content: '',
  parent: props.parent,
  secret: false,
})

const onSubmit = () => {
  if (!form.content?.trim()) return
  emit('on-submit', { ...form, post: props.post })
  formReset()
}

const formReset = () => {
  form.pk = undefined
  form.post = props.post
  form.content = ''
  form.parent = props.parent
  form.secret = false
}

const formSet = () => {
  form.post = props.post
  if (props.comment) {
    form.pk = props.comment.pk
    form.content = props.comment.content
    form.parent = props.comment.parent
    form.secret = props.comment.secret
  } else {
    formReset()
  }
}

watch(
  [() => props.comment, () => props.post, () => props.parent],
  () => formSet(),
  { deep: true },
)

onMounted(() => formSet())
</script>

<template>
  <v-form class="p-4 bg-more-light" @submit.prevent="onSubmit">
    <v-container fluid class="m-0 p-0">
      <v-textarea
        label="comment"
        v-model="form.content"
        auto-grow
        variant="outlined"
        rows="3"
        row-height="25"
        color="grey-lighten-1"
        base-color="grey-lighten-1"
        bg-color="white"
        shaped
        required
      />
      <v-row>
        <v-checkbox
          label="비밀댓글"
          v-model="form.secret"
          density="compact"
          hide-details
          class="m-3 pt-1 text-muted text-caption"
        />
        <span
          v-if="form.secret"
          class="text-end text-muted text-caption"
          style="padding-top: 30px"
        >
          비밀댓글은 관리자와 작성자만 볼 수 있습니다.
        </span>

        <v-col class="text-end pt-3">
          <v-btn
            type="submit"
            :color="!comment ? 'primary' : 'success'"
            tonal
            size="large"
            :disabled="!form.content"
          >
            댓글등록
          </v-btn>
        </v-col>
      </v-row>
    </v-container>
  </v-form>
</template>
