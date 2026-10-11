<script setup lang="ts">
import { onMounted, ref } from 'vue'

const now = ref('加载中')
const error = ref('')

onMounted(async () => {
  try {
    const res = await fetch('/api/health')
    if (!res.ok) throw new Error(String(res.status))
    const data = await res.json()
    now.value = data.now
  } catch (e) {
    error.value = e instanceof Error ? e.message : '请求失败'
  }
})
</script>

<template>
  <main>
    <h1>求职作战台</h1>
    <p v-if="error">健康检查失败：{{ error }}</p>
    <p v-else>数据库时间：{{ now }}</p>
  </main>
</template>
