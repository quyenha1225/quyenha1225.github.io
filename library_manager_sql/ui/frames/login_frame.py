import tkinter as tk
from tkinter import messagebox
from database.db import get_collection   # ✅ dùng get_collection, KHÔNG import db/check_login


class LoginFrame(tk.Toplevel):
    def __init__(self, master, on_success):
        """
        master    : cửa sổ root ẩn (tk.Tk)
        on_success: hàm callback nhận dict user khi đăng nhập thành công
        """
        super().__init__(master)
        self.on_success = on_success

        self.title("Đăng nhập")
        self.resizable(False, False)
        self.configure(bg="white")

        # Khi bấm nút X
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Chặn focus ra ngoài
        self.grab_set()

        self.init_ui()
        self.center_window(400, 270)

    # ------------------------------------------------------------------ UI
    def center_window(self, width, height):
        """Căn giữa cửa sổ login trên màn hình."""
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - width) // 2
        y = (sh - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def init_ui(self):
        tk.Label(
            self,
            text="Đăng nhập",
            font=("Segoe UI", 14, "bold"),
            bg="white"
        ).pack(pady=12)

        frm = tk.Frame(self, bg="white")
        frm.pack(pady=6)

        tk.Label(frm, text="Tài khoản:", bg="white").grid(
            row=0, column=0, sticky="e", padx=6, pady=6
        )
        self.txt_user = tk.Entry(frm, width=28)
        self.txt_user.grid(row=0, column=1)

        tk.Label(frm, text="Mật khẩu:", bg="white").grid(
            row=1, column=0, sticky="e", padx=6, pady=6
        )
        self.txt_pass = tk.Entry(frm, width=28, show="*")
        self.txt_pass.grid(row=1, column=1)

        btn = tk.Button(
            self,
            text="Đăng nhập",
            bg="#1f6feb",
            fg="white",
            relief="flat",
            command=self.try_login
        )
        btn.pack(pady=12)

        self.lbl_msg = tk.Label(self, text="", fg="red", bg="white")
        self.lbl_msg.pack()

        # Enter = đăng nhập, Esc = thoát
        self.bind("<Return>", lambda _e: self.try_login())
        self.bind("<Escape>", lambda _e: self.on_close())

    # ------------------------------------------------------------------ LOGIN
    def try_login(self):
        username = self.txt_user.get().strip()
        password = self.txt_pass.get().strip()

        if not username or not password:
            self.lbl_msg.config(text="Vui lòng nhập tài khoản và mật khẩu")
            return

        try:
            employees = get_collection("employees")
            doc = employees.find_one({
                "username": username,
                "password": password
            })
        except Exception as e:
            messagebox.showerror(
                "Lỗi kết nối",
                f"Không thể kết nối MongoDB:\n{e}",
                parent=self
            )
            return

        if doc:
            # Chuẩn hoá object user truyền sang LibraryApp
            user = {
                "employee_id": doc.get("employee_id"),
                "is_admin": bool(doc.get("is_admin", False)),
                "username": doc.get("username"),
                "name": doc.get("name"),
                "position": doc.get("position"),
            }
            self.on_success(user)
            self.destroy()
        else:
            self.lbl_msg.config(text="Sai tài khoản hoặc mật khẩu")

    # ------------------------------------------------------------------ EXIT
    def on_close(self):
        if messagebox.askokcancel("Thoát", "Bạn có chắc muốn thoát chương trình?", parent=self):
            self.destroy()
            # đóng luôn root ẩn
            if self.master is not None:
                self.master.destroy()