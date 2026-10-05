import math
from decimal import Decimal

# Harga web = harga POS + 1%, dibulatkan ke atas ke kelipatan 500.
# SATU-SATUNYA tempat aturan ini ditulis (views & serializers import dari sini).
WEB_MARKUP   = Decimal("1.01")
WEB_ROUND_TO = 500


def web_price(price):
    marked_up = Decimal(str(price)) * WEB_MARKUP
    return Decimal(int(math.ceil(marked_up / WEB_ROUND_TO) * WEB_ROUND_TO))