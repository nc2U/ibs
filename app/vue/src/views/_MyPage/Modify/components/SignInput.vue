<script lang="ts" setup>
import { ref, onMounted, watch } from 'vue'

const props = withDefaults(
  defineProps<{
    image?: string | File | null
    signType?: 'STAMP' | 'SIGN'
  }>(),
  {
    image: null,
    signType: 'STAMP',
  },
)

const emit = defineEmits(['update:image', 'update:signType'])

const fileInput = ref<HTMLInputElement>()
const previewSrc = ref<string>('')
const selectedType = ref<'STAMP' | 'SIGN'>(props.signType)

const browse = () => {
  fileInput.value?.click()
}

const onFileChange = (e: Event) => {
  const target = e.target as HTMLInputElement
  if (target.files && target.files[0]) {
    const file = target.files[0]
    emit('update:image', file)

    const reader = new FileReader()
    reader.onload = evt => {
      previewSrc.value = String(evt.target?.result || '')
    }
    reader.readAsDataURL(file)
  }
}

const onTypeChange = (type: 'STAMP' | 'SIGN') => {
  selectedType.value = type
  emit('update:signType', type)
}

watch(
  () => props.image,
  val => {
    if (typeof val === 'string') {
      previewSrc.value = val
    } else if (!val) {
      previewSrc.value = ''
    }
  },
)

watch(
  () => props.signType,
  val => {
    if (val) selectedType.value = val
  },
)

onMounted(() => {
  if (typeof props.image === 'string') {
    previewSrc.value = props.image
  }
})
</script>

<template>
  <div class="sign-input-wrapper">
    <input
      ref="fileInput"
      type="file"
      class="d-none"
      accept="image/png, image/jpeg, image/gif, image/webp"
      @change="onFileChange"
    />

    <CRow class="align-items-center">
      <CCol xs="auto">
        <div
          class="sign-preview-box border rounded d-flex align-items-center justify-content-center bg-light"
          @click="browse"
        >
          <img
            v-if="previewSrc"
            :src="previewSrc"
            alt="Sign/Stamp"
            class="sign-preview-img"
          />
          <div v-else class="text-center text-muted p-2">
            <CIcon name="cilPencil" size="xl" class="mb-1" />
            <div class="small">인장/서명 등록</div>
          </div>
        </div>
      </CCol>

      <CCol>
        <div class="mb-2">
          <div class="form-check form-check-inline">
            <input
              id="signTypeStamp"
              v-model="selectedType"
              class="form-check-input"
              type="radio"
              value="STAMP"
              @change="onTypeChange('STAMP')"
            />
            <label class="form-check-label" for="signTypeStamp">도장 (인장)</label>
          </div>
          <div class="form-check form-check-inline">
            <input
              id="signTypeSign"
              v-model="selectedType"
              class="form-check-input"
              type="radio"
              value="SIGN"
              @change="onTypeChange('SIGN')"
            />
            <label class="form-check-label" for="signTypeSign">사인 (서명)</label>
          </div>
        </div>

        <div>
          <v-btn size="small" variant="outlined" color="primary" class="me-2" @click="browse">
            이미지 선택
          </v-btn>
          <span class="text-muted small">
            * 배경이 투명한 PNG 이미지 권장 (정사각형/원형 인장 권장)
          </span>
        </div>
        <div class="text-muted small mt-1">
          * 전자결재 승인 시 결재란에 날인될 개인 인장/서명입니다. 미등록 시 시스템 기본 도장으로 자동 날인됩니다.
        </div>
      </CCol>
    </CRow>
  </div>
</template>

<style scoped>
.sign-preview-box {
  width: 90px;
  height: 90px;
  cursor: pointer;
  overflow: hidden;
  position: relative;
  transition: border-color 0.2s;
}

.sign-preview-box:hover {
  border-color: #0d6efd !important;
}

.sign-preview-img {
  max-width: 80px;
  max-height: 80px;
  object-fit: contain;
}
</style>
