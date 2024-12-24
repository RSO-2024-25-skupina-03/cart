from rso_cart.db import connect_to_database, create_cart_collection_if_not_exists
from rso_cart.cart_utils import (
    get_cart_info,
    add_product_to_cart,
    decrease_quantity_of_product_in_cart,
)
from fastapi import FastAPI
import uvicorn

app = FastAPI()


@app.get("/")
async def root():
    """
    Returns a message.
    """
    return {"status": "Cart API online"}


@app.get("/cart/{uid}")
async def get_cart(uid):
    db_conn = connect_to_database("mongo", "rso_shop")
    cart_info = get_cart_info(db_conn, uid)
    return cart_info.to_dict()


@app.post("/cart/{uid}/{pid}")
async def add_to_cart(uid, pid):
    db_conn = connect_to_database("mongo", "rso_shop")

    # create the collection if needed
    create_cart_collection_if_not_exists(db_conn)

    cart_info = get_cart_info(db_conn, uid)
    new_cart_info = add_product_to_cart(cart_info, pid)
    new_contents = new_cart_info.get_contents()

    cart = db_conn["cart"].find_one({"user_id": uid})
    if cart is None:
        db_conn["cart"].insert_one({"user_id": uid, "contents": new_contents})
    else:
        query = {"user_id": uid}
        new_value = {"$set": {"user_id": uid, "contents": new_contents}}

        db_conn["cart"].update_one(query, new_value)

    return new_cart_info.to_dict()


@app.delete("/cart/{uid}/{pid}")
async def delete_from_cart(uid, pid):
    db_conn = connect_to_database("mongo", "rso_shop")
    cart_info = get_cart_info(db_conn, uid)
    new_cart_info = decrease_quantity_of_product_in_cart(cart_info, pid)
    new_contents = new_cart_info.get_contents()

    cart = db_conn["cart"].find_one({"user_id": uid})
    if cart is None:
        db_conn["cart"].insert_one({"user_id": uid, "contents": new_contents})
    else:
        query = {"user_id": uid}
        new_value = {"$set": {"user_id": uid, "contents": new_contents}}

        db_conn["cart"].update_one(query, new_value)

    return new_cart_info.to_dict()


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8080, reload=True)
