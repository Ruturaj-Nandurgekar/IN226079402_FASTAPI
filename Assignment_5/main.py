from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel

app = FastAPI()

# ── Sample Data ──────────────────────────────────────────────────────────────

products = [
    {"product_id": 1, "name": "Wireless Mouse",  "price": 499,  "category": "Electronics"},
    {"product_id": 2, "name": "USB Hub",          "price": 799,  "category": "Electronics"},
    {"product_id": 3, "name": "Notebook",         "price": 99,   "category": "Stationery"},
    {"product_id": 4, "name": "Pen Set",          "price": 49,   "category": "Stationery"},
]

orders = []
order_counter = {"id": 1}

# ── Pydantic Model ────────────────────────────────────────────────────────────

class OrderRequest(BaseModel):
    customer_name: str
    product_id: int
    quantity: int


# ─────────────────────────────────────────────────────────────────────────────
# Q1 — GET /products/search  (already built in Day 6 session)
# Test: keyword=mouse, MOUSE, e, laptop
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/products/search")
def search_products(keyword: str = Query(...)):
    results = [p for p in products if keyword.lower() in p["name"].lower()]
    if not results:
        return {"message": f"No products found for: {keyword}"}
    return {"keyword": keyword, "total_found": len(results), "products": results}


# ─────────────────────────────────────────────────────────────────────────────
# Q2 — GET /products/sort  (already built in Day 6 session)
# Test: sort_by=price&order=asc/desc, sort_by=name&order=asc/desc, sort_by=category
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/products/sort")
def sort_products(
    sort_by: str = Query("price"),
    order: str = Query("asc"),
):
    allowed = ["price", "name"]
    if sort_by not in allowed:
        return {"error": f"sort_by must be one of {allowed}. Got: '{sort_by}'"}
    sorted_list = sorted(products, key=lambda p: p[sort_by], reverse=(order == "desc"))
    return {
        "sort_by": sort_by,
        "order": order,
        "products": sorted_list,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Q3 — GET /products/page  (already built in Day 6 session)
# Test: page=1, page=2, page=3, limit=1
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/products/page")
def get_products_paged(
    page: int = Query(1, ge=1),
    limit: int = Query(2, ge=1, le=20),
):
    start = (page - 1) * limit
    paged = products[start: start + limit]
    return {
        "page": page,
        "limit": limit,
        "total": len(products),
        "total_pages": -(-len(products) // limit),
        "products": paged,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Q4 — GET /orders/search  (NEW — you write this)
# Test: customer_name=rahul, customer_name=xyz (no results)
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/orders/search")
def search_orders(customer_name: str = Query(...)):
    results = [
        o for o in orders
        if customer_name.lower() in o["customer_name"].lower()
    ]
    if not results:
        return {"message": f"No orders found for: {customer_name}"}
    return {"customer_name": customer_name, "total_found": len(results), "orders": results}


# ─────────────────────────────────────────────────────────────────────────────
# Q5 — GET /products/sort-by-category  (NEW — you write this)
# Sorts: category A→Z, then price low→high within each category
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/products/sort-by-category")
def sort_by_category():
    result = sorted(products, key=lambda p: (p["category"], p["price"]))
    return {"products": result, "total": len(result)}


# ─────────────────────────────────────────────────────────────────────────────
# Q6 — GET /products/browse  (NEW — you write this)
# Combines search + sort + pagination in one endpoint
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/products/browse")
def browse_products(
    keyword: str = Query(None),
    sort_by: str = Query("price"),
    order: str = Query("asc"),
    page: int = Query(1, ge=1),
    limit: int = Query(4, ge=1, le=20),
):
    # Step 1 — Filter by keyword (if provided)
    result = products
    if keyword:
        result = [p for p in result if keyword.lower() in p["name"].lower()]

    # Step 2 — Sort
    if sort_by in ["price", "name"]:
        result = sorted(result, key=lambda p: p[sort_by], reverse=(order == "desc"))

    # Step 3 — Paginate
    total = len(result)
    start = (page - 1) * limit
    paged = result[start: start + limit]

    return {
        "keyword": keyword,
        "sort_by": sort_by,
        "order": order,
        "page": page,
        "limit": limit,
        "total_found": total,
        "total_pages": -(-total // limit),
        "products": paged,
    }


# ─────────────────────────────────────────────────────────────────────────────
# BONUS — GET /orders/page  (BONUS — you write this)
# Paginate the orders list
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/orders/page")
def get_orders_paged(
    page: int = Query(1, ge=1),
    limit: int = Query(3, ge=1, le=20),
):
    start = (page - 1) * limit
    return {
        "page": page,
        "limit": limit,
        "total": len(orders),
        "total_pages": -(-len(orders) // limit) if orders else 0,
        "orders": orders[start: start + limit],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Helper endpoint — POST /orders  (to create test orders for Q4 & Bonus)
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/orders")
def place_order(order: OrderRequest):
    product = next((p for p in products if p["product_id"] == order.product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    new_order = {
        "order_id": order_counter["id"],
        "customer_name": order.customer_name,
        "product_id": order.product_id,
        "product_name": product["name"],
        "quantity": order.quantity,
        "total_price": product["price"] * order.quantity,
    }
    orders.append(new_order)
    order_counter["id"] += 1
    return {"message": "Order placed successfully", "order": new_order}


# ─────────────────────────────────────────────────────────────────────────────
# Basic endpoints (carry over from Day 5)
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/")
def home():
    return {"message": "FastAPI Day 6 — Search, Sort & Pagination"}


@app.get("/products")
def get_all_products():
    return {"total": len(products), "products": products}


@app.get("/products/{product_id}")
def get_product(product_id: int):
    product = next((p for p in products if p["product_id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.get("/orders")
def get_all_orders():
    return {"total": len(orders), "orders": orders}