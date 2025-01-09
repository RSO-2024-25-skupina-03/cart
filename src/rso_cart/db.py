from rso_cart.utils import loki_handler
from pymongo import MongoClient
from pymongo.errors import OperationFailure
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(loki_handler)


def _create_cart_collection(db):
    logger.info("Creating collection 'cart'!")
    # TODO check result
    db.create_collection(
        "cart",
        validator={
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["user_id", "contents"],
                "properties": {
                    "user_id": {
                        "bsonType": "string",
                        "description": "must be a string and is required",
                    },
                    "contents": {
                        "bsonType": "array",
                        "description": "must be an array and is required",
                        "items": {
                            "bsonType": "object",
                            "required": ["product_id", "quantity"],
                            "properties": {
                                "product_id": {
                                    "bsonType": "string",
                                    "description": "must be a string and is required",
                                },
                                "quantity": {
                                    "bsonType": "int",
                                    "description": "must be an integer and is required",
                                },
                            },
                        },
                    },
                },
            }
        },
    )


def create_cart_collection_if_not_exists(db):
    try:
        db.validate_collection("cart")
        logger.info("Collection 'cart' available.")
    except OperationFailure:
        # create the cart collection
        _create_cart_collection(db)


# TODO move this into commons onstead of copying accross repositories
def connect_to_database(host, dbname):
    client = MongoClient("mongo", 27017)
    db = client[dbname]
    return db
