from rso_cart.db import create_cart_collection_if_not_exists
from rso_cart.utils import loki_handler
import logging
import sys

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(loki_handler)


class ProductQuantity:
    def __init__(self, product_id, quantity):
        self.product_id = product_id
        self.quantity = quantity

    def to_dict(self):
        return {"product_id": self.product_id, "quantity": self.quantity}


class CartInfo:
    def __init__(self, user_id, contents):
        self.user_id = user_id
        self.contents = contents

    def get_user_id(self):
        return self.user_id

    def get_contents(self):
        return self.contents

    def to_dict(self):
        return {"user_id": self.user_id, "contents": self.contents}


def get_cart_info(db_conn, user_id):
    """Fetches cart information for the user with the
    specified ID from the database using the provided DB connection object.

    Args:
        db_conn (None): The DB cpnnection.
        user_id (str): The user ID.

    Returns:
        CartInfo: An object containing cart information.
    """
    create_cart_collection_if_not_exists(db_conn)

    cart = db_conn["cart"].find_one({"user_id": user_id})
    if cart is None:
        logger.info(f"No cart found for user {user_id}")
        return CartInfo(user_id, [])
    else:
        user_id = cart["user_id"]
        contents = cart["contents"]
        return CartInfo(user_id, contents)


def cart_contains_product(contents: list[ProductQuantity], product_id: str) -> bool:
    for prod_quantity_obj in contents:
        if prod_quantity_obj.product_id == product_id:
            return True

    return False


def get_product_quantity_object_in_cart(
    contents: list[ProductQuantity], product_id: str
) -> ProductQuantity:
    for prod_quantity_obj in contents:
        if prod_quantity_obj["product_id"] == product_id:
            return prod_quantity_obj

    return None


def update_product_quantity_in_cart(
    contents: list[ProductQuantity], product_id: str, quantity: int
):
    for prod_quantity_obj in contents:
        if prod_quantity_obj["product_id"] == product_id:
            prod_quantity_obj["quantity"] = quantity


def delete_product_from_list(contents: list[ProductQuantity], product_id: str):
    i = 0
    while i < len(contents):
        if contents[i]["product_id"] == product_id:
            break

    contents = contents[:i] + contents[i + 1 :]


def add_product_to_cart(cart_info: CartInfo, product_id: str) -> CartInfo:
    uid = cart_info.get_user_id()

    contents = cart_info.get_contents().copy()
    logger.info(f"Old contents: {contents}")

    product_quantity = get_product_quantity_object_in_cart(contents, product_id)
    if product_quantity is not None:
        amount = product_quantity["quantity"]
        update_product_quantity_in_cart(contents, product_id, amount + 1)
        logger.info(f"New amount: {amount + 1}")
    else:
        new_product = ProductQuantity(product_id, 1).to_dict()
        contents.append(new_product)

    new_cart_info = CartInfo(uid, contents)
    logger.info(new_cart_info.to_dict())

    return new_cart_info


def decrease_quantity_of_product_in_cart(
    cart_info: CartInfo, product_id: str
) -> CartInfo:
    uid = cart_info.get_user_id()

    contents = cart_info.get_contents().copy()
    logger.info(f"Old contents: {contents}")

    product_quantity = get_product_quantity_object_in_cart(contents, product_id)
    if product_quantity is not None and product_quantity["quantity"] > 1:
        amount = product_quantity["quantity"]
        update_product_quantity_in_cart(contents, product_id, amount - 1)
        logger.info(f"New amount: {amount - 1}")
    else:
        # remove the product altogether from the cart
        delete_product_from_list(contents, product_id)

    new_cart_info = CartInfo(uid, contents)
    logger.info(new_cart_info.to_dict())

    return new_cart_info
