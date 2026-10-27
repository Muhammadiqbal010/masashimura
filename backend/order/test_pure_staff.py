"""
Tes modul murni (tanpa Django/DB): telegram_ui dan report_format.
Jalankan: python -m unittest order.test_pure_staff   (dari folder backend; juga ikut python manage.py test)
"""
import unittest

from order import report_format as rf
from order import telegram_ui as ui


def view(**kw):
    base = {
        "id": 12, "order_number": "MSM-0012", "customer_name": "Budi Santoso", "customer_phone": "0812-3456-7890",
        "lines": ["• 2× Katsu"], "total": 40000, "status": "pending", "payment_status": "pending",
        "payment_method": "cash", "source": "web", "awaiting": True, "tracks_readiness": True,
        "is_ready": False, "ready_manual": False, "confirm_minutes": 15, "minutes_left": 12,
        "admin_url": "https://x.y/admin/orders",
    }
    base.update(kw)
    return base


def buttons(rows):
    return [b for row in rows for b in row]


class CallbackTests(unittest.TestCase):
    def test_roundtrip(self):
        self.assertEqual(ui.parse_callback(ui.build_callback(ui.ACT_ACCEPT, 12)), ("acc", 12, None))
        self.assertEqual(ui.parse_callback(ui.build_callback(ui.ACT_REJECT_DO, 7, "out_of_stock")), ("rjd", 7, "out_of_stock"))

    def test_rejects_garbage(self):
        for bad in (None, 5, "", "ao", "ao:acc", "ao:zzz:1", "x:acc:1", "ao:acc:abc", "ao:acc:0",
                    "ao:acc:-3", "ao:acc:1:2:3", "ao:acc:1:x", "ao:rjd:1", "ao:rjd:1:hack", "ao:" + "a" * 80):
            self.assertIsNone(ui.parse_callback(bad), bad)

    def test_unknown_action_cannot_be_built(self):
        with self.assertRaises(ValueError):
            ui.build_callback("boom", 1)

    def test_all_callbacks_fit_telegram_limit(self):
        for v in (view(), view(awaiting=False), view(awaiting=False, is_ready=True, ready_manual=True), view(status="cancelled")):
            for b in buttons(ui.render_keyboard(v) + ui.reject_keyboard(v["id"])):
                if "callback_data" in b:
                    self.assertLessEqual(len(b["callback_data"].encode()), 64)
                    self.assertIsNotNone(ui.parse_callback(b["callback_data"]), b)


class StateTests(unittest.TestCase):
    def test_states(self):
        self.assertEqual(ui.state_of(view()), ui.S_AWAITING)
        self.assertEqual(ui.state_of(view(awaiting=False)), ui.S_PROCESSING)
        self.assertEqual(ui.state_of(view(awaiting=False, is_ready=True)), ui.S_READY)
        self.assertEqual(ui.state_of(view(awaiting=False, source="pos", tracks_readiness=False)), ui.S_DONE)
        self.assertEqual(ui.state_of(view(status="cancelled")), ui.S_CANCELLED)
        self.assertEqual(ui.state_of(view(payment_status="void")), ui.S_CANCELLED)

    def test_paid_order_cannot_be_cancelled_from_telegram(self):
        v = view(awaiting=False, status="completed", payment_status="paid", payment_method="gateway")
        acts = [ui.parse_callback(b["callback_data"])[0] for b in buttons(ui.render_keyboard(v)) if "callback_data" in b]
        self.assertEqual(acts, [ui.ACT_READY])


class KeyboardTests(unittest.TestCase):
    def acts(self, v):
        return [ui.parse_callback(b["callback_data"])[0] for b in buttons(ui.render_keyboard(v)) if "callback_data" in b]

    def test_awaiting_has_accept_and_reject(self):
        self.assertEqual(self.acts(view()), ["acc", "rjc"])

    def test_processing_has_ready_and_cancel(self):
        self.assertEqual(self.acts(view(awaiting=False)), ["rdy", "rjc"])

    def test_manual_ready_can_be_undone_auto_ready_cannot(self):
        self.assertIn("unr", self.acts(view(awaiting=False, is_ready=True, ready_manual=True)))
        self.assertNotIn("unr", self.acts(view(awaiting=False, is_ready=True, ready_manual=False)))

    def test_cancelled_has_only_links(self):
        v = view(status="cancelled", payment_status="void", cancel_reason="out_of_stock", awaiting=False)
        rows = ui.render_keyboard(v)
        self.assertTrue(all("url" in b for b in buttons(rows)))
        self.assertIn("Alasan: Stok habis", ui.render_text(v))

    def test_wa_button_prefilled_and_encoded(self):
        v = view(awaiting=False, is_ready=True)
        url = [b["url"] for b in buttons(ui.render_keyboard(v)) if "wa.me" in b.get("url", "")][0]
        self.assertTrue(url.startswith("https://wa.me/6281234567890?text="))
        self.assertIn("Budi", url)
        self.assertNotIn(" ", url)

    def test_no_phone_no_wa_button(self):
        v = view(customer_phone="")
        self.assertFalse([b for b in buttons(ui.render_keyboard(v)) if "wa.me" in b.get("url", "")])

    def test_reject_menu_lists_every_reason_and_back(self):
        parsed = [ui.parse_callback(b["callback_data"]) for b in buttons(ui.reject_keyboard(5))]
        reasons = {p[2] for p in parsed if p[0] == ui.ACT_REJECT_DO}
        self.assertEqual(reasons, set(ui.REASON_LABELS))
        self.assertIn(ui.ACT_REFRESH, [p[0] for p in parsed])


