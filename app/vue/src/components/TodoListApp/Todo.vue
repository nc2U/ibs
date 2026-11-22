<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import type { Todo } from '@/store/types/accounts.ts'

const props = defineProps<{
  todo: Todo
}>()

const emit = defineEmits<{
  (e: 'del-todo', pk: number): void
  (e: 'edit-todo', pk: number, title: string): void
  (e: 'toggle-todo', todo: Todo): void
  (e: 'convert-todo', todo: Todo): void
}>()

const editInput = ref<HTMLInputElement>()
const editing = ref(false)

watch(editing, val => {
  if (val) nextTick(() => editInput.value?.focus())
})

const delTodo = (pk: number | undefined) => {
  if (pk) emit('del-todo', pk)
}

const editTodo = (pk: number, title: string) => {
  if (props.todo.title !== title) emit('edit-todo', pk, title)
}

const toggleTodo = (todo: Todo) => emit('toggle-todo', todo)

const doneEdit = (e: Event) => {
  if ((e as KeyboardEvent).isComposing || !editing.value) return
  const input = e.target as HTMLInputElement
  const title = input.value.trim()
  if (!title && props.todo.pk) delTodo(props.todo.pk)
  else if (props.todo.pk) editTodo(props.todo.pk, title)
  editing.value = false
}

const cancelEdit = (e: Event) => {
  editing.value = false
  const input = e.target as HTMLInputElement
  input.value = props.todo.title || ''
}
</script>

<template>
  <li :class="{ completed: todo.completed, editing: editing }" class="todo">
    <div class="view">
      <input :checked="todo.completed" class="toggle" type="checkbox" @change="toggleTodo(todo)" />
      <label @dblclick="editing = true">
        {{ todo.title }}
        <router-link
          v-if="todo.issue_info"
          :to="{
            name: '(업무) - 보기',
            params: {
              projId: todo.issue_info.project_slug || todo.issue_info.project_id,
              issueId: todo.issue_info.pk,
            },
          }"
          class="badge text-bg-primary text-decoration-none ms-2 align-middle issue-badge"
          :title="`[${todo.issue_info.project_name}] ${todo.issue_info.subject}`"
          @click.stop
        >
          #{{ todo.issue_info.pk }}
        </router-link>
        <span v-else-if="todo.issue" class="badge text-bg-secondary ms-2 align-middle issue-badge">
          #{{ todo.issue }}
        </span>
      </label>
      <button
        v-if="!todo.issue"
        type="button"
        class="convert-btn"
        title="업무로 전환"
        @click.stop="emit('convert-todo', todo)"
      >
        <v-icon icon="mdi-transfer-right" size="18" />
      </button>
      <button class="destroy" title="삭제" @click="delTodo(todo.pk)" />
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
