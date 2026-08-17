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
  component: () => import("../views/customer/Checkout.vue"), // Pastikan file Checkout.vue ada di folder pages
  meta: { requiresAuth: false } // Pelanggan tidak perlu login untuk checkout
},
    {
      path: "/menu",
      name: "Menu",
      component: () => import("../pages/Menu.vue"),
    },
    {
      path: "/contact",
      name: "Contact",
      component: () => import("../pages/Contact.vue"),
    },

    // 🌟 Admin Group Routes
    {
      path: "/admin",
      component: () => import("../layouts/AdminLayout.vue"),
      meta: { requiresAuth: true },
      children: [
        {
          path: "",
          name: "AdminDashboard",
          component: () => import("../views/admin/AdminDashboard.vue"),
        },
        {
          path: "menus",
          name: "ManageMenus",
          component: () => import("../views/admin/ManageMenus.vue"),
        },
        {
          path: "promos",
          name: "AdminPromos",
          component: () => import("../views/admin/AdminPromos.vue"),
        },
        {
          path: "point-rewards",
          name: "AdminPointRewards",
          component: () => import("../views/admin/AdminPointRewards.vue"),
        },
        {
          path: "orders",
          name: "ActiveOrders",
          component: () => import("../views/admin/ActiveOrders.vue"),
        },
        {
          path: "reports",
          name: "OrderReports",
          component: () => import("../pages/OrderReports.vue"), // Sesuai kode lo
        },
        {
          path: "pos",
          name: "NewOrder",
          component: () => import("../pages/NewOrder.vue"), // Sesuai kode lo (Tempat kode POS kustom kita)
        },
        {
          path: "customers",
          name: "LoyalCustomers",
          component: () => import("../pages/LoyalCustomers.vue"), // Sesuai kode lo
        },
        // 💰 Tambahkan Rute Finansial Baru (AdminFinance.vue) di Folder Views
        {
          path: "finance",
          name: "AdminFinance",
          component: () => import("../views/admin/AdminFinance.vue"),
          meta: { roles: ["owner"] },
        },
        {
          path: 'edit-homepage',
          name: 'EditHomepage',
          component: () => import("../views/admin/EditHomepage.vue"),
        },
        // 👥 Tambahkan Rute Register Staff Baru (Register.vue) di Folder Views
        {
          path: "registerinternal",
          name: "RegisterStaff",
          component: () => import("../pages/Register.vue"),
        },
        // 👤 Tambahkan Rute Profile Baru (UserProfile.vue) di Folder Views
        {
          path: "profile",
          name: "UserProfile",
          component: () => import("../pages/UserProfile.vue"),
        },
        {
          path: "settings",
          name: "AdminSettings",
          component: () => import("../views/admin/AdminSettings.vue"),
          meta: { roles: ["owner"] },
        },
      ],
    },
    { path: "/:pathMatch(.*)*", redirect: "/" },
  ],
});

// Auth Guard
router.beforeEach((to) => {
  const token = localStorage.getItem("token");
  const userRole = localStorage.getItem("role")?.toLowerCase(); // Normalisasi casing agar aman

  if (to.matched.some((record) => record.meta.requiresAuth)) {
    if (!token) return { name: "Login" };

    // Proteksi role pelanggan agar tidak masuk ke area admin
    if (userRole === "pelanggan") return { name: "Menu" };

    // Proteksi rute khusus owner
    if (to.meta.roles && !to.meta.roles.includes(userRole))
      return { name: "AdminDashboard" };
  }

  // Mencegah user yang sudah login mengakses halaman auth
  if ((to.name === "Login" || to.name === "Register") && token)
    return { name: "AdminDashboard" };

  return true;
});

export default router;