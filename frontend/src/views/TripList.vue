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
        style="width: 160px"
        @change="loadTrips"
      />
      <el-button v-if="filterCity" text @click="handleClearFilters">重置</el-button>
      <span class="trip-list-page__total-budget" v-if="totalBudget > 0">
        总预算 <strong>¥{{ totalBudget }}</strong>
      </span>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="trip-list-page__loading">
      <el-skeleton v-for="i in 3" :key="i" :rows="2" animated style="margin-bottom: 16px" />
    </div>

    <!-- 空状态 -->
    <div v-else-if="trips.length === 0" class="trip-list-page__empty">
      <el-empty description="还没有行程">
        <el-button type="primary" @click="showPlanDialog = true">让 AI 帮你规划</el-button>
      </el-empty>
    </div>

    <!-- 日历 + 行程 -->
    <template v-else>
      <!-- 日历 -->
      <div class="trip-list-page__calendar">
        <el-calendar v-model="selectedDate">
          <template #date-cell="{ data }">
            <div
              class="calendar-cell"
              :class="{ 'calendar-cell--has-trip': tripDates.has(data.day) }"
            >
              {{ data.day.split('-').pop() }}
            </div>
          </template>
        </el-calendar>
      </div>

      <!-- 选中日期行程 -->
      <div class="trip-list-page__selected">
        <div class="trip-list-page__date-header">
          <span class="trip-list-page__date-label">{{ selectedDateStr }}</span>
          <span class="trip-list-page__date-weekday">{{ selectedWeekday }}</span>
          <span class="trip-list-page__date-count" v-if="selectedDateTrips.length > 0">
            {{ selectedDateTrips.length }} 条行程
          </span>
          <span class="trip-list-page__date-budget" v-if="selectedDateBudget > 0">
            ¥{{ selectedDateBudget }}
          </span>
          <el-button link type="primary" size="small" @click="handleCreateOnDate">
            <el-icon><Plus /></el-icon>
          </el-button>
        </div>

        <div class="trip-list-page__cards" v-if="selectedDateTrips.length > 0">
          <TripCard
            v-for="trip in selectedDateTrips"
            :key="trip.id"
            :trip="trip"
            @edit="handleEdit"
            @delete="handleDelete"
            @copywriting="handleCopywriting"
          />
        </div>
        <p v-else class="trip-list-page__no-trip">暂无行程，点击 + 新建</p>
      </div>
    </template>

    <!-- 弹窗 -->
    <TripFormDialog
      v-model:visible="showFormDialog"
      :trip="editingTrip"
      @saved="handleSaved"
    />
    <AIPlanDialog
      v-model:visible="showPlanDialog"
      @saved="handleSaved"
    />
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

// ---- 数据 ----
const trips = ref([])
const dailyBudgets = ref({})
const totalBudget = ref(0)
const loading = ref(false)
const filterCity = ref('')

// ---- 日历 ----
const selectedDate = ref(new Date())
const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']

