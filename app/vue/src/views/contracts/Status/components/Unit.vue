<script lang="ts" setup>
import { computed, inject, type PropType } from 'vue'
import { type SimpleUnit } from './ContractBoard.vue'

const props = defineProps({
  units: { type: Object as PropType<SimpleUnit[]>, default: null },
  unit: { type: Object as PropType<SimpleUnit>, required: true },
  floor: { type: Number, default: 1 },
  line: { type: Number, default: 1 },
  maxPiloti: { type: Number, default: 1 },
  firstLine: { type: Number, default: 1 },
})

const isContor = inject('isContor')

const isPiloti = computed(() => !props.unit && props.floor < props.maxPiloti)
const isContract = computed(() => !!props.unit?.key_unit?.contract)
const contorName = computed(() =>
  isContract.value ? props.unit.key_unit.contract?.contractor.name : '',
)
const contorPk = computed(() =>
  isContract.value ? props.unit.key_unit.contract?.contractor.pk : '',
)
const status = computed(() =>
  isContract.value ? props.unit.key_unit.contract?.contractor.status : '',
)
const isHold = computed(() => props.unit?.is_hold || '')
</script>

<template>
  <div class="unit">
    <div
      class="unit-name"
      :class="{
        firstClass: (isPiloti || unit) && line === firstLine,
        restClass: (isPiloti || unit) && line !== firstLine,
        piloti: isPiloti,
      }"
      :style="`background-color: ${unit ? unit.color : ''}`"
    >
      <span v-if="unit" style="color: #666">{{ unit.name }}</span>
    </div>

    <div
      class="status"
      :class="{
        firstClass: unit && line === firstLine,
        restClass: unit && line !== firstLine,
        firstPiloti: isPiloti && line === 1,
        restPiloti: isPiloti && line !== 1,
        piloti: isPiloti,
        back: unit && !status,
        app: status === '1',
        cont: status === '2',
        hold: isHold,
      }"
    >
      <span v-show="isContor">
        <span v-if="unit && unit.key_unit && unit.key_unit.contract">
          <router-link
            :to="{
              name: '계약 상세 보기',
              params: { contractorId: contorPk },
            }"
            class="dark-link"
          >
            {{ contorName }}
          </router-link>
        </span>
        <span v-if="isHold">
          HOLD
          <v-tooltip activator="parent" location="top">
            {{ unit.hold_reason }}
          </v-tooltip>
        </span>
      </span>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.unit {
  width: 40px;
  height: 40px;
  padding: 0;
  font-size: 10px;
  text-align: center;
  vertical-align: middle;
}

.unit-name {
  height: 20px;
  line-height: 20px;
  padding: 0;
}

.status {
  height: 20px;
  line-height: 20px;
  padding: 0;
}

.firstClass {
  border-width: 1px 1px 0 1px;
  border-style: solid;
  border-color: #999;
}

.firstPiloti {
  border-width: 0 1px 0 1px;
  border-style: solid;
  border-color: #999;
}

.restClass {
  border-width: 1px 1px 0 0;
  border-style: solid;
  border-color: #999;
}

.restPiloti {
  border-width: 0 1px 0 0;
  border-style: solid;
  border-color: #999;
}

.piloti {
  background-color: #bbb;
  border-color: #999;
}

$back: white;
$app: #ffff99;
$cont: #ddd;
$hold: #999;

.back {
  background: $back;
}

.app {
  background: $app;
}

.cont {
  background: $cont;
}

.hold {
  background: $hold;
}

.dark-theme {
  .app {
    background: darken($app, 20%);
  }

  .cont {
    background: darken($cont, 40%);
  }

  .hold {
    background: darken($hold, 20%);
  }

  .firstClass {
    border-color: #666;
  }

  .firstPiloti {
    border-color: #666;
  }

  .restClass {
    border-color: #666;
  }

  .restPiloti {
    border-color: #666;
  }

  .piloti {
    background-color: #777;
    border-color: #666;
  }
}
</style>
