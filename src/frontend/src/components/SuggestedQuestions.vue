<template>
  <div class="suggestions">
    <div class="suggestion-title">Try asking:</div>
    <div class="suggestion-grid">
      <el-tag 
        v-for="q in questions" 
        :key="q" 
        class="suggestion-item" 
        effect="dark"
        @click="$emit('select', q)"
      >
        {{ q }}
      </el-tag>
    </div>
  </div>
</template>

<script setup lang="ts">
const questions = [
  "Stars trend of vuejs/core",
  "Compare react vs vuejs/core activity",
  "What is the openrank of tensorflow/tensorflow?",
  "Show me issues_new for fastapi/fastapi"
];
defineEmits(['select']);
</script>

<style scoped>
.suggestions { margin-top: 20px; text-align: center; }
.suggestion-title { color: #666; font-size: 0.8rem; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 1px; }
.suggestion-grid { display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; }
.suggestion-item { cursor: pointer; transition: all 0.2s; background-color: #1c2533; border-color: #30363d; color: #a5d6ff; }
.suggestion-item:hover { transform: scale(1.05); background-color: #00bcd4; border-color: #00bcd4; color: #fff; }
</style>
