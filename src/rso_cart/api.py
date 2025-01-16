from rso_cart.db import connect_to_database, create_cart_collection_if_not_exists
from rso_cart.cart_utils import (
    get_cart_info,
    add_product_to_cart,
    decrease_quantity_of_product_in_cart,
)
from rso_cart.utils import loki_handler
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
import uvicorn
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(loki_handler)

app = FastAPI()

# metrics
Instrumentator().instrument(app).expose(app)


@app.get("/")
async def root():
    """
    Returns a message.
    """
    logger.info("GET /")
    return {"status": "Cart API online"}


@app.get("/{tenant}/cart/{uid}")
async def get_cart(tenant, uid):
    logger.info(f"GET /{tenant}/cart/{uid}")
    db_name = f"rso_shop_{tenant}"
    logger.info(f"Using database: {db_name}")
    db_conn = connect_to_database("mongo", db_name)
    cart_info = get_cart_info(db_conn, uid)
    return cart_info.to_dict()


@app.post("/{tenant}/cart/{uid}/{pid}")
async def add_to_cart(tenant, uid, pid):
    logger.info(f"POST /{tenant}/cart/{uid}/{pid}")
    db_name = f"rso_shop_{tenant}"
    logger.info(f"Using database: {db_name}")
    db_conn = connect_to_database("mongo", db_name)

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


@app.put("/{tenant}/cart/{uid}/{pid}")
async def delete_from_cart(tenant, uid, pid):
    logger.info(f"DELETE /{tenant}/cart/{uid}/{pid}")
    db_name = f"rso_shop_{tenant}"
    logger.info(f"Using database: {db_name}")
    db_conn = connect_to_database("mongo", db_name)
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


@app.delete("/{tenant}/cart/{uid}")
async def delete_cart(tenant, uid):
    logger.info(f"DELETE /{tenant}/cart/{uid}")
    db_name = f"rso_shop_{tenant}"
    logger.info(f"Using database: {db_name}")
    db_conn = connect_to_database("mongo", db_name)
    db_conn["cart"].delete_one({"user_id": uid})
    return {"status": "Cart deleted"}


@app.delete("/{tenant}/cart/{uid}/{pid}")
async def delete_product_from_cart(tenant, uid, pid):
    logger.info(f"DELETE /{tenant}/cart/{uid}/{pid}")
    db_name = f"rso_shop_{tenant}"
    logger.info(f"Using database: {db_name}")
    db_conn = connect_to_database("mongo", db_name)
    cart_info = get_cart_info(db_conn, uid)

    # remove the product altogether from the dictionary
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
    uvicorn.run(
        "api:app", host="0.0.0.0", root_path="/api/cart", port=8080, reload=True
    )
