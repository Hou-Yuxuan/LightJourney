<template>
  <div class="trip-list-page">
    <!-- 顶部操作栏 -->
    <header class="trip-list-page__header">
      <div class="trip-list-page__header-left">
        <h1>我的行程</h1>
        <span class="trip-list-page__username">{{ userStore.username }}</span>
      </div>
      <div class="trip-list-page__header-right">
        <el-button type="primary" @click="showPlanDialog = true">
          <el-icon><MagicStick /></el-icon> AI 帮我规划
        </el-button>
        <el-button @click="handleCreate">
          <el-icon><Plus /></el-icon> 新建行程
        </el-button>
        <el-button text @click="handleLogout">退出登录</el-button>
      </div>
    </header>

    <!-- 筛选栏 -->
    <div class="trip-list-page__filters">
      <el-input
        v-model="filterCity"
        placeholder="按城市筛选"
        clearable
        style="width: 200px"
        @change="loadTrips"
      />
      <el-date-picker
        v-model="filterDateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        format="YYYY-MM-DD"
        value-format="YYYY-MM-DD"
        style="width: 280px"
        @change="loadTrips"
      />
      <el-button v-if="filterCity || filterDateRange" text @click="handleClearFilters">
        重置筛选
      </el-button>
      <span class="trip-list-page__total-budget" v-if="totalBudget > 0">
        总预算：<strong>¥{{ totalBudget }}</strong>
      </span>
    </div>

    <!-- 加载中骨架屏 -->
    <div v-if="loading" class="trip-list-page__loading">
      <el-skeleton v-for="i in 3" :key="i" :rows="2" animated style="margin-bottom: 16px" />
    </div>

    <!-- 空状态 -->
    <div v-else-if="trips.length === 0" class="trip-list-page__empty">
      <el-empty description="还没有行程">
        <template #image>
          <img src="" alt="" style="display:none" />
        </template>
        <el-button type="primary" @click="showPlanDialog = true">
          让 AI 帮你规划
        </el-button>
        <p class="trip-list-page__empty-hint">或者点击右上角"新建行程"手动添加</p>
      </el-empty>
    </div>

    <!-- 行程列表：按日期分组 -->
    <div v-else class="trip-list-page__groups">
      <div
        v-for="group in groupedTrips"
        :key="group.date"
        class="trip-list-page__group"
      >
        <!-- 日期分组标题 -->
        <div class="trip-list-page__date-header">
          <span class="trip-list-page__date-label">{{ group.date }}</span>
          <span class="trip-list-page__date-weekday">{{ group.weekday }}</span>
          <span class="trip-list-page__date-budget" v-if="group.dailyBudget > 0">
            当日预算 ¥{{ group.dailyBudget }}
          </span>
        </div>

        <!-- 该日期下的行程卡片 -->
        <TransitionGroup name="trip-card-list" tag="div" class="trip-list-page__cards">
          <TripCard
            v-for="trip in group.trips"
            :key="trip.id"
            :trip="trip"
            @edit="handleEdit"
            @delete="handleDelete"
            @copywriting="handleCopywriting"
          />
        </TransitionGroup>
      </div>
    </div>

    <!-- 行程编辑弹窗 -->
    <TripFormDialog
      v-model:visible="showFormDialog"
      :trip="editingTrip"
      @saved="handleSaved"
    />

    <!-- AI 规划弹窗 (P5) -->
    <AIPlanDialog
      v-model:visible="showPlanDialog"
      @saved="handleSaved"
    />

    <!-- AI 文案弹窗 (P5) -->
    <AICopywritingDialog
      v-model:visible="showCopywritingDialog"
      :trip="selectedTrip"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { MagicStick, Plus } from '@element-plus/icons-vue'
import { useUserStore } from '../stores/user'
import { useRouter } from 'vue-router'
import { getTrips, deleteTrip } from '../api/trips'
import TripCard from '../components/TripCard.vue'
import TripFormDialog from '../components/TripFormDialog.vue'
import AIPlanDialog from '../components/AIPlanDialog.vue'
import AICopywritingDialog from '../components/AICopywritingDialog.vue'

const userStore = useUserStore()
const router = useRouter()

// ---- 数据状态 ----
const trips = ref([])
const dailyBudgets = ref({})
const totalBudget = ref(0)
const loading = ref(false)

// ---- 筛选状态 ----
const filterCity = ref('')
const filterDateRange = ref([])

// ---- 弹窗控制 ----
const showFormDialog = ref(false)
const showPlanDialog = ref(false)
const showCopywritingDialog = ref(false)
const editingTrip = ref(null)
const selectedTrip = ref(null)

