from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Cart System API", description="FastAPI Day 5 Assignment - Cart System")

# ─────────────────────────────────────────────
# PRODUCT DATABASE (in-memory)
# ─────────────────────────────────────────────
products = [
    {"product_id": 1, "name": "Wireless Mouse", "price": 499, "in_stock": True},
    {"product_id": 2, "name": "Notebook",       "price": 99,  "in_stock": True},
    {"product_id": 3, "name": "USB Hub",         "price": 299, "in_stock": False},  # Out of stock!
    {"product_id": 4, "name": "Pen Set",         "price": 49,  "in_stock": True},
]

# ─────────────────────────────────────────────
# IN-MEMORY STORAGE (resets on server restart)
# ─────────────────────────────────────────────
cart = []        # List of cart items
orders = []      # List of placed orders
order_counter = {"count": 0}  # Auto-increment order ID


# ─────────────────────────────────────────────
# PYDANTIC MODEL FOR CHECKOUT
# ─────────────────────────────────────────────
class CheckoutRequest(BaseModel):
    customer_name: str
    delivery_address: str


# ─────────────────────────────────────────────
# HELPER: Find product by ID
# ─────────────────────────────────────────────
def get_product(product_id: int):
    for p in products:
        if p["product_id"] == product_id:
            return p
    return None


# ─────────────────────────────────────────────
# ROOT
# ─────────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "Welcome to the Cart System API!", "docs": "/docs"}


# ─────────────────────────────────────────────
# Q1 & Q4 — POST /cart/add
# Add item to cart OR update quantity if already present
# ─────────────────────────────────────────────
@app.post("/cart/add")
def add_to_cart(product_id: int, quantity: int = 1):
    # Step 1: Check product exists
    product = get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail=f"Product with id={product_id} not found")

    # Step 2: Check if product is in stock
    if not product["in_stock"]:
        raise HTTPException(status_code=400, detail=f"{product['name']} is out of stock")

    # Step 3: If product already in cart → update quantity (Q4 logic)
    for item in cart:
        if item["product_id"] == product_id:
            item["quantity"] += quantity
            item["subtotal"] = item["unit_price"] * item["quantity"]
            return {"message": "Cart updated", "cart_item": item}

    # Step 4: New product → add to cart
    cart_item = {
        "product_id": product["product_id"],
        "product_name": product["name"],
        "quantity": quantity,
        "unit_price": product["price"],
        "subtotal": product["price"] * quantity,
    }
    cart.append(cart_item)
    return {"message": "Added to cart", "cart_item": cart_item}


# ─────────────────────────────────────────────
# Q2 — GET /cart
# View all cart items with grand total
# ─────────────────────────────────────────────
@app.get("/cart")
def view_cart():
    if not cart:
        return {"message": "Cart is empty"}
    grand_total = sum(item["subtotal"] for item in cart)
    return {
        "items": cart,
        "item_count": len(cart),
        "grand_total": grand_total,
    }


# ─────────────────────────────────────────────
# Q5 — DELETE /cart/{product_id}
# Remove a specific product from the cart
# ─────────────────────────────────────────────
@app.delete("/cart/{product_id}")
def remove_from_cart(product_id: int):
    for item in cart:
        if item["product_id"] == product_id:
            cart.remove(item)
            return {"message": f"{item['product_name']} removed from cart"}
    raise HTTPException(status_code=404, detail=f"Product id={product_id} not found in cart")


# ─────────────────────────────────────────────
# Q5 — POST /cart/checkout
# Checkout: create an order per cart item, then clear cart
# BONUS: returns 400 if cart is empty
# ─────────────────────────────────────────────
@app.post("/cart/checkout")
def checkout(request: CheckoutRequest):
    # BONUS — Handle empty cart gracefully
    if not cart:
        raise HTTPException(status_code=400, detail="Cart is empty — add items first")

    placed_orders = []
    grand_total = 0

    for item in cart:
        order_counter["count"] += 1
        order = {
            "order_id": order_counter["count"],
            "customer_name": request.customer_name,
            "delivery_address": request.delivery_address,
            "product": item["product_name"],
            "quantity": item["quantity"],
            "unit_price": item["unit_price"],
            "total_price": item["subtotal"],
        }
        orders.append(order)
        placed_orders.append(order)
        grand_total += item["subtotal"]

    cart.clear()  # Empty the cart after checkout

    return {
        "message": "Checkout successful!",
        "customer_name": request.customer_name,
        "orders_placed": placed_orders,
        "grand_total": grand_total,
        "cart_status": "Cart is now empty",
    }


# ─────────────────────────────────────────────
# Q5 & Q6 — GET /orders
# View all placed orders
# ─────────────────────────────────────────────
@app.get("/orders")
def get_orders():
    if not orders:
        return {"message": "No orders placed yet", "orders": [], "total_orders": 0}
    return {
        "orders": orders,
        "total_orders": len(orders),
    }