# library_system.py
import json, pyodbc, pymongo, bcrypt, uuid
from datetime import datetime, timedelta, timezone
from database.db import get_collection

# === CẤU HÌNH ===
with open("config.json", "r", encoding="utf-8") as f:
    cfg = json.load(f)

# SQL Server
def sql_conn():
    c = cfg["sql_server"]
    conn_str = f"DRIVER={c['driver']};SERVER={c['server']};DATABASE={c['database']};Trusted_Connection=yes;"
    return pyodbc.connect(conn_str)

def sql_execute(sql, params=None):
    with sql_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params or ())
        conn.commit()
        return cursor.rowcount

def sql_fetch(sql, params=None):
    with sql_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params or ())
        cols = [col[0] for col in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]

# MongoDB
mongo = pymongo.MongoClient(cfg["mongo_uri"])[cfg["database"]]
logs = mongo["system_logs"]

# === BẢO MẬT ===
def hash_pwd(p): return bcrypt.hashpw(p.encode(), bcrypt.gensalt())

def login(username, password):
    user = sql_fetch("SELECT * FROM employees WHERE username = ?", (username,))
    if not user: return None
    if bcrypt.checkpw(password.encode(), user[0]["password_hash"]):
        return {"id": user[0]["employee_id"], "name": user[0]["name"], "admin": bool(user[0]["is_admin"])}
    return None

def create_admin():
    if not sql_fetch("SELECT 1 FROM employees WHERE username='admin'"):
        sql_execute(
            "INSERT INTO employees (name, username, password_hash, is_admin) VALUES (?, ?, ?, ?)",
            ("Admin", "admin", hash_pwd("admin123"), 1)
        )

# === GHI LOG ===
def log_action(user, action, details=None):
    entry = {
        "time": datetime.now(timezone.utc),
        "user": user,
        "action": action,
        "id": str(uuid.uuid4())[:8],
        **(details or {})
    }
    logs.insert_one(entry)

# === GHI MƯỢN VÀO MONGODB ===
def record_loan_to_mongo(borrower_id, book_id, emp_id):
    borrower = sql_fetch("SELECT name FROM borrowers WHERE borrower_id = ?", (borrower_id,))[0]
    book = sql_fetch("SELECT title, category FROM books WHERE book_id = ?", (book_id,))[0]
    get_collection("loans").insert_one({
        "borrower_id": borrower_id,
        "borrower_name": borrower["name"],
        "book_id": book_id,
        "book_title": book["title"],
        "book_category": book["category"],
        "employee_id": emp_id,
        "borrow_date": datetime.now(timezone.utc),
        "is_returned": False
    })

# === MƯỢN SÁCH ===
def borrow_book(borrower_id, book_id, emp_id):
    if not sql_fetch("SELECT 1 FROM employees WHERE employee_id = ?", (emp_id,)):
        return False, "Nhân viên không tồn tại"
    book = sql_fetch("SELECT status FROM books WHERE book_id = ?", (book_id,))
    if not book or book[0]["status"] != "Có sẵn":
        return False, "Sách không có sẵn"

    sql_execute("INSERT INTO loans (borrower_id, book_id, employee_id) VALUES (?, ?, ?)",
                (borrower_id, book_id, emp_id))

    record_loan_to_mongo(borrower_id, book_id, emp_id)

    book_info = sql_fetch("SELECT title, category FROM books WHERE book_id = ?", (book_id,))[0]
    log_action("employee", "borrow_book", {
        "borrower_id": borrower_id,
        "book_id": book_id,
        "book_title": book_info["title"],
        "category": book_info["category"]
    })
    return True, "Mượn thành công"

# === TRẢ SÁCH ===
def return_book(loan_id):
    loan = sql_fetch("SELECT * FROM loans WHERE loan_id = ?", (loan_id,))
    if not loan or loan[0]["is_returned"]:
        return False, "Phiếu không tồn tại hoặc đã trả"

    sql_execute("UPDATE loans SET is_returned = 1 WHERE loan_id = ?", (loan_id,))

    get_collection("loans").update_one(
        {"book_id": loan[0]["book_id"], "is_returned": False},
        {"$set": {"is_returned": True, "return_date": datetime.now(timezone.utc)}}
    )

    log_action("employee", "return_book", {"loan_id": loan_id})
    return True, "Trả sách thành công"

# === DỌN DẸP ===
def clear_test_data():
    sql_execute("DELETE FROM loans")
    sql_execute("DELETE FROM borrowers")
    sql_execute("DELETE FROM books")
    sql_execute("DELETE FROM employees WHERE username != 'admin'")
    sql_execute("DBCC CHECKIDENT ('books', RESEED, 0)")
    sql_execute("DBCC CHECKIDENT ('borrowers', RESEED, 0)")
    print("Dọn dẹp dữ liệu test thành công!")

if __name__ == "__main__":
    create_admin()
    print("Hệ thống sẵn sàng!")