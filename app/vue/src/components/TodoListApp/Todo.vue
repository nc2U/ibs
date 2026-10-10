<script setup lang="ts">
import { type PropType, ref, watch, nextTick } from 'vue'
import type { Todo } from '@/store/types/accounts'

const props = defineProps({
  todo: { type: Object as PropType<Todo>, required: true },
})

const emit = defineEmits(['delTodo', 'editTodo', 'toggleTodo'])

const editInput = ref()
const editing = ref(false)

watch(editing, val => {
  if (val) nextTick(() => editInput.value.focus())
})

const delTodo = (pk: number | undefined) => {
  if (!!pk) emit('delTodo', pk)
}

const editTodo = (pk: number, title: string) => {
  if (props.todo?.title !== title) emit('editTodo', pk, title)
  else return
}

const toggleTodo = (todo: Todo) => emit('toggleTodo', todo)

const doneEdit = (e: Event) => {
  if (!editing.value) return
  const title = (e.target as HTMLInputElement).value.trim()
  if (!title && props.todo?.pk) delTodo(props.todo.pk)
  else if (props.todo?.pk) editTodo(props.todo.pk, title)
  editing.value = false
}

const cancelEdit = (e: Event) => {
  editing.value = false
  ;(e.target as HTMLInputElement).value = props.todo?.title || ''
}
</script>

<template>
  <li :class="{ completed: todo.completed, editing: editing }" class="todo">
    <div class="view">
      <input :checked="todo.completed" class="toggle" type="checkbox" @change="toggleTodo(todo)" />
      <label @dblclick="editing = true" v-text="todo.title" />
      <button class="destroy" @click="delTodo(todo.pk)" />
    </div>
    <input
      v-show="editing"
      ref="editInput"
      :value="todo.title"
      class="edit"
      @keyup.enter="doneEdit"
      @keyup.esc="cancelEdit"
      @blur="doneEdit"
    />
  </li>
</template>
