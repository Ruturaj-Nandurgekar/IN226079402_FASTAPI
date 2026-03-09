import uvicorn
from fastapi import FastAPI

app = FastAPI()

# our database of products
products = [
    {"id": 1, "name": "Wireless Mouse", "price": 499, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook", "price": 99, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "USB-C Hub", "price": 1299, "category": "Electronics", "in_stock": False},
    {"id": 4, "name": "Pen Set", "price": 49, "category": "Stationery", "in_stock": True},
    # 3 new products for Q1
    {"id": 5, "name": "Laptop Stand", "price": 1299, "category": "Electronics", "in_stock": True},
    {"id": 6, "name": "Mechanical Keyboard", "price": 2499, "category": "Electronics", "in_stock": True},
    {"id": 7, "name": "Webcam", "price": 1899, "category": "Electronics", "in_stock": False},
]

# Q1: Get all products
@app.get("/products")
def get_products():
    return {"products": products, "total": len(products)}

# Q2: Filter by category
@app.get("/products/category/{category_name}")
def get_category(category_name: str):
    filtered_products = []
    
    # loop through to find matching category (ignoring case)
    for p in products:
        if p["category"].lower() == category_name.lower():
            filtered_products.append(p)
            
    if len(filtered_products) == 0:
        return {"error": "No products found in this category"}
        
    return {"category": category_name, "products": filtered_products, "total": len(filtered_products)}

# Q3: Get only in-stock products
@app.get("/products/instock")
def get_instock_products():
    instock_list = []
    
    for p in products:
        if p["in_stock"] == True:
            instock_list.append(p)
            
    return {"in_stock_products": instock_list, "count": len(instock_list)}

# Q4: Store summary details
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
        "store_name": "My E-commerce Store",
        "total_products": len(products),
        "in_stock": in_stock_count,
        "out_of_stock": out_of_stock,
        "categories": list(categories_set)
    }

# Q5: Search by keyword
@app.get("/products/search/{keyword}")
def search_product(keyword: str):
    matches = []
    
    for p in products:
        # Check if keyword is in the product name
        if keyword.lower() in p["name"].lower():
            matches.append(p)
            
    if not matches:
        return {"message": "No products matched your search"}
        
    return {"keyword": keyword, "results": matches, "total_matches": len(matches)}


# This allows you to run it directly with "python main.py"
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
