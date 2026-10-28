import { onMounted } from "vue"
import { useStoreSettings } from "@/composables/useStoreSettings"

/**
 * Status buka/tutup + jadwal untuk tampilan pelanggan (Home, Footer, Kontak).
 *
 * Tidak lagi menyimpan jam sendiri: semuanya dibaca dari pengaturan toko yang diatur admin
 * (Pengaturan Sistem -> Jam operasional + saklar buka/tutup manual), lewat useStoreSettings.
 * Ubah jam di admin, maka semua halaman ikut berubah.
 */
export function useOpenStatus() {
  const {
    openStatus, scheduleText, scheduleRows, todayIndex, closesText, nextOpenText,
    closedMessage, settingsReady, fetchSettings,
  } = useStoreSettings()

  onMounted(() => fetchSettings())

  return {
    status: openStatus,
    scheduleText,
    scheduleRows,
    todayIndex,
    closesText,
    nextOpenText,
    closedMessage,
    ready: settingsReady,
  }
}
