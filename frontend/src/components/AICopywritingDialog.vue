<template>
  <el-dialog
    :model-value="visible"
    title="生成分享文案"
    width="480px"
    :close-on-click-modal="false"
    @update:model-value="$emit('update:visible', $event)"
    @open="handleOpen"
  >
    <!-- 加载中 -->
    <div v-if="loading" class="copywriting-loading">
      <el-skeleton :rows="5" animated />
    </div>

    <!-- 错误状态 -->
    <el-result
      v-else-if="errorMsg"
      icon="warning"
      title="生成失败"
      :sub-title="errorMsg"
    >
      <template #extra>
        <el-button type="primary" @click="handleOpen">重新生成</el-button>
      </template>
    </el-result>

    <!-- 文案展示 — 上方图片，下方文案 -->
    <div v-else-if="copywritingText" class="copywriting-result">
      <!-- 行程封面图 -->
      <div class="copywriting-result__image" v-if="tripImage">
        <img :src="tripImage" :alt="tripTitle" />
      </div>

      <!-- 行程信息 -->
      <div class="copywriting-result__header">
        <span class="copywriting-result__title">{{ tripTitle }}</span>
        <span class="copywriting-result__date">{{ tripDate }}</span>
      </div>

      <!-- 文案 -->
      <div class="copywriting-result__text">{{ copywritingText }}</div>

      <!-- 操作区 -->
      <div class="copywriting-result__actions">
        <span class="copywriting-result__hint">可编辑后复制</span>
        <el-button type="primary" :icon="DocumentCopy" @click="handleCopy" :loading="copied" size="small">
          {{ copied ? '已复制' : '一键复制' }}
        </el-button>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="copywriting-empty">
      <el-empty description="生成一段口语化的朋友圈文案" :image-size="80" />
    </div>

    <template #footer>
      <el-button @click="$emit('update:visible', false)">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { DocumentCopy } from '@element-plus/icons-vue'
import { generateCopywriting } from '../api/ai'

const props = defineProps({
  visible: { type: Boolean, default: false },
  trip: { type: Object, default: null },
})

const emit = defineEmits(['update:visible'])

const loading = ref(false)
const copywritingText = ref('')
const tripTitle = ref('')
const tripDate = ref('')
const tripImage = ref('')
const errorMsg = ref('')
const copied = ref(false)

/** 弹窗打开 / 重新生成时调用 */
async function handleOpen() {
  if (!props.trip) return

  loading.value = true
  errorMsg.value = ''
  copywritingText.value = ''
  copied.value = false

  try {
    const res = await generateCopywriting(props.trip.id)
    const data = res.data.data
    copywritingText.value = data.copywriting || ''
    tripTitle.value = data.trip_title || props.trip.title || ''
    tripDate.value = data.trip_date || props.trip.date || ''
    tripImage.value = props.trip.image_url || ''
  } catch (err) {
    errorMsg.value = err.response?.data?.message || 'AI 服务暂时不可用，请稍后重试'
  } finally {
    loading.value = false
  }
}

/** 复制到剪贴板 */
async function handleCopy() {
  try {
    await navigator.clipboard.writeText(copywritingText.value)
    copied.value = true
    ElMessage.success('已复制到剪贴板')
    setTimeout(() => (copied.value = false), 2000)
  } catch {
    ElMessage.error('复制失败，请手动选择文字后 Ctrl+C')
  }
}
</script>

<style scoped>
.copywriting-loading {
  padding: var(--spacing-lg) 0;
}

.copywriting-empty {
  padding: var(--spacing-lg) 0;
}

.copywriting-result {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.copywriting-result__image {
  width: 100%;
  height: 200px;
  border-radius: var(--radius-md);
  overflow: hidden;
  background: #f0f0f0;
}
.copywriting-result__image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.copywriting-result__header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.copywriting-result__title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
}

.copywriting-result__date {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.copywriting-result__text {
  font-size: 15px;
  line-height: 1.8;
  color: var(--text-primary);
  white-space: pre-wrap;
  padding: var(--spacing-md);
  background: #f9fafb;
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--color-accent);
}

.copywriting-result__actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.copywriting-result__hint {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}
</style>
