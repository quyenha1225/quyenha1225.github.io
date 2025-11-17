import tkinter as tk
from tkinter import messagebox

from ui.frames.login_frame import LoginFrame
from ui.components.sidebar import Sidebar
from ui.components.header import Header
from ui.frames.books_frame import BooksFrame
from ui.frames.borrowers_frame import BorrowersFrame
from ui.frames.employees_frame import EmployeesFrame
from ui.frames.statistics_frame import StatisticsFrame
from database.db import get_collection



class LibraryApp(tk.Tk):
    def __init__(self, user: dict):
        super().__init__()

        # ===== LƯU THÔNG TIN USER ĐỂ CÁC FRAME KHÁC DÙNG =====
        self.current_user_id = user.get("employee_id")
        self.is_admin = bool(user.get("is_admin", False))
        self.current_username = user.get("username")
        self.current_name = user.get("name")

        print(
            f"APP START WITH: id={self.current_user_id}, "
            f"is_admin={self.is_admin}, username={self.current_username}"
        )

        # ===== CẤU HÌNH CỬA SỔ CHÍNH (KHÔNG FULLSCREEN) =====
        self.title("Quản Lý Thư Viện")
        self.geometry("1200x700")        # có border, có nút thu nhỏ/phóng to
        self.configure(bg="#f0f0f0")

        # ===== CONTAINER CHÍNH =====
        self.container = tk.Frame(self, bg="white")
        self.container.pack(fill="both", expand=True)

        # Header
        self.header = Header(self.container, self, exit_cmd=self.logout)
        self.header.pack(fill="x")

        # Main layout
        main = tk.Frame(self.container, bg="white")
        main.pack(fill="both", expand=True)

        # Sidebar
        self.sidebar = Sidebar(main, self.show_frame)
        self.sidebar.grid(row=0, column=0, sticky="ns")

        # Khu vực nội dung
        self.content_frame = tk.Frame(main, bg="white")
        self.content_frame.grid(row=0, column=1, sticky="nsew")

        main.grid_rowconfigure(0, weight=1)
        main.grid_columnconfigure(1, weight=1)

        # ===== CÁC FRAME CON =====
        self.frames = {}
        for F in (BooksFrame, BorrowersFrame, EmployeesFrame, StatisticsFrame):
            frame = F(self.content_frame, self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # Mặc định mở trang sách
        self.show_frame("BooksFrame")

    def show_frame(self, name: str):
        frame = self.frames[name]
        frame.tkraise()

    def logout(self):
        if messagebox.askyesno("Đăng xuất", "Bạn có chắc muốn đăng xuất?"):
            self.destroy()
            main()  # quay lại màn hình login


def main():
    """Khởi động app: mở form login trước."""
    # ===== TEST KẾT NỐI MONGODB BẰNG get_collection =====
    try:
        books_col = get_collection("books")
        # gọi thử 1 lệnh đơn giản để đảm bảo kết nối OK
        _ = books_col.find_one({})
    except Exception as e:
        messagebox.showerror("Lỗi CSDL", f"Không thể kết nối MongoDB:\n{e}")
        return

    # ===== CỬA SỔ GỐC CHO LOGIN =====
    root = tk.Tk()
    root.withdraw()  # Ẩn, chỉ làm parent cho LoginFrame

    LoginFrame(
        root,
        on_success=lambda user: (
            root.destroy(),
            LibraryApp(user).mainloop()
        )
    )

    root.mainloop()


if __name__ == "__main__":
    main()
