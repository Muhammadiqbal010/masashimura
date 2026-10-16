from rest_framework.throttling import SimpleRateThrottle


class _PerOrderThrottle(SimpleRateThrottle):
    """Throttle per order_number, bukan per IP.

    Per IP berbahaya di sini: banyak customer bisa berbagi satu IP (wifi
    restoran), dan di Vercel IP asli ada di belakang proxy. Per order_number
    cuma membatasi spam ke satu order, tidak mengganggu customer lain.
    """
    def get_cache_key(self, request, view):
        order_number = view.kwargs.get("order_number")
        if not order_number:
            return None
        return self.cache_format % {"scope": self.scope, "ident": order_number}


class PaymentCreateThrottle(_PerOrderThrottle):
    scope = "payment_create"


class PaymentStatusThrottle(_PerOrderThrottle):
    scope = "payment_status"