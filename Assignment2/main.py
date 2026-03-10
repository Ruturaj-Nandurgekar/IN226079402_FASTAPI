import uvicorn
from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI()

# product list acting as our database
products = [
    {"id": 1, "name": "Wireless Mouse",      "price": 499,  "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook",            "price": 99,   "category": "Stationery",  "in_stock": True},
    {"id": 3, "name": "USB Hub",             "price": 799,  "category": "Electronics", "in_stock": False},
    {"id": 4, "name": "Pen Set",             "price": 49,   "category": "Stationery",  "in_stock": True},
    {"id": 5, "name": "Laptop Stand",        "price": 1299, "category": "Electronics", "in_stock": True},
    {"id": 6, "name": "Mechanical Keyboard", "price": 2499, "category": "Electronics", "in_stock": True},
    {"id": 7, "name": "Webcam",             "price": 1899, "category": "Electronics", "in_stock": False},
]

orders = []
feedback = []


# ==================================================
#  DAY 1 - basic endpoints
# ==================================================

# returns all products with a count
@app.get("/products")
def get_products():
    return {"products": products, "total": len(products)}


# returns products filtered by category name
# ignores uppercase/lowercase difference
@app.get("/products/category/{category_name}")
def get_category(category_name: str):
    filtered_products = []
    for p in products:
        if p["category"].lower() == category_name.lower():
            filtered_products.append(p)
    if len(filtered_products) == 0:
        return {"error": "No products found in this category"}
    return {"category": category_name, "products": filtered_products, "total": len(filtered_products)}


# shows only products that are currently available
@app.get("/products/instock")
def get_instock_products():
    instock_list = []
    for p in products:
        if p["in_stock"] == True:
            instock_list.append(p)
    return {"in_stock_products": instock_list, "count": len(instock_list)}


# gives a store-level overview with counts and categories
@app.get("/store/summary")
def get_store_summary():
    in_stock_count = 0
    categories_set = set()
    for p in products:
        if p["in_stock"]:
            in_stock_count += 1
        categories_set.add(p["category"])
    out_of_stock = len(products) - in_stock_count
    return {
        "store_name":     "My E-commerce Store",
        "total_products": len(products),
        "in_stock":       in_stock_count,
        "out_of_stock":   out_of_stock,
        "categories":     list(categories_set)
    }


# ==================================================
#  DAY 2 - new endpoints
#
#  IMPORTANT: fixed routes like /filter, /summary,
#  /instock must be defined BEFORE any route that
#  has a path variable like /{keyword} or /{id}
#  otherwise FastAPI will treat the word as a variable
# ==================================================


# Day 2 Q1 - filter by min price, max price or category
# these can be combined together in one request
# example: /products/filter?min_price=100&max_price=600
@app.get("/products/filter")
def filter_products(
    category:  Optional[str] = None,
    max_price: Optional[int] = None,
    min_price: int = Query(None, description="Minimum price filter")
):
    result = products.copy()

    # apply category filter if given
    if category:
        new_result = []
        for p in result:
            if p["category"].lower() == category.lower():
                new_result.append(p)
        result = new_result

    # apply max price filter if given
    if max_price:
        new_result = []
        for p in result:
            if p["price"] <= max_price:
                new_result.append(p)
        result = new_result

    # apply min price filter if given
    if min_price:
        new_result = []
        for p in result:
            if p["price"] >= min_price:
                new_result.append(p)
        result = new_result

    if len(result) == 0:
        return {"message": "No products found with the given filters"}

    return {"products": result, "total": len(result)}


# Day 2 Q4 - dashboard showing product stats
# returns cheapest, most expensive, counts and categories
@app.get("/products/summary")
def product_summary():
    in_stock_list  = []
    out_stock_list = []
    categories_set = set()

    for p in products:
        if p["in_stock"]:
            in_stock_list.append(p)
        else:
            out_stock_list.append(p)
        categories_set.add(p["category"])

    most_expensive = max(products, key=lambda p: p["price"])
    cheapest       = min(products, key=lambda p: p["price"])

    return {
        "total_products":     len(products),
        "in_stock_count":     len(in_stock_list),
        "out_of_stock_count": len(out_stock_list),
        "most_expensive":     {"name": most_expensive["name"], "price": most_expensive["price"]},
        "cheapest":           {"name": cheapest["name"],       "price": cheapest["price"]},
        "categories":         list(categories_set)
    }


