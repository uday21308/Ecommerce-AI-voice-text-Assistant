# orders.py
import csv
import ast
from langsmith import traceable

ORDERS_CSV = "orders.csv"

def load_orders(csv_path=ORDERS_CSV):
    orders = {}
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                order_id = r.get("order_id")
                items = r.get("items", "[]")
                try:
                    parsed_items = ast.literal_eval(items)
                except Exception:
                    parsed_items = []
                orders[order_id] = {
                    "order_id": order_id,
                    "user_email": r.get("user_email"),
                    "user_name": r.get("user_name"),
                    "items": parsed_items,
                    "total_amount": r.get("total_amount"),
                    "currency": r.get("currency"),
                    "status": r.get("status"),
                    "placed_date": r.get("placed_date"),
                    "estimated_delivery": r.get("estimated_delivery"),
                }
    except FileNotFoundError:
        print(f"[orders] {csv_path} not found.")
    return orders

_ORDERS = load_orders()

@traceable(name="order_status_lookup")
def get_order_status(order_id: str, user_email: str = None):
    if not order_id:
        return None
    o = _ORDERS.get(order_id)
    if o is None:
        # case-insensitive attempt
        for oid, data in _ORDERS.items():
            if oid.lower() == order_id.lower():
                o = data
                break
    # privacy check
    if o and user_email:
        if user_email.lower() != (o.get("user_email","").lower()):
            return {"error": "order_found_but_email_mismatch"}
    return o
