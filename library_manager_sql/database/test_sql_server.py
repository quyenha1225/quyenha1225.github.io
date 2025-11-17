# test_sql_server.py
from library_system import sql_fetch, sql_execute, create_admin, record_loan_to_mongo
print("=== TEST SQL SERVER ===")

create_admin()

sql_execute(
    "INSERT INTO books (title, author, category) VALUES (?, ?, ?)",
    ("Python Nâng Cao", "Nguyễn Văn A", "Lập trình")
)
book_id = sql_fetch("SELECT TOP 1 book_id FROM books ORDER BY book_id DESC")[0]["book_id"]
print(f"Thêm sách ID: {book_id}")

sql_execute(
    "INSERT INTO borrowers (name, phone) VALUES (?, ?)",
    ("Trần Thị B", "0901234567")
)
borrower_id = sql_fetch("SELECT TOP 1 borrower_id FROM borrowers ORDER BY borrower_id DESC")[0]["borrower_id"]
print(f"Thêm độc giả ID: {borrower_id}")

sql_execute(
    "INSERT INTO loans (borrower_id, book_id, employee_id) VALUES (?, ?, ?)",
    (borrower_id, book_id, 1)
)
print("Mượn sách thành công (trigger tự động cập nhật status)")

# GHI VÀO MONGODB ĐỂ THỐNG KÊ
record_loan_to_mongo(borrower_id, book_id, 1)

loans = sql_fetch("SELECT * FROM vw_ChiTietMuonTra")
print(f"Tổng phiếu mượn: {len(loans)}")
for l in loans:
    print(f"  • {l['TenDocGia']} mượn '{l['TenSach']}' - {l['TrangThaiMuon']}")

print("TEST SQL SERVER: THÀNH CÔNG!")