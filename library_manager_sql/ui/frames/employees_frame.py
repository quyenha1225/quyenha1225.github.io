import tkinter as tk
from tkinter import ttk, messagebox
import datetime

from database.db import get_collection


def _status_today_from_schedule(schedule_days: str | None) -> str:
    """
    schedule_days: chuỗi '1,15' nghĩa là làm ngày 1 và 15 hàng tháng.
    Trả về: 'Có lịch làm' hoặc 'Nghỉ' dựa trên ngày hiện tại.
    """
    if not schedule_days:
        return "Nghỉ"
    today = datetime.datetime.now().day
    days = {d.strip() for d in str(schedule_days).split(",") if d.strip().isdigit()}
    return "Có lịch làm" if str(today) in days else "Nghỉ"


def _get_next_employee_id(col):
    """Tìm employee_id lớn nhất và +1 (giống IDENTITY trong SQL)."""
    last = col.find_one(sort=[("employee_id", -1)])
    return (last.get("employee_id", 0) if last else 0) + 1


class EmployeesFrame(tk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent, bg="white")
        self.controller = controller

        tk.Label(
            self,
            text="QUẢN LÝ NHÂN VIÊN",
            font=("Segoe UI", 14, "bold"),
            bg="white",
            fg="#2c3e50",
        ).pack(pady=10)

        self.create_search_frame()
        self.create_table()
        self.create_buttons()
        self.load_data()

    # ================= UI PHẦN TÌM KIẾM =================
    def create_search_frame(self):
        frame = tk.Frame(self, bg="white")
        frame.pack(fill="x", padx=10)

        tk.Label(frame, text="Tìm kiếm:", bg="white").pack(side="left")
        self.search_entry = tk.Entry(frame, width=30)
        self.search_entry.pack(side="left", padx=5)

        tk.Button(
            frame,
            text="Tìm",
            bg="#3498db",
            fg="white",
            command=self.search,
        ).pack(side="left", padx=3)

        tk.Button(
            frame,
            text="Làm mới",
            bg="#7f8c8d",
            fg="white",
            command=self.load_data,
        ).pack(side="left", padx=3)

    # ================= BẢNG DỮ LIỆU =================
    def create_table(self):
        columns = (
            "id",
            "name",
            "position",
            "username",
            "password",
            "work_date",
            "schedule",
            "status_today",
        )
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=18)

        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Họ và tên")
        self.tree.heading("position", text="Chức vụ")
        self.tree.heading("username", text="Tài khoản")
        self.tree.heading("password", text="Mật khẩu")
        self.tree.heading("work_date", text="Ngày bắt đầu")
        self.tree.heading("schedule", text="Lịch làm")
        self.tree.heading("status_today", text="Phân công hôm nay")

        self.tree.column("id", width=60, anchor="center", stretch=tk.NO)
        self.tree.column("name", width=180, stretch=tk.NO)
        self.tree.column("position", width=160, stretch=tk.NO)
        self.tree.column("username", width=160, stretch=tk.NO)
        self.tree.column("password", width=160, anchor="center", stretch=tk.NO)
        self.tree.column("work_date", width=160, anchor="center", stretch=tk.NO)
        self.tree.column("schedule", width=160, anchor="center", stretch=tk.NO)
        self.tree.column("status_today", width=160, anchor="center", stretch=tk.NO)

        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

    # ================= CÁC NÚT CHỨC NĂNG =================
    def create_buttons(self):
        frame = tk.Frame(self, bg="white")
        frame.pack(pady=5)

        is_admin = bool(getattr(self.controller, "is_admin", False))
        admin_state = "normal" if is_admin else "disabled"

        buttons = [
            ("Thêm", "#2ecc71", self.add_employee, admin_state),
            ("Sửa", "#f1c40f", self.edit_employee, admin_state),
            ("Xóa", "#e74c3c", self.delete_employee, admin_state),
            ("Kiểm tra lịch", "#3498db", self.check_today, "normal"),
        ]

        for text, color, cmd, state in buttons:
            tk.Button(
                frame,
                text=text,
                bg=color,
                fg="white",
                width=12,
                command=cmd,
                state=state,
            ).pack(side="left", padx=5)

    # ================= TIỆN ÍCH CHUNG =================
    @staticmethod
    def _clean(value):
        if value is None:
            return ""
        return str(value)

    def _load_from_cursor(self, cursor):
        """Đổ dữ liệu Mongo vào Treeview, xử lý ẩn mật khẩu + lịch làm."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        is_admin = bool(getattr(self.controller, "is_admin", False))
        current_user_id = getattr(self.controller, "current_user_id", -1)

        for doc in cursor:
            emp_id = doc.get("employee_id")
            name = doc.get("name", "")
            position = doc.get("position", "")
            username = doc.get("username", "")
            password = doc.get("password", "")

            if not is_admin and emp_id != current_user_id:
                password_display = "********"
            else:
                password_display = password

            work_date = doc.get("work_date")
            if isinstance(work_date, datetime.datetime):
                work_date_str = work_date.date().isoformat()
            else:
                work_date_str = self._clean(work_date)

            schedule = doc.get("schedule_days", "")
            status_today = _status_today_from_schedule(schedule)

            self.tree.insert(
                "",
                "end",
                values=(
                    emp_id,
                    name,
                    position,
                    username,
                    password_display,
                    work_date_str,
                    schedule,
                    status_today,
                ),
            )

    # ================= LOAD & TÌM KIẾM =================
    def load_data(self):
        try:
            col = get_collection("employees")
            cursor = col.find({"is_admin": {"$ne": True}}).sort("employee_id", 1)
            self._load_from_cursor(cursor)
        except Exception as e:
            messagebox.showerror("Lỗi CSDL", f"Không thể tải dữ liệu:\n{e}")

    def search(self):
        keyword = self.search_entry.get().strip()
        try:
            col = get_collection("employees")
            cond = {"is_admin": {"$ne": True}}
            if keyword:
                cond["$or"] = [
                    {"name": {"$regex": keyword, "$options": "i"}},
                    {"position": {"$regex": keyword, "$options": "i"}},
                ]
            cursor = col.find(cond).sort("employee_id", 1)
            self._load_from_cursor(cursor)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi khi tìm kiếm:\n{e}")

    # ================= THÊM NHÂN VIÊN =================
    def add_employee(self):
        form = tk.Toplevel(self)
        form.title("Thêm nhân viên")
        form.geometry("450x520")
        form.config(bg="white")
        form.resizable(False, False)
        form.grab_set()

        labels = ["Họ và tên", "Chức vụ", "Tài khoản", "Mật khẩu"]
        entries = []

        for i, label in enumerate(labels):
            tk.Label(form, text=label + ":", bg="white").place(x=30, y=30 + i * 40)
            entry = tk.Entry(form, width=30)
            if label == "Mật khẩu":
                entry.config(show="*")
            entry.place(x=130, y=30 + i * 40)
            entries.append(entry)

        tk.Label(form, text="Lịch làm (Tối đa 2):", bg="white").place(x=30, y=200)
        schedule_frame = tk.Frame(form, bg="white")
        schedule_frame.place(x=130, y=200)

        days = [str(i) for i in range(1, 32)]
        check_vars = {}
        for i, day in enumerate(days):
            var = tk.IntVar()
            cb = tk.Checkbutton(schedule_frame, text=day, variable=var, bg="white", width=2)
            cb.grid(row=i // 7, column=i % 7, sticky="w")
            check_vars[day] = var

        def save_employee():
            name, position, username, password = [e.get().strip() for e in entries]
            if not all([name, position, username, password]):
                return messagebox.showwarning(
                    "Thiếu dữ liệu", "Vui lòng nhập đủ thông tin.", parent=form
                )

            if username.lower() == "admin":
                return messagebox.showwarning(
                    "Không hợp lệ",
                    "Không thể thêm tài khoản admin!",
                    parent=form,
                )

            selected_days = [d for d, v in check_vars.items() if v.get() == 1]
            if len(selected_days) > 2:
                return messagebox.showwarning(
                    "Lỗi Lịch làm",
                    "Chỉ được chọn tối đa 2 ngày làm việc.",
                    parent=form,
                )

            schedule_string = ",".join(selected_days)

            try:
                col = get_collection("employees")
                new_id = _get_next_employee_id(col)

                doc = {
                    "employee_id": new_id,
                    "name": name,
                    "position": position,
                    "username": username,
                    "password": password,
                    "is_admin": False,
                    "work_date": datetime.datetime.now(),
                    "schedule_days": schedule_string,
                }
                col.insert_one(doc)

                messagebox.showinfo("Thành công", "Đã thêm nhân viên mới.", parent=form)
                form.destroy()
                self.load_data()
            except Exception as e:
                # kiểm tra trùng username
                if "E11000" in str(e):
                    messagebox.showwarning(
                        "Lỗi Trùng Lặp",
                        "Tên tài khoản này đã tồn tại.\nVui lòng nhập tài khoản khác.",
                        parent=form,
                    )
                else:
                    messagebox.showerror(
                        "Lỗi",
                        f"Không thể thêm nhân viên:\n{e}",
                        parent=form,
                    )

        tk.Button(
            form,
            text="Lưu",
            bg="#2ecc71",
            fg="white",
            width=10,
            command=save_employee,
        ).place(x=120, y=460)

        tk.Button(
            form,
            text="Hủy",
            bg="#e74c3c",
            fg="white",
            width=10,
            command=form.destroy,
        ).place(x=240, y=460)

    # ================= SỬA NHÂN VIÊN =================
    def edit_employee(self):
        selected = self.tree.selection()
        if not selected:
            return messagebox.showwarning(
                "Chọn dòng", "Vui lòng chọn nhân viên cần sửa."
            )

        emp_id = self.tree.item(selected[0])["values"][0]

        is_admin = bool(getattr(self.controller, "is_admin", False))
        current_user_id = getattr(self.controller, "current_user_id", -1)
        can_edit_password = is_admin or int(emp_id) == int(current_user_id)

        try:
            col = get_collection("employees")
            emp = col.find_one({"employee_id": emp_id})
            if not emp:
                return messagebox.showerror("Lỗi", "Không tìm thấy nhân viên này.")
        except Exception as e:
            return messagebox.showerror("Lỗi", f"Lỗi khi tải dữ liệu:\n{e}")

        form = tk.Toplevel(self)
        form.title("Cập nhật nhân viên")
        form.geometry("450x520")
        form.config(bg="white")
        form.resizable(False, False)
        form.grab_set()

        labels = ["Họ và tên", "Chức vụ", "Tài khoản", "Mật khẩu"]
        entries = []

        for i, label in enumerate(labels):
            tk.Label(form, text=label + ":", bg="white").place(x=30, y=40 + i * 40)
            entry = tk.Entry(form, width=30)
            if label == "Mật khẩu":
                entry.config(show="*")
                if not can_edit_password:
                    entry.config(state="disabled")
            entry.place(x=130, y=40 + i * 40)

            if i == 0:
                entry.insert(0, self._clean(emp.get("name")))
            elif i == 1:
                entry.insert(0, self._clean(emp.get("position")))
            elif i == 2:
                entry.insert(0, self._clean(emp.get("username")))
            else:  # password
                entry.insert(0, self._clean(emp.get("password")))
            entries.append(entry)

        tk.Label(form, text="Lịch làm (Tối đa 2):", bg="white").place(x=30, y=210)
        schedule_frame = tk.Frame(form, bg="white")
        schedule_frame.place(x=130, y=210)

        days = [str(i) for i in range(1, 32)]
        check_vars = {}
        for i, day in enumerate(days):
            var = tk.IntVar()
            cb = tk.Checkbutton(schedule_frame, text=day, variable=var, bg="white", width=2)
            cb.grid(row=i // 7, column=i % 7, sticky="w")
            check_vars[day] = var

        saved_days = str(emp.get("schedule_days", "")).split(",")
        for d in saved_days:
            d = d.strip()
            if d in check_vars:
                check_vars[d].set(1)

        def update():
            name, position, username, password = [e.get().strip() for e in entries]
            if not all([name, position, username, password]):
                return messagebox.showwarning(
                    "Thiếu dữ liệu", "Vui lòng nhập đủ thông tin.", parent=form
                )

            if username.lower() == "admin":
                return messagebox.showwarning(
                    "Không hợp lệ",
                    "Không thể đặt tài khoản admin!",
                    parent=form,
                )

            selected_days = [d for d, v in check_vars.items() if v.get() == 1]
            if len(selected_days) > 2:
                return messagebox.showwarning(
                    "Lỗi Lịch làm",
                    "Chỉ được chọn tối đa 2 ngày làm việc.",
                    parent=form,
                )

            schedule_string = ",".join(selected_days)

            try:
                col = get_collection("employees")
                update_doc = {
                    "name": name,
                    "position": position,
                    "username": username,
                    "schedule_days": schedule_string,
                }
                if can_edit_password:
                    update_doc["password"] = password

                col.update_one({"employee_id": emp_id}, {"$set": update_doc})

                messagebox.showinfo("Thành công", "Cập nhật thành công.", parent=form)
                form.destroy()
                self.load_data()
            except Exception as e:
                if "E11000" in str(e):
                    messagebox.showwarning(
                        "Lỗi Trùng Lặp",
                        "Tên tài khoản này đã tồn tại.\nVui lòng sử dụng tài khoản khác!",
                        parent=form,
                    )
                else:
                    messagebox.showerror("Lỗi", f"Lỗi khi cập nhật:\n{e}", parent=form)

        tk.Button(
            form,
            text="Lưu",
            bg="#2ecc71",
            fg="white",
            width=10,
            command=update,
        ).place(x=120, y=460)

        tk.Button(
            form,
            text="Hủy",
            bg="#e74c3c",
            fg="white",
            width=10,
            command=form.destroy,
        ).place(x=240, y=460)

    # ================= XÓA NHÂN VIÊN =================
    def delete_employee(self):
        selected = self.tree.selection()
        if not selected:
            return messagebox.showwarning(
                "Chọn dòng", "Vui lòng chọn nhân viên cần xóa."
            )

        emp_id = self.tree.item(selected[0])["values"][0]
        if not messagebox.askyesno(
            "Xác nhận", "Bạn có chắc muốn xóa nhân viên này không?"
        ):
            return

        try:
            col = get_collection("employees")
            col.delete_one({"employee_id": emp_id})
            messagebox.showinfo("Thành công", "Đã xóa nhân viên.")
            self.load_data()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi khi xóa:\n{e}")

    # ================= KIỂM TRA LỊCH HÔM NAY =================
    def check_today(self):
        """Xem hôm nay có những ai có lịch làm (dựa trên schedule_days)."""
        try:
            col = get_collection("employees")
            all_emp = list(col.find({"is_admin": {"$ne": True}}))
            today = datetime.datetime.now().day

            names_today = []
            for emp in all_emp:
                schedule = emp.get("schedule_days", "")
                days = {d.strip() for d in str(schedule).split(",") if d.strip().isdigit()}
                if str(today) in days:
                    names_today.append(emp.get("name", ""))

            if not names_today:
                messagebox.showinfo(
                    "Lịch làm hôm nay",
                    f"Hôm nay (Ngày {today}) không có nhân viên nào trong lịch làm.",
                )
            else:
                if len(names_today) == 1:
                    text = f"Hôm nay {names_today[0]} làm việc."
                elif len(names_today) == 2:
                    text = f"Hôm nay {names_today[0]} và {names_today[1]} làm việc."
                else:
                    text = (
                        f"Hôm nay {', '.join(names_today[:-1])} và {names_today[-1]} làm việc."
                    )

                messagebox.showinfo(
                    f"Nhân viên có lịch làm hôm nay (Ngày {today})", text
                )
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi khi kiểm tra lịch:\n{e}")