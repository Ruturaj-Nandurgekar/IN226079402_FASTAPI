from fastapi import FastAPI, Response, Query
from fastapi import status
from pydantic import BaseModel

app = FastAPI()

# Starting product catalogue — 4 items by default
products = [
    {"id": 1, "name": "Wireless Mouse",  "price": 499,  "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook",        "price": 99,   "category": "Stationery",  "in_stock": True},
    {"id": 3, "name": "USB Hub",         "price": 799,  "category": "Electronics", "in_stock": False},
    {"id": 4, "name": "Pen Set",         "price": 49,   "category": "Stationery",  "in_stock": True},
]


# Small helper — returns the product dict if found, else None
def find_product(pid: int):
    for item in products:
        if item["id"] == pid:
            return item
    return None


# Schema for creating a new product
class NewProduct(BaseModel):
    name: str
    price: int
    category: str
    in_stock: bool = True


# ── GET all products ──────────────────────────────────────────────────────────

@app.get("/products")
def get_all_products():
    return {"products": products, "total": len(products)}


# ── GET single product ────────────────────────────────────────────────────────

# Q5 note: /products/audit MUST sit above this route, otherwise FastAPI
# will try to cast the string "audit" as an int and throw a validation error.

# ── Q5 — Inventory audit endpoint ────────────────────────────────────────────

@app.get("/products/audit")
def product_audit():
    in_stock_items  = [p for p in products if     p["in_stock"]]
    out_stock_items = [p for p in products if not p["in_stock"]]

    # Assume 10 units per in-stock product for total value estimate
    stock_value = sum(p["price"] * 10 for p in in_stock_items)
    priciest    = max(products, key=lambda p: p["price"])

    return {
        "total_products":    len(products),
        "in_stock_count":    len(in_stock_items),
        "out_of_stock_names": [p["name"] for p in out_stock_items],
        "total_stock_value": stock_value,
        "most_expensive":    {"name": priciest["name"], "price": priciest["price"]},
    }


# ── Bonus — Bulk category discount ───────────────────────────────────────────
# PUT /products/discount?category=Electronics&discount_percent=10
# Also placed above /products/{product_id} for the same routing reason.

@app.put("/products/discount")
def bulk_discount(
    category:         str = Query(..., description="Category to apply discount to"),
    discount_percent: int = Query(..., ge=1, le=99, description="Discount percentage"),
):
    updated = []
    for p in products:
        if p["category"] == category:
            p["price"] = int(p["price"] * (1 - discount_percent / 100))
            updated.append(p)

    if not updated:
        return {"message": f"No products found in category: {category}"}

    return {
        "message":          f"{discount_percent}% discount applied to {category}",
        "updated_count":    len(updated),
        "updated_products": updated,
    }


# ── GET /products/{product_id} ────────────────────────────────────────────────

@app.get("/products/{product_id}")
def get_product(product_id: int, response: Response):
    product = find_product(product_id)
    if not product:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"error": "Product not found"}
    return product


# ── Q1 — POST /products ───────────────────────────────────────────────────────
# Adds a new product; blocks duplicates by name (case-sensitive).

@app.post("/products", status_code=201)
def add_product(new_product: NewProduct, response: Response):
    # Reject if a product with the same name already exists
    for p in products:
        if p["name"].lower() == new_product.name.lower():
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"error": f"Product '{new_product.name}' already exists"}

    next_id = max(p["id"] for p in products) + 1
    entry = {
        "id":       next_id,
        "name":     new_product.name,
        "price":    new_product.price,
        "category": new_product.category,
        "in_stock": new_product.in_stock,
    }
    products.append(entry)
    return {"message": "Product added", "product": entry}


# ── Q2 — PUT /products/{product_id} ──────────────────────────────────────────
# Updates price and/or in_stock for an existing product.
# Both params are optional — send one or both in the same call.

@app.put("/products/{product_id}")
def update_product(
    product_id: int,
    response:   Response,
    price:      int  = Query(None, description="New price"),
    in_stock:   bool = Query(None, description="Stock availability"),
):
    product = find_product(product_id)
    if not product:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"error": "Product not found"}

    if price is not None:
        product["price"] = price

    # Use "is not None" check — False is a valid value and must not be skipped
    if in_stock is not None:
        product["in_stock"] = in_stock

    return {"message": "Product updated", "product": product}


# ── Q3 — DELETE /products/{product_id} ───────────────────────────────────────
# Removes the product permanently; returns 404 if ID doesn't exist.

@app.delete("/products/{product_id}")
def delete_product(product_id: int, response: Response):
    product = find_product(product_id)
    if not product:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"error": "Product not found"}

    products.remove(product)
    return {"message": f"Product '{product['name']}' deleted"}


# ── Q4 is a Swagger walkthrough, no new code needed ───────────────────────────
# Steps to follow in Swagger UI (http://127.0.0.1:8000/docs):
#   1. POST /products  → Smart Watch, price 3999, Electronics, in_stock false
#   2. GET  /products  → note the auto-assigned ID
#   3. PUT  /products/{id}?price=3499  → fix the pricing error
#   4. GET  /products/{id}  → confirm price is 3499
#   5. DELETE /products/{id}  → launch cancelled, remove it
#   6. GET  /products  → Smart Watch must be gone, total back to previous count