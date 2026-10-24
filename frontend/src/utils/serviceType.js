// Tipe pesanan: makan di tempat / dibungkus. Order lama tanpa field ini dianggap dine_in.
export const SERVICE_TYPES = {
  dine_in: { label: "Makan di Tempat", short: "Dine In", icon: "🍽️" },
  takeaway: { label: "Dibungkus", short: "Bungkus", icon: "🥡" },
}

export const serviceTypeLabel = (type) => (SERVICE_TYPES[type] || SERVICE_TYPES.dine_in).label
