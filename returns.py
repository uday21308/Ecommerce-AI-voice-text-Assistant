import csv
from datetime import datetime

RETURNS_FILE = "returns.csv"

def get_return_by_order(order_id):
    with open(RETURNS_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["order_id"].upper() == order_id.upper():
                return row
    return None


def create_return_request(order, reason):
    today = datetime.today()
    placed_date = datetime.strptime(order["placed_date"], "%d-%m-%Y")
    days_to_return = (today - placed_date).days

    item = order["items"][0]  # first product

    new_row = {
        "order_id": order["order_id"],
        "product_id": item["prod_id"],
        "User_ID": order["user_email"],
        "Order_Date": order["placed_date"],
        "Return_Date": today.strftime("%d-%m-%Y"),
        "Product_Category": "General",
        "Product_Price": order["total_amount"],
        "Order_Quantity": item["qty"],
        "Return_Reason": reason,
        "Return_Status": "Initiated",
        "Days_to_Return": days_to_return,
        "User_Age": "Unknown",
        "User_Gender": "Unknown",
        "User_Location": "Unknown",
        "Payment_Method": "Online",
        "Shipping_Method": "Standard",
        "Discount_Applied": "No"
    }

    with open(RETURNS_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=new_row.keys())
        writer.writerow(new_row)

    return new_row
