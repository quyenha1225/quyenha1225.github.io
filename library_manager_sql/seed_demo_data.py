# seed_demo_data.py
import random
from datetime import datetime, timedelta
from database.db import get_collection

def seed_borrowers_books_employees():
    borrowers_col = get_collection("borrowers")
    books_col = get_collection("books")
    employees_col = get_collection("employees")
    loans_col = get_collection("loans")
    receipts_col = get_collection("loan_receipts")

    print("Đang xóa dữ liệu cũ...")
    borrowers_col.delete_many({})
    books_col.delete_many({})
    employees_col.delete_many({})
    loans_col.delete_many({})
    receipts_col.delete_many({})

    today = datetime.today()

    # === NHÂN VIÊN ===
    print("Tạo nhân viên...")
    positions = ["Thủ thư", "Bảo vệ", "Nhân viên kho"]
    all_employee_ids = []

    employees_col.insert_one({
        "employee_id": 1, "name": "Admin Thư Viện", "position": "Quản trị viên",
        "username": "admin", "password": "admin123", "is_admin": True,
        "work_date": today, "schedule_days": "1,15"
    })
    all_employee_ids.append(1)

    employees_col.insert_one({
        "employee_id": 2, "name": "Nhân viên 1", "position": "Thủ thư",
        "username": "staff", "password": "staff123", "is_admin": False,
        "work_date": today, "schedule_days": "2,16"
    })
    all_employee_ids.append(2)

    for i in range(1, 101):
        emp_id = i + 2
        days = sorted(random.sample(range(1, 32), k=2))
        employees_col.insert_one({
            "employee_id": emp_id, "name": f"Nhân viên {emp_id}",
            "position": random.choice(positions), "username": f"user{i}",
            "password": f"user{i}", "is_admin": False,
            "work_date": today, "schedule_days": ",".join(map(str, days))
        })
        all_employee_ids.append(emp_id)

    # === SÁCH ===
    print("Tạo 500 sách...")
    categories = ["Lịch sử", "Khoa học", "Lập trình", "Văn học", "Thiếu nhi", "Kinh tế"]
    for book_id in range(1, 501):
        books_col.insert_one({
            "book_id": book_id, "title": f"Sách {book_id}",
            "author": f"Tác giả {book_id}", "published_year": random.randint(1990, 2024),
            "category": random.choice(categories), "status": "Có sẵn"
        })

    # === NGƯỜI MƯỢN ===
    print("Tạo 500 người mượn...")
    for bor_id in range(1, 501):
        phone = f"09{random.randint(10000000, 99999999)}"
        borrowers_col.insert_one({
            "borrower_id": bor_id, "name": f"Người mượn {bor_id}",
            "phone": phone, "email": f"borrower{bor_id}@example.com"
        })

    # === PHIẾU MƯỢN ===
    print("Tạo phiếu mượn + chi tiết...")
    next_receipt_id = 1
    next_loan_id = 1

    for borrower_id in range(1, 501):
        num_receipts = random.randint(0, 4)
        if num_receipts == 0: continue
        has_open = random.random() < 0.6
        open_index = num_receipts - 1 if has_open else -1

        for idx in range(num_receipts):
            base_days_ago = random.randint(15, 60) + (num_receipts - idx) * 3
            borrow_date = today - timedelta(days=base_days_ago)
            due_date = borrow_date + timedelta(days=7)
            is_open = (idx == open_index)
            return_date = None if is_open else (
                borrow_date + timedelta(days=random.randint(1, 20))
            )
            if return_date and return_date > today:
                return_date = today - timedelta(days=random.randint(1, 3))
            employee_id = random.choice(all_employee_ids)

            receipts_col.insert_one({
                "receipt_id": next_receipt_id, "borrower_id": borrower_id,
                "borrow_date": borrow_date, "due_date": due_date,
                "return_date": return_date, "employee_id": employee_id, "note": None
            })

            num_books = random.randint(1, 5)
            book_ids = random.sample(range(1, 501), k=num_books)

            for book_id in book_ids:
                book = books_col.find_one({"book_id": book_id})
                borrower = borrowers_col.find_one({"borrower_id": borrower_id})

                loan_doc = {
                    "loan_id": next_loan_id, "receipt_id": next_receipt_id,
                    "borrower_id": borrower_id, "borrower_name": borrower["name"],
                    "book_id": book_id, "book_title": book["title"],
                    "book_category": book["category"], "employee_id": employee_id,
                    "borrow_date": borrow_date, "return_date": return_date,
                    "is_returned": (return_date is not None)
                }
                loans_col.insert_one(loan_doc)
                next_loan_id += 1

                if is_open:
                    books_col.update_one({"book_id": book_id}, {"$set": {"status": "Đã mượn"}})
                else:
                    books_col.update_one(
                        {"book_id": book_id, "status": {"$ne": "Đã mượn"}},
                        {"$set": {"status": "Có sẵn"}}
                    )

            next_receipt_id += 1

    print("HOÀN TẤT! Dữ liệu demo đã sẵn sàng cho thống kê!")

# === CHỈ XÓA KHI XÁC NHẬN ===
if __name__ == "__main__":
    confirm = input("XÓA HẾT dữ liệu cũ để tạo demo mới? (y/n): ")
    if confirm.lower() == 'y':
        seed_borrowers_books_employees()
        print("Seed hoàn tất!")
    else:
        print("Hủy seed. Dữ liệu cũ được giữ nguyên.")