# Day 1 Q5 - search products by a keyword in the name
# works even if you type in all caps
@app.get("/products/search/{keyword}")
def search_product(keyword: str):
    matches = []
    for p in products:
        if keyword.lower() in p["name"].lower():
            matches.append(p)
    if not matches:
        return {"message": "No products matched your search"}
    return {"keyword": keyword, "results": matches, "total_matches": len(matches)}


# Day 2 Q2 - returns only the name and price of a product
# useful when the full product details are not needed
@app.get("/products/{product_id}/price")
def get_product_price(product_id: int):
    for product in products:
        if product["id"] == product_id:
            return {"name": product["name"], "price": product["price"]}
    return {"error": "Product not found"}


# ==================================================
#  POST ENDPOINTS - test these in Swagger UI
#  open: http://127.0.0.1:8000/docs
# ==================================================


# Day 2 Q3 - customer feedback with validation
# rating must be between 1 and 5, comment is optional
class CustomerFeedback(BaseModel):
    customer_name: str          = Field(..., min_length=2, max_length=100)
    product_id:    int          = Field(..., gt=0)
    rating:        int          = Field(..., ge=1, le=5)
    comment:       Optional[str] = Field(None, max_length=300)

@app.post("/feedback")
def submit_feedback(data: CustomerFeedback):
    feedback.append(data.model_dump())
    return {
        "message":        "Feedback submitted successfully",
        "feedback":       data.model_dump(),
        "total_feedback": len(feedback)
    }


# Day 2 Q5 - bulk order for companies
# each item has a product id and quantity
# if a product is out of stock it goes to the failed list
class OrderItem(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity:   int = Field(..., gt=0, le=50)

class BulkOrder(BaseModel):
    company_name:  str             = Field(..., min_length=2)
    contact_email: str             = Field(..., min_length=5)
    items:         List[OrderItem] = Field(..., min_length=1)

@app.post("/orders/bulk")
def place_bulk_order(order: BulkOrder):
    confirmed   = []
    failed      = []
    grand_total = 0

    for item in order.items:
        # search for the product by id
        product = None
        for p in products:
            if p["id"] == item.product_id:
                product = p
                break

        if not product:
            failed.append({"product_id": item.product_id, "reason": "Product not found"})
        elif not product["in_stock"]:
            failed.append({"product_id": item.product_id, "reason": f"{product['name']} is out of stock"})
        else:
            subtotal = product["price"] * item.quantity
            grand_total += subtotal
            confirmed.append({"product": product["name"], "qty": item.quantity, "subtotal": subtotal})

    return {
        "company":     order.company_name,
        "confirmed":   confirmed,
        "failed":      failed,
        "grand_total": grand_total
    }


# ==================================================
#  BONUS - order status tracker
#  new orders start as pending
#  warehouse can confirm them using PATCH
# ==================================================

class OrderRequest(BaseModel):
    user_name:  str
    product_id: int
    quantity:   int

# place a new order - starts with status pending
@app.post("/orders")
def place_order(order_data: OrderRequest):
    for p in products:
        if p["id"] == order_data.product_id:
            if not p["in_stock"]:
                return {"error": "Out of stock"}
            new_order = {
                "order_id":   len(orders) + 1,
                "user_name":  order_data.user_name,
                "product_id": order_data.product_id,
                "quantity":   order_data.quantity,
                "status":     "pending"
            }
            orders.append(new_order)
            return {"message": "Order placed", "order": new_order}
    return {"error": "Product not found"}

# fetch a single order by its id
@app.get("/orders/{order_id}")
def get_order(order_id: int):
    for order in orders:
        if order["order_id"] == order_id:
            return {"order": order}
    return {"error": "Order not found"}

# confirm an order - changes status from pending to confirmed
@app.patch("/orders/{order_id}/confirm")
def confirm_order(order_id: int):
    for order in orders:
        if order["order_id"] == order_id:
            order["status"] = "confirmed"
            return {"message": "Order confirmed", "order": order}
    return {"error": "Order not found"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)