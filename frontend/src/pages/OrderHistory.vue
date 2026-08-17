<template>
  <div class="min-h-screen bg-[#050505] text-white">
    <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-10">

      <!-- Header -->
      <div class="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-6">
        <div>
          <h1 class="text-2xl sm:text-3xl font-oswald uppercase tracking-wide">Riwayat Transaksi</h1>
          <p class="text-sm text-white/40 mt-1">Pantau transaksi yang sudah diproses pada periode ini.</p>
        </div>

        <!-- Period selector -->
        <div class="inline-flex p-1 bg-white/5 rounded-xl border border-white/5 self-start sm:self-auto">
          <button
            v-for="opt in periodOptions"
            :key="opt.value"
            @click="period = opt.value"
            class="px-3 sm:px-4 py-2 text-sm font-medium rounded-lg transition-colors duration-150"
            :class="period === opt.value
              ? 'bg-red-600 text-white shadow-sm'
              : 'text-white/50 hover:text-white hover:bg-white/5'"
          >
            {{ opt.label }}
          </button>
        </div>
      </div>

      <!-- Summary stats -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6">
        <div class="bg-[#0a0a0a] border border-white/5 rounded-xl p-4">
          <p class="text-xs text-white/40 uppercase tracking-wide">Total Transaksi</p>
          <p class="text-2xl font-oswald mt-1">{{ summary.count }}</p>
        </div>
        <div class="bg-[#0a0a0a] border border-white/5 rounded-xl p-4">
          <p class="text-xs text-white/40 uppercase tracking-wide">Total Pendapatan</p>
          <p class="text-2xl font-oswald mt-1 text-red-500">{{ formatPrice(summary.total) }}</p>
        </div>
        <div class="bg-[#0a0a0a] border border-white/5 rounded-xl p-4">
          <p class="text-xs text-white/40 uppercase tracking-wide">Rata-rata / Transaksi</p>
          <p class="text-2xl font-oswald mt-1">{{ formatPrice(summary.average) }}</p>
        </div>
      </div>

      <!-- Search -->
      <div class="relative mb-5">
        <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-4.35-4.35M17 11a6 6 0 11-12 0 6 6 0 0112 0z" />
        </svg>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Cari nomor order atau nama pelanggan..."
          class="w-full bg-[#0a0a0a] border border-white/5 rounded-xl pl-10 pr-4 py-2.5 text-sm placeholder:text-white/30 focus:outline-none focus:ring-2 focus:ring-red-600/50 focus:border-red-600/50 transition"
        />
      </div>

      <!-- Loading skeleton -->
      <div v-if="isLoading" class="space-y-3">
        <div v-for="n in 4" :key="n" class="bg-[#0a0a0a] border border-white/5 rounded-xl p-4 animate-pulse">
          <div class="flex justify-between">
            <div class="space-y-2">
              <div class="h-3.5 w-28 bg-white/10 rounded"></div>
              <div class="h-2.5 w-20 bg-white/5 rounded"></div>
            </div>
            <div class="space-y-2 text-right">
              <div class="h-3.5 w-24 bg-white/10 rounded ml-auto"></div>
              <div class="h-2.5 w-16 bg-white/5 rounded ml-auto"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Orders list -->
      <div v-else-if="filteredOrders.length" class="space-y-3">
        <div
          v-for="order in filteredOrders"
          :key="order.id"
          class="bg-[#0a0a0a] border border-white/5 rounded-xl overflow-hidden transition-colors hover:border-white/10"
        >
          <div class="p-4">
            <div class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
              <!-- Left: order info -->
              <div class="min-w-0">
                <div class="flex items-center gap-2">
                  <p class="font-bold truncate">{{ order.order_number }}</p>
                  <span
                    class="px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide rounded-full shrink-0"
                    :class="statusStyle(order.payment_status).badge"
                  >
                    {{ statusStyle(order.payment_status).label }}
                  </span>
                </div>
                <p class="text-xs text-white/40 mt-1">{{ order.customer_name || 'Walk In' }}</p>
                <p class="text-xs text-white/30 font-mono mt-0.5">{{ order.created_time }}</p>
              </div>

              <!-- Right: price info -->
              <div class="text-left sm:text-right shrink-0">
                <p class="text-red-500 font-bold text-base">{{ formatPrice(order.total_price) }}</p>
                <p class="text-xs text-white/40 mt-1">{{ order.payment_method || '—' }}</p>
              </div>
            </div>

            <!-- Toggle items -->
            <button
              v-if="order.items?.length"
              @click="toggleExpand(order.id)"
              class="mt-3 flex items-center gap-1.5 text-xs text-white/40 hover:text-white/70 transition-colors"
            >
              <svg
                class="w-3.5 h-3.5 transition-transform duration-200"
                :class="{ 'rotate-90': isExpanded(order.id) }"
                fill="none" viewBox="0 0 24 24" stroke="currentColor"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
              </svg>
              {{ order.items.length }} item{{ order.items.length > 1 ? '' : '' }}
            </button>
          </div>

          <!-- Detail item -->
          <div
            v-if="order.items?.length && isExpanded(order.id)"
            class="px-4 pb-4 pt-0 border-t border-white/5 mt-1"
          >
            <div class="space-y-1.5 pt-3">
              <div v-for="item in order.items" :key="item.id" class="flex justify-between text-xs text-white/50">
                <span class="truncate pr-3">{{ item.quantity }}x {{ item.menu_name }}</span>
                <span class="shrink-0">{{ formatPrice(item.price * item.quantity) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty state -->
      <div v-else class="flex flex-col items-center justify-center text-center py-20 px-4">
        <div class="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center mb-4">
          <svg class="w-6 h-6 text-white/30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <p class="text-white/50 font-medium">
          {{ searchQuery ? 'Tidak ada transaksi yang cocok' : 'Belum ada transaksi pada periode ini' }}
        </p>
        <p class="text-white/30 text-sm mt-1">
          {{ searchQuery ? 'Coba kata kunci lain.' : 'Transaksi akan muncul di sini setelah ada order yang selesai.' }}
        </p>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from "vue";
import apiClient from "@/api/client";

const orders = ref([]);
const period = ref("today");
const isLoading = ref(true);
const searchQuery = ref("");
const expandedIds = ref(new Set());

const periodOptions = [
  { value: "today", label: "Hari Ini" },
  { value: "week", label: "Minggu Ini" },
  { value: "month", label: "Bulan Ini" },
];

const fetchHistory = async () => {
  isLoading.value = true;
  try {
    const { data } = await apiClient.get("/orders/history/", {
      params: { period: period.value },
    });
    orders.value = data;
  } catch (err) {
    console.error(err);
  } finally {
    isLoading.value = false;
  }
};

watch(period, fetchHistory);
onMounted(fetchHistory);

const filteredOrders = computed(() => {
  const q = searchQuery.value.trim().toLowerCase();
  if (!q) return orders.value;
  return orders.value.filter((o) =>
    o.order_number?.toLowerCase().includes(q) ||
    (o.customer_name || "walk in").toLowerCase().includes(q)
  );
});

const summary = computed(() => {
  const count = filteredOrders.value.length;
  const total = filteredOrders.value.reduce((sum, o) => sum + (o.total_price || 0), 0);
  return {
    count,
    total,
    average: count ? total / count : 0,
  };
});

const toggleExpand = (id) => {
  const next = new Set(expandedIds.value);
  next.has(id) ? next.delete(id) : next.add(id);
  expandedIds.value = next;
};
const isExpanded = (id) => expandedIds.value.has(id);

const statusStyle = (status) => {
  const s = (status || "").toLowerCase();
  const map = {
    paid: { label: "Lunas", badge: "bg-emerald-500/10 text-emerald-400" },
    completed: { label: "Lunas", badge: "bg-emerald-500/10 text-emerald-400" },
    pending: { label: "Pending", badge: "bg-amber-500/10 text-amber-400" },
    unpaid: { label: "Belum Bayar", badge: "bg-amber-500/10 text-amber-400" },
    cancelled: { label: "Batal", badge: "bg-white/10 text-white/40" },
    canceled: { label: "Batal", badge: "bg-white/10 text-white/40" },
  };
  return map[s] || { label: status || "—", badge: "bg-white/10 text-white/40" };
};

const formatPrice = (value) =>
  new Intl.NumberFormat("id-ID", {
    style: "currency",
    currency: "IDR",
    minimumFractionDigits: 0,
  }).format(value || 0);
</script>