# test_mongodb.py
from library_system import log_action
from database.db import get_top_category_7days
import time

print("\n=== TEST MONGODB ===")

categories = ["Lập trình", "Văn học", "Khoa học", "Kinh tế", "Lịch sử"]
for i in range(10):
    cat = categories[i % len(categories)]
    log_action(
        user="staff",
        action="borrow_book",
        details={
            "book_id": i + 100,
            "book_title": f"Sách mẫu {i}",
            "category": cat
        }
    )
    time.sleep(0.01)

print("Ghi 10 log mượn sách vào MongoDB")

top = get_top_category_7days()
print("Top 5 thể loại mượn nhiều nhất (7 ngày):")
for item in top[:5]:
    print(f"  • {item[0]}: {item[1]} lượt")

print("TEST MONGODB: THÀNH CÔNG!")