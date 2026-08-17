// src/stores/orderNotifications.js
import { defineStore } from 'pinia';
import { ref } from 'vue';
import { toast } from 'vue-sonner';
import apiClient from '@/api/client';
import { playNewOrderChime } from '@/utils/notificationSound';

const POLL_INTERVAL_MS = 8000;
const STORAGE_KEY = 'masashimura_last_seen_order_id';

export const useOrderNotificationsStore = defineStore('orderNotifications', () => {
  // Coba baca cursor terakhir dari localStorage dulu (survive refresh/reload).
  // Kalau gak ada / gak valid, tetep null → nanti di-bootstrap dari backend.
  const savedId = Number(localStorage.getItem(STORAGE_KEY));
  const lastSeenId = ref(Number.isFinite(savedId) && savedId >= 0 ? savedId : null);

  const unreadCount = ref(0); // buat badge di sidebar "Active Orders"
  let pollingTimer = null;

  const persistLastSeenId = () => {
    if (lastSeenId.value !== null) {
      localStorage.setItem(STORAGE_KEY, String(lastSeenId.value));
    }
  };

  const checkForNewOrders = async () => {
    try {
      const params = lastSeenId.value !== null ? { after_id: lastSeenId.value } : {};
      const { data } = await apiClient.get('/orders/notifications/', { params });

      // Amankan data: Kalau backend ngereturn array langsung, pakai data.
      // Kalau ngereturn object { new_orders: [...] }, pakai data.new_orders.
      const orders = Array.isArray(data) ? data : (data.new_orders || []);

      // Panggilan pertama (lastSeenId masih null): cuma bootstrap cursor.
      // Backend SELALU ngasih `latest_id` di response — itu starting point
      // cursor kita. JANGAN fallback ke 0, karena itu bikin poll berikutnya
      // nganggep SEMUA order dari awal database sebagai "baru".
      if (lastSeenId.value === null) {
        const latestId = Number(data.latest_id);
        lastSeenId.value = Number.isFinite(latestId) ? latestId : 0;
        persistLastSeenId();
        return;
      }

      // Kalau ada orderan baru (array tidak kosong)
      if (orders.length > 0) {
        playNewOrderChime();

        orders.forEach((o) => {
          toast.success(`Pesanan baru masuk — ${o.order_number}`, {
            description: `${o.customer_name} · Rp ${Number(o.total_price).toLocaleString('id-ID')}`,
            duration: 6000,
          });
        });

        unreadCount.value += orders.length;

        // Update cursor ke ID terbesar dari batch pesanan baru ini.
        // Backend cuma balikin max 20 per call (lihat [:20] di view), jadi
        // kalau ada backlog gede, sisanya bakal kekejar di poll berikutnya
        // secara bertahap — bukan sekaligus.
        lastSeenId.value = Math.max(...orders.map((o) => o.id));
        persistLastSeenId();
      } else {
        const latestId = Number(data.latest_id);
        const hadRealJump = Number.isFinite(latestId) && latestId > lastSeenId.value;

        if (data.backlog_skipped) {
          // Backend deteksi backlog gede (bulk insert / dummy data / dll),
          // bukan order customer beneran. Cursor di-jump langsung tanpa
          // toast satu-satu — cukup 1 info ringkas biar admin ngerti kenapa
          // gak ada notif bunyi berkali-kali.
          if (hadRealJump) {
            toast.info(`${data.backlog_count} data lama disinkronkan (bukan pesanan baru)`, {
              duration: 4000,
            });
          }
        }

        // Tetep sinkronin cursor ke latest_id backend (jaga-jaga kalau ada
        // order 'pos' yang nambahin id tapi di-exclude dari new_orders —
        // biar cursor gak ketinggalan jauh).
        if (hadRealJump) {
          lastSeenId.value = latestId;
          persistLastSeenId();
        }
      }
    } catch (err) {
      console.error('[order-notifications] polling gagal:', err);
    }
  };

  const startPolling = () => {
    if (pollingTimer) return; // udah jalan, jangan dobel
    checkForNewOrders();
    pollingTimer = setInterval(checkForNewOrders, POLL_INTERVAL_MS);
  };

  const stopPolling = () => {
    if (pollingTimer) {
      clearInterval(pollingTimer);
      pollingTimer = null;
    }
  };

  const clearUnread = () => {
    unreadCount.value = 0;
  };

  return { lastSeenId, unreadCount, startPolling, stopPolling, clearUnread, checkForNewOrders };
});