// src/stores/cart.js

import { defineStore } from "pinia";
import { ref, computed, watch } from "vue";
import { orderAPI } from "@/api";

export const useCartStore = defineStore("cart", () => {
  const cart = ref(JSON.parse(localStorage.getItem("cart") || "{}"));

  // Diskon member % SUDAH DIHAPUS — sistem loyalty sekarang murni poin
  // (tukar menu gratis, ditangani terpisah lewat PointRedeemBox/PointRewardsPanel
  // di Checkout.vue). isMember/points di sini cuma buat nampilin badge info,
  // BUKAN buat motong harga cart lagi.
  const isMember = ref(false);
  const points = ref(0);
  const pointsExpiringNote = ref(null);

  watch(
    cart,
    (value) => {
      localStorage.setItem("cart", JSON.stringify(value));
    },
    {
      deep: true,
    }
  );

const addToCart = (menu) => {
  // price_web sudah dihitung di backend saat menu disimpan
  const price   = menu.price_web ?? menu.price;
  const cartKey = `${menu.id}-${Date.now()}`;

  cart.value[cartKey] = {
    ...menu,
    cartKey,
    quantity: 1,
    notes:    "",
    price,         
    price_pos: menu.price,     
    price_web: menu.price_web, 
  };
};

  const updateQuantity = (cartKey, delta) => {
    if (!cart.value[cartKey]) return;

    cart.value[cartKey].quantity += delta;

    if (cart.value[cartKey].quantity <= 0) {
      delete cart.value[cartKey];
    }
  };

  const removeFromCart = (cartKey) => {
    delete cart.value[cartKey];
  };

  const clearCart = () => {
    cart.value = {};
    isMember.value = false;
    points.value = 0;
    pointsExpiringNote.value = null;
  };

  const checkLoyalty = async (phone) => {
    if (!phone || phone.length < 9) {
      isMember.value = false;
      points.value = 0;
      pointsExpiringNote.value = null;
      return;
    }

    try {
      const { data } = await orderAPI.checkLoyalty(phone);

      isMember.value = data.is_member ?? false;
      points.value = data.points ?? 0;
      pointsExpiringNote.value = data.points_expiring_note ?? null;
    } catch (err) {
      console.error(err);

      isMember.value = false;
      points.value = 0;
      pointsExpiringNote.value = null;
    }
  };

  const cartItems = computed(() => Object.values(cart.value));

  const cartItemCount = computed(() =>
    cartItems.value.reduce((sum, item) => sum + item.quantity, 0)
  );

  const subtotal = computed(() =>
    cartItems.value.reduce(
      (sum, item) => sum + Number(item.price) * item.quantity,
      0
    )
  );

  // Total sekarang murni subtotal — diskon member % udah ngga ada.
  // Potongan harga cuma dari promo code (ditangani terpisah di Checkout.vue)
  // atau tukar poin (item reward masuk cart dengan harga Rp0).
  const totalPrice = computed(() => subtotal.value);

  const isEmpty = computed(() => cartItems.value.length === 0);

  return {
    cart,

    isMember,
    points,
    pointsExpiringNote,

    cartItems,
    cartItemCount,

    subtotal,
    totalPrice,
    isEmpty,

    addToCart,
    updateQuantity,
    removeFromCart,
    clearCart,
    checkLoyalty,
  };
});