// ---- 星期转换 ----
const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
function getWeekday(dateStr) {
  const d = new Date(dateStr)
  return weekdays[d.getDay()]
}

// ---- 按日期分组（计算属性） ----
const groupedTrips = computed(() => {
  const groups = {}
  for (const trip of trips.value) {
    if (!groups[trip.date]) {
      groups[trip.date] = []
    }
    groups[trip.date].push(trip)
  }
  // 按日期排序，组内按时段排序
  return Object.keys(groups)
    .sort()
    .map((date) => ({
      date,
      weekday: getWeekday(date),
      dailyBudget: dailyBudgets.value[date] || 0,
      trips: groups[date].sort((a, b) => a.start_time.localeCompare(b.start_time)),
    }))
})

// ---- 加载行程列表 ----
async function loadTrips() {
  loading.value = true
  try {
    const params = {}
    if (filterCity.value) params.city = filterCity.value
    if (filterDateRange.value && filterDateRange.value.length === 2) {
      params.date_from = filterDateRange.value[0]
      params.date_to = filterDateRange.value[1]
    }
    const res = await getTrips(params)
    const data = res.data.data
    trips.value = data.trips || []
    dailyBudgets.value = data.daily_budgets || {}
    totalBudget.value = data.total_budget || 0
  } catch {
    // 错误已由 axios 拦截器统一处理
  } finally {
    loading.value = false
  }
}

// ---- 清除筛选 ----
function handleClearFilters() {
  filterCity.value = ''
  filterDateRange.value = []
  loadTrips()
}

// ---- 新建行程 ----
function handleCreate() {
  editingTrip.value = null
  showFormDialog.value = true
}

// ---- 编辑行程 ----
function handleEdit(trip) {
  editingTrip.value = trip
  showFormDialog.value = true
}

// ---- 删除行程 ----
async function handleDelete(trip) {
  try {
    await ElMessageBox.confirm(
      `确定删除行程"${trip.title}"吗？删除后不可恢复。`,
      '删除确认',
      { confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'warning' }
    )
    await deleteTrip(trip.id)
    ElMessage.success('已删除')
    await loadTrips()
  } catch {
    // 用户取消删除 或 删除失败（错误已由拦截器处理）
  }
}

// ---- 生成文案 ----
function handleCopywriting(trip) {
  selectedTrip.value = trip
  showCopywritingDialog.value = true
}

// ---- 保存成功回调节 ----
function handleSaved() {
  loadTrips()
}

// ---- 退出登录 ----
function handleLogout() {
  userStore.clearAuth()
  router.push('/login')
}

// ---- 页面初始化 ----
onMounted(() => {
  loadTrips()
})
</script>

<style scoped>
.trip-list-page {
  max-width: 900px;
  margin: 0 auto;
  padding: var(--spacing-lg);
}

/* 顶部操作栏 */
.trip-list-page__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-lg);
}
.trip-list-page__header-left {
  display: flex;
  align-items: baseline;
  gap: var(--spacing-md);
}
.trip-list-page__header-left h1 {
  margin: 0;
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
}
.trip-list-page__username {
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
}
.trip-list-page__header-right {
  display: flex;
  gap: var(--spacing-sm);
}

/* 筛选栏 */
.trip-list-page__filters {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
  padding: var(--spacing-md);
  background: var(--bg-card);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
}
.trip-list-page__total-budget {
  margin-left: auto;
  font-size: var(--font-size-md);
  color: var(--text-secondary);
}
.trip-list-page__total-budget strong {
  color: var(--color-accent);
  font-size: var(--font-size-lg);
}

/* 加载状态 */
.trip-list-page__loading {
  padding: var(--spacing-lg) 0;
}

/* 空状态 */
.trip-list-page__empty {
  padding: var(--spacing-xl) 0;
  text-align: center;
}
.trip-list-page__empty-hint {
  margin-top: var(--spacing-sm);
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

/* 日期分组 */
.trip-list-page__groups {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}
.trip-list-page__group {
  /* 分组容器 */
}
.trip-list-page__date-header {
  display: flex;
  align-items: baseline;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) 0;
  margin-bottom: var(--spacing-sm);
  border-bottom: 1px solid var(--border-color);
}
.trip-list-page__date-label {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
}
.trip-list-page__date-weekday {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}
.trip-list-page__date-budget {
  margin-left: auto;
  font-size: var(--font-size-sm);
  color: var(--color-accent);
}

/* 卡片列表 */
.trip-list-page__cards {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

/* 列表过渡动效 */
.trip-card-list-enter-active,
.trip-card-list-leave-active {
  transition: all 0.3s ease;
}
.trip-card-list-enter-from {
  opacity: 0;
  transform: translateY(-8px);
}
.trip-card-list-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
