<template>
  <div class="trip-card">
    <!-- 左侧时间 -->
    <div class="trip-card__time">
      <span class="trip-card__time-text">{{ trip.start_time }} - {{ trip.end_time }}</span>
    </div>
    <!-- 中间图片 + 内容 -->
    <div class="trip-card__body">
      <div class="trip-card__main">
        <div class="trip-card__thumb" v-if="trip.image_url">
          <img :src="trip.image_url" :alt="trip.title" />
        </div>
        <div class="trip-card__info">
          <div class="trip-card__header">
            <h3 class="trip-card__title">{{ trip.title }}</h3>
            <el-tag size="small" type="info">{{ trip.city }}</el-tag>
          </div>
          <p class="trip-card__desc" v-if="trip.description">{{ trip.description }}</p>
          <div class="trip-card__footer">
            <span class="trip-card__budget" v-if="trip.budget > 0">¥{{ trip.budget }}</span>
          </div>
        </div>
      </div>
    </div>
    <!-- 右侧操作 -->
    <div class="trip-card__actions">
      <el-button text size="small" @click="$emit('edit', trip)">编辑</el-button>
      <el-button text size="small" type="primary" @click="$emit('copywriting', trip)">生成文案</el-button>
      <el-button text size="small" type="danger" @click="$emit('delete', trip)">删除</el-button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  trip: { type: Object, required: true },
})

defineEmits(['edit', 'delete', 'copywriting'])
</script>

<style scoped>
.trip-card {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
  transition: var(--transition-fast);
}
.trip-card:hover {
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
}
.trip-card__time {
  min-width: 100px;
  padding-top: 4px;
}
.trip-card__time-text {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  white-space: nowrap;
}
.trip-card__body {
  flex: 1;
  min-width: 0;
}
.trip-card__main {
  display: flex;
  gap: var(--spacing-md);
}
.trip-card__thumb {
  flex-shrink: 0;
  width: 80px;
  height: 60px;
  border-radius: var(--radius-sm);
  overflow: hidden;
  background: #f0f0f0;
}
.trip-card__thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.trip-card__info {
  flex: 1;
  min-width: 0;
}
.trip-card__header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
}
.trip-card__title {
  margin: 0;
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-medium);
}
.trip-card__desc {
  margin: var(--spacing-xs) 0 0;
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  line-height: 1.5;
}
.trip-card__footer {
  margin-top: var(--spacing-xs);
}
.trip-card__budget {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--color-accent);
}
.trip-card__actions {
  display: flex;
  flex-direction: column;
  gap: 2px;
  opacity: 0;
  transition: var(--transition-fast);
  flex-shrink: 0;
}
.trip-card:hover .trip-card__actions {
  opacity: 1;
}
</style>