function fmtDate(d) {
  if (typeof d === 'string') return d
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

const selectedDateStr = computed(() => fmtDate(selectedDate.value))

const tripDates = computed(() => {
  const set = new Set()
  trips.value.forEach((t) => set.add(t.date))
  return set
})

const selectedWeekday = computed(() => {
  const d = selectedDate.value
  return weekdays[d.getDay()]
})

const selectedDateTrips = computed(() => {
  const dateStr = selectedDateStr.value
  return trips.value
    .filter((t) => t.date === dateStr)
    .sort((a, b) => a.start_time.localeCompare(b.start_time))
})

const selectedDateBudget = computed(() => {
  return dailyBudgets.value[selectedDateStr.value] || 0
})

// ---- 弹窗 ----
const showFormDialog = ref(false)
const showPlanDialog = ref(false)
const showCopywritingDialog = ref(false)
const editingTrip = ref(null)
const selectedTrip = ref(null)

// ---- 加载 ----
async function loadTrips() {
  loading.value = true
  try {
    const params = {}
    if (filterCity.value) params.city = filterCity.value
    const res = await getTrips(params)
    const data = res.data.data
    trips.value = data.trips || []
    dailyBudgets.value = data.daily_budgets || {}
    totalBudget.value = data.total_budget || 0

    // 选中日期无行程时跳到最近有行程的日期
    if (!tripDates.value.has(selectedDateStr.value) && trips.value.length > 0) {
      const sorted = [...new Set(trips.value.map((t) => t.date))].sort()
      const today = new Date().toISOString().split('T')[0]
      selectedDate.value = new Date(sorted.find((d) => d >= today) || sorted[sorted.length - 1])
    }
  } catch {
    // 拦截器已处理
  } finally {
    loading.value = false
  }
}

function handleClearFilters() {
  filterCity.value = ''
  loadTrips()
}

// ---- 操作 ----
function handleCreate() {
  editingTrip.value = null
  showFormDialog.value = true
}

function handleCreateOnDate() {
  editingTrip.value = { date: selectedDateStr.value }
  showFormDialog.value = true
}

function handleEdit(trip) {
  editingTrip.value = trip
  showFormDialog.value = true
}

async function handleDelete(trip) {
  try {
    await ElMessageBox.confirm(
      `确定删除"${trip.title}"吗？`,
      '删除确认',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    await deleteTrip(trip.id)
    ElMessage.success('已删除')
    await loadTrips()
  } catch { /* 取消 */ }
}

function handleCopywriting(trip) {
  selectedTrip.value = trip
  showCopywritingDialog.value = true
}

function handleSaved() {
  loadTrips()
}

function handleLogout() {
  userStore.clearAuth()
  router.push('/login')
}

onMounted(() => {
  loadTrips()
})
</script>

<style scoped>
.trip-list-page {
  max-width: 780px;
  margin: 0 auto;
  padding: var(--spacing-lg);
}

/* 顶部 */
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

/* 筛选 */
.trip-list-page__filters {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}
.trip-list-page__total-budget {
  margin-left: auto;
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}
.trip-list-page__total-budget strong {
  color: var(--color-accent);
  font-size: var(--font-size-md);
}

/* 加载 / 空 */
.trip-list-page__loading { padding: var(--spacing-lg) 0; }
.trip-list-page__empty { padding: var(--spacing-xl) 0; text-align: center; }

/* 日历 */
.trip-list-page__calendar {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  margin-bottom: var(--spacing-lg);
}
.calendar-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  margin: 0 auto;
  border-radius: 50%;
  font-size: var(--font-size-md);
  transition: var(--transition-fast);
}
.calendar-cell--has-trip {
  background: var(--color-accent);
  color: #fff;
  font-weight: var(--font-weight-semibold);
}

/* Element Plus 日历样式覆盖 */
:deep(.el-calendar) {
  --el-calendar-border: none;
  --el-calendar-header-border-bottom: none;
}
:deep(.el-calendar__header) {
  padding: var(--spacing-md) var(--spacing-md) 0;
}
:deep(.el-calendar__body) {
  padding: 0 var(--spacing-sm) var(--spacing-sm);
}
:deep(.el-calendar-table td) {
  border: none !important;
}
:deep(.el-calendar-table .el-calendar-day) {
  height: 44px;
  padding: 0;
}

/* 选中日期 */
.trip-list-page__selected {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
  padding: var(--spacing-md);
}
.trip-list-page__date-header {
  display: flex;
  align-items: baseline;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
  padding-bottom: var(--spacing-sm);
  border-bottom: 1px solid var(--border-color);
}
.trip-list-page__date-label {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
}
.trip-list-page__date-weekday {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}
.trip-list-page__date-count {
  margin-left: auto;
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}
.trip-list-page__date-budget {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-accent);
}
.trip-list-page__cards {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}
.trip-list-page__no-trip {
  text-align: center;
  color: var(--text-secondary);
  font-size: var(--font-size-md);
  padding: var(--spacing-lg) 0;
}
</style>
