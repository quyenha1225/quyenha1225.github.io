# database/db.py
import json
from pathlib import Path
import pymongo
from datetime import datetime, timedelta, timezone

CONFIG_FILE = Path(__file__).parent / "config.json"

def load_config():
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"Config file not found: {CONFIG_FILE}")
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def get_client():
    cfg = load_config()
    return pymongo.MongoClient(cfg.get("mongo_uri", "mongodb://localhost:27017"))

def get_db():
    cfg = load_config()
    client = get_client()
    db_name = cfg.get("database")
    if not db_name:
        raise ValueError("Missing 'database' in config.json")
    return client[db_name]

def get_collection(collection_name: str):
    db = get_db()
    return db[collection_name]

# === THỐNG KÊ SIÊU NHANH ===
def get_top_category():
    pipeline = [
        {"$group": {"_id": "$book_category", "so_luot": {"$sum": 1}}},
        {"$sort": {"so_luot": -1}},
        {"$limit": 10}
    ]
    results = get_collection("loans").aggregate(pipeline)
    return [(doc["_id"] or "Khác", doc["so_luot"]) for doc in results]

def get_top_category_7days():
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    pipeline = [
        {"$match": {"borrow_date": {"$gte": seven_days_ago}}},
        {"$group": {"_id": "$book_category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    results = get_collection("loans").aggregate(pipeline)
    return [(doc["_id"] or "Khác", doc["count"]) for doc in results]

def get_top_borrower():
    pipeline = [
        {"$group": {"_id": "$borrower_name", "so_luot": {"$sum": 1}}},
        {"$sort": {"so_luot": -1}},
        {"$limit": 20}
    ]
    results = get_collection("loans").aggregate(pipeline)
    return [(doc["_id"], doc["so_luot"]) for doc in results]