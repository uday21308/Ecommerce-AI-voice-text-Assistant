# orders.py
import csv
import ast
import uuid
from datetime import datetime, timedelta
from langsmith import traceable

ORDERS_CSV = "orders.csv"

ORDER_FIELDS = [
    "order_id",
    "user_email",
    "user_name",
    "items",
    "total_amount",
    "currency",
    "status",
    "placed_date",
    "estimated_delivery"
]


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
                    "total_amount": float(r.get("total_amount", 0)),
                    "currency": r.get("currency"),
                    "status": r.get("status"),
                    "placed_date": r.get("placed_date"),
                    "estimated_delivery": r.get("estimated_delivery"),
                }
    except FileNotFoundError:
        print(f"[orders] {csv_path} not found.")
    return orders


def _write_orders_to_csv():
    with open(ORDERS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=ORDER_FIELDS)
        writer.writeheader()
        for o in _ORDERS.values():
            writer.writerow({
                "order_id": o["order_id"],
                "user_email": o["user_email"],
                "user_name": o["user_name"],
                "items": str(o["items"]),
                "total_amount": o["total_amount"],
                "currency": o["currency"],
                "status": o["status"],
                "placed_date": o["placed_date"],
                "estimated_delivery": o["estimated_delivery"],
            })


# Load once at startup
_ORDERS = load_orders()


# --------------------------------------------------
# ORDER STATUS TOOL (UNCHANGED)
# --------------------------------------------------
@traceable(name="order_status_lookup")
def get_order_status(order_id: str, user_email: str = None):
    if not order_id:
        return None

    o = _ORDERS.get(order_id)

    if o is None:
        for oid, data in _ORDERS.items():
            if oid.lower() == order_id.lower():
                o = data
                break

    if o and user_email:
        if user_email.lower() != (o.get("user_email", "").lower()):
            return {"error": "order_found_but_email_mismatch"}

    return o


# --------------------------------------------------
# CREATE ORDER TOOL (NEW)
# --------------------------------------------------
@traceable(name="create_order")
def create_order(product: dict, quantity: int, user_email: str, user_name: str):
    order_id = f"ORD{uuid.uuid4().int % 1_000_000}"

    placed_date = datetime.now()
    estimated_delivery = placed_date + timedelta(days=7)

    total_amount = float(product["final_price"]) * quantity

    new_order = {
        "order_id": order_id,
        "user_email": user_email,
        "user_name": user_name,
        "items": [{
            "prod_id": product["prod_id"],
            "title": product["title"],
            "qty": quantity,
            "price": product["final_price"],
        }],
        "total_amount": round(total_amount, 2),
        "currency": product.get("currency", "INR"),
        "status": "Placed",
        "placed_date": placed_date.strftime("%d-%m-%Y"),
        "estimated_delivery": estimated_delivery.strftime("%d-%m-%Y"),
    }

    # Update in-memory store
    _ORDERS[order_id] = new_order

    # Persist to CSV
    _write_orders_to_csv()

    return new_order
