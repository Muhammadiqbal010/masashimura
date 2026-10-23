import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "Home", component: () => import("../pages/Home.vue") },
    {
      path: "/masashimura-internalakses",
      name: "Login",
      component: () => import("../pages/Login.vue"),
      meta: { hideNavFooter: true },
    },
    {
      path: "/register",
      name: "Register",
      component: () => import("../pages/Register.vue"),
    },
    {
      path: "/checkout",
      name: "Checkout",
      component: () => import("../views/customer/Checkout.vue"),
      // Checkout fokus ke pembayaran: tanpa Navbar & Footer, tapi tetap memakai gaya situs publik.
      meta: { requiresAuth: false, hideNavFooter: true, publicStyle: true },
    },
    { path: "/menu", name: "Menu", component: () => import("../pages/Menu.vue") },
    { path: "/contact", name: "Contact", component: () => import("../pages/Contact.vue") },

    {
      path: "/admin",
      component: () => import("../layouts/AdminLayout.vue"),
      meta: { requiresAuth: true, roles: ["owner", "admin", "kasir"] },
      children: [
        { path: "", name: "AdminDashboard", component: () => import("../views/admin/AdminDashboard.vue"), meta: { roles: ["owner", "admin"] } },
        { path: "menus", name: "ManageMenus", component: () => import("../views/admin/ManageMenus.vue"), meta: { roles: ["owner", "admin"] } },
        { path: "promos", name: "AdminPromos", component: () => import("../views/admin/AdminPromos.vue"), meta: { roles: ["owner", "admin"] } },
        { path: "point-rewards", name: "AdminPointRewards", component: () => import("../views/admin/AdminPointRewards.vue"), meta: { roles: ["owner", "admin"] } },
        { path: "orders", name: "ActiveOrders", component: () => import("../views/admin/ActiveOrders.vue"), meta: { roles: ["owner", "admin", "kasir"] } },
        { path: "reports", name: "OrderReports", component: () => import("../pages/OrderReports.vue"), meta: { roles: ["owner", "admin"] } },
        { path: "pos", name: "NewOrder", component: () => import("../pages/NewOrder.vue"), meta: { roles: ["owner", "admin", "kasir"] } },
        { path: "customers", name: "LoyalCustomers", component: () => import("../pages/LoyalCustomers.vue"), meta: { roles: ["owner", "admin"] } },
        { path: "finance", name: "AdminFinance", component: () => import("../views/admin/AdminFinance.vue"), meta: { roles: ["owner"] } },
        { path: "edit-homepage", name: "EditHomepage", component: () => import("../views/admin/EditHomepage.vue"), meta: { roles: ["owner", "admin"] } },
        { path: "registerinternal", name: "RegisterStaff", component: () => import("../pages/Register.vue"), meta: { roles: ["owner"] } },
        { path: "profile", name: "UserProfile", component: () => import("../pages/UserProfile.vue"), meta: { roles: ["owner", "admin", "kasir"] } },
        { path: "settings", name: "AdminSettings", component: () => import("../views/admin/AdminSettings.vue"), meta: { roles: ["owner"] } },
        { path: "staff", name: "ManageStaff", component: () => import("../views/admin/ManageStaff.vue"), meta: { roles: ["owner"] } },
      ],
    },

    // 404 — catch-all PALING BAWAH, harus komponen sendiri, BUKAN redirect
    { path: "/:pathMatch(.*)*", name: "NotFound", component: () => import("../pages/NotFound.vue") },
  ],
});

router.beforeEach((to) => {
  const token = localStorage.getItem("token");
  const userRole = localStorage.getItem("role")?.toLowerCase();
  const STAFF_ROLES = ["owner", "admin", "kasir"];

  if (to.matched.some((record) => record.meta.requiresAuth)) {
    if (!token) return { name: "Login" };

    // Allowlist: cuma 3 role staff yang boleh masuk /admin sama sekali
    if (!STAFF_ROLES.includes(userRole)) return { name: "Menu" };

    // Cek role spesifik per halaman (ambil meta.roles paling dalam yang match)
    const matchedWithRoles = [...to.matched].reverse().find((r) => r.meta.roles);
    if (matchedWithRoles && !matchedWithRoles.meta.roles.includes(userRole)) {
      return { name: "AdminDashboard" };
    }
  }

  if ((to.name === "Login" || to.name === "Register") && token) {
    return { name: "AdminDashboard" };
  }

  return true;
});

// Setelah deploy baru, file chunk lama (hash berbeda) hilang di server. Navigasi ke halaman
// yang di-lazy-load jadi gagal diam-diam. Muat ulang sekali ke tujuan agar dapat versi terbaru.
router.onError((err, to) => {
  const msg = String(err?.message || err);
  const isChunkError = /dynamically imported module|Importing a module script failed|Loading chunk|Unable to preload CSS/i.test(msg);
  if (!isChunkError) return;
  const KEY = "masashimura:chunkReload";
  if (sessionStorage.getItem(KEY) === to.fullPath) return; // cegah loop reload
  sessionStorage.setItem(KEY, to.fullPath);
  window.location.assign(to.fullPath);
});

window.addEventListener("vite:preloadError", (e) => {
  e.preventDefault();
  window.location.reload();
});

export default router;