class TextTests(unittest.TestCase):
    def test_new_order_text(self):
        text = ui.render_text(view())
        self.assertIn("PESANAN WEB BARU", text)
        self.assertIn("2× Katsu", text)
        self.assertIn("Rp 40.000", text)
        self.assertIn("Terima dalam 12 menit", text)

    def test_reminder_headline(self):
        self.assertIn("SEGERA TERIMA", ui.render_text(view(banner="reminder", minutes_left=5)))
        self.assertNotIn("SEGERA TERIMA", ui.render_text(view(banner="reminder", awaiting=False)))

    def test_auto_cancel_message(self):
        text = ui.render_text(view(status="cancelled", cancelled_by="sistem", cancel_reason="other", awaiting=False))
        self.assertIn("DIBATALKAN OTOMATIS", text)
        self.assertIn("Tidak diterima kasir dalam 15 menit.", text)

    def test_last_event_line(self):
        v = view(awaiting=False, last_event={"label": "Diterima", "actor": "@wawan", "channel_label": "Telegram"})
        self.assertIn("↳ Diterima · @wawan · Telegram", ui.render_text(v))

    def test_table_and_takeaway(self):
        self.assertIn("Meja 5", ui.render_text(view(table_number="5")))
        self.assertIn("Jenis: Bungkus", ui.render_text(view(service_type="takeaway", table_number="5")))
        self.assertNotIn("Meja", ui.render_text(view(service_type="takeaway", table_number="5")))

    def test_queue_text(self):
        self.assertIn("Tidak ada order", ui.render_queue([]))
        items = [{"id": i, "order_number": f"M{i}", "customer_name": "A", "tag": "🛎", "minutes": 3} for i in range(1, 20)]
        out = ui.render_queue(items)
        self.assertIn("(19)", out)
        self.assertIn("dan 7 lainnya", out)


class ReportTests(unittest.TestCase):
    def summary(self, **kw):
        s = {
            "date_label": "Selasa, 27 Oktober 2026",
            "today": {"orders": 30, "web": 12, "pos": 18, "dine_in": 25, "takeaway": 5, "cancelled": 2,
                      "auto_cancelled": 1, "cancel_reasons": {"stok habis": 1, "lainnya": 1}, "items_sold": 61,
                      "revenue": 1250000, "avg_order": 41666},
            "queue": {"awaiting": 0, "late": 1, "unpaid": 2, "unpaid_total": 80000, "refunds": 0},
            "compare": {"label": "Selasa lalu (jam yang sama)", "orders": 25, "revenue": 1000000},
            "busy_hours": [{"hour": 11, "orders": 4}, {"hour": 12, "orders": 12}],
            "peak_hour": 12,
            "service": {"avg_accept_minutes": 2.4, "avg_ready_minutes": 14.0},
            "top_menus": [{"name": "Katsu", "qty": 20}],
            "staff": [{"actor": "Wawan", "accepted": 5, "ready": 4, "cancelled": 0}],
        }
        s.update(kw)
        return s

    def test_full_report(self):
        text = rf.format_daily_report(self.summary())
        for needle in ("RINGKASAN Selasa, 27 Oktober 2026", "Order: 30", "Rp 1.250.000", "order ↑ 20%", "omzet ↑ 25%",
                       "Dibatalkan: 2 (1 otomatis)", "Puncak: 12.00", "1. Katsu — 20", "Wawan: terima 5, siap 4",
                       "1 telat", "2 belum dibayar (Rp 80.000)"):
            self.assertIn(needle, text)

    def test_money_hidden_when_none(self):
        s = self.summary()
        s["today"]["revenue"] = None
        s["today"]["avg_order"] = None
        s["compare"]["revenue"] = None
        s["queue"]["unpaid_total"] = None
        text = rf.format_daily_report(s)
        self.assertNotIn("Omzet", text)
        self.assertNotIn("Rp", text)

    def test_clean_day_message(self):
        s = self.summary(queue={"awaiting": 0, "late": 0, "unpaid": 0, "refunds": 0})
        self.assertIn("Tidak ada tagihan atau antrean tertinggal", rf.format_daily_report(s))

    def test_delta_edge_cases(self):
        self.assertIsNone(rf.delta_text(5, 0))
        self.assertIsNone(rf.delta_text(5, None))
        self.assertEqual(rf.delta_text(10, 10), "= sama")
        self.assertEqual(rf.delta_text(5, 10), "↓ 50%")

    def test_minutes_text(self):
        self.assertEqual(rf.minutes_text(None), "-")
        self.assertEqual(rf.minutes_text(0.3), "<1 mnt")
        self.assertEqual(rf.minutes_text(14), "14 mnt")
        self.assertEqual(rf.minutes_text(120), "2.0 jam")

    def test_empty_day_does_not_crash(self):
        text = rf.format_daily_report({"today": {}, "queue": {}})
        self.assertIn("Order: 0", text)


if __name__ == "__main__":
    unittest.main()
