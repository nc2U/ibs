<script lang="ts">
import { defineComponent, ref, watch } from 'vue'
import { CircleStencil, Cropper } from 'vue-advanced-cropper'
import 'vue-advanced-cropper/dist/style.css'
import 'vue-advanced-cropper/dist/theme.compact.css'

export default defineComponent({
  name: 'CropperModal',
  components: { CircleStencil, Cropper },
  props: {
    modalImg: { type: String, default: undefined },
  },
  emits: ['image-del', 'trans-avatar-input'],
  setup(props, ctx) {
    const visible = ref(false)
    const cropper = ref()

    const close = () => {
      ctx.emit('image-del')
      visible.value = false
    }

    const crop = () => {
      const { canvas } = cropper.value.getResult()
      if (canvas) {
        canvas.toBlob((blob: Blob) => {
          const img = new File([blob], 'profile.png', { type: blob.type })
          ctx.emit('trans-avatar-input', img)
        })
      }
      close()
    }

    watch(visible, val => {
      if (!val) close()
    })

    return {
      visible,
      cropper,
      close,
      crop,
    }
  },
})
</script>

<template>
  <CModal :visible="visible" @close="() => close">
    <CModalHeader :close-button="false">
      <CModalTitle component="h6"> Crop your new profile picture</CModalTitle>
      <v-btn type="button" aria-label="Close" class="btn btn-close" @click="close" />
    </CModalHeader>
    <CModalBody>
      <cropper
        ref="cropper"
        class="cropper"
        :stencil-component="$options.components?.CircleStencil"
        :default-size="{
          width: 1000,
          height: 1000,
        }"
        :src="modalImg"
      />
    </CModalBody>
    <CModalFooter class="d-grid gap-2">
      <v-btn color="success" @click="crop"> Set new profile picture</v-btn>
    </CModalFooter>
    <CircleStencil v-if="false" />
  </CModal>
</template>

<style lang="scss" scoped>
.cropper {
  height: 320px;
  width: 470px;
  background: #ddd;
}

.line {
  border-style: dashed;
  border-color: red;
}
</style>
