# ui/frames/borrowers_frame.py
import os
import sys
import datetime
import tkinter as tk
from tkinter import ttk, messagebox

# Cho phép chạy trực tiếp trong VS Code
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from database.db import get_collection

# ============================= DB HELPERS (MONGO) =============================

def _stats_by_borrower() -> dict:
    """
    Trả về map:
        { borrower_id: {"total_receipts": x, "open_receipts": y} }

    Đếm theo collection loan_receipts (mỗi phiếu = 1 lượt).
    """
    receipts = get_collection("loan_receipts")
    pipeline = [
        {
            "$group": {
                "_id": "$borrower_id",
                "total_receipts": {"$sum": 1},
                "open_receipts": {
                    "$sum": {
                        "$cond": [{"$eq": ["$return_date", None]}, 1, 0]
                    }
                },
            }
        }
    ]
    stats = {}
    for doc in receipts.aggregate(pipeline):
        stats[int(doc["_id"])] = {
            "total_receipts": int(doc.get("total_receipts", 0) or 0),
            "open_receipts": int(doc.get("open_receipts", 0) or 0),
        }
    return stats


def _build_rows(
    keyword: str | None = None,
    only_returned: bool = False,
    only_borrowing: bool = False,
):
    """
    Tạo list row cho Treeview:
    (borrower_id, name, phone, email, open_receipts, total_receipts, status_text)
    """
    borrowers_col = get_collection("borrowers")
    stats_map = _stats_by_borrower()

    base_filter: dict = {}

    if keyword:
        kw = keyword.strip()
        if kw:
            base_filter = {
                "$or": [
                    {"phone": {"$regex": kw, "$options": "i"}},
                    {"name": {"$regex": kw, "$options": "i"}},
                ]
            }

    borrowers = list(
        borrowers_col.find(base_filter).sort("borrower_id", 1)
    )

    rows = []
    for b in borrowers:
        bid = int(b.get("borrower_id"))
        st = stats_map.get(bid, {"total_receipts": 0, "open_receipts": 0})
        total = st["total_receipts"]
        open_cnt = st["open_receipts"]

        # Lọc theo trạng thái đã trả hết / đang mượn
        if only_returned:
            if not (total > 0 and open_cnt == 0):
                continue
        if only_borrowing:
            if open_cnt == 0:
                continue

        if total == 0:
            status_text = "Vừa thêm"
        elif open_cnt > 0:
            status_text = "Đang mượn"
        else:
            status_text = "Đã trả hết"

        rows.append(
            (
                bid,
                b.get("name", ""),
                b.get("phone", ""),
                b.get("email", ""),
                open_cnt,   # số phiếu đang mượn
                total,      # tổng số phiếu (đã + đang)
                status_text,
            )
        )
    return rows


def _has_open_loans(borrower_id: int) -> bool:
    """Kiểm tra người mượn còn phiếu chưa trả không (đếm theo loan_receipts)."""
    receipts = get_collection("loan_receipts")
    count = receipts.count_documents(
        {"borrower_id": borrower_id, "return_date": None}
    )
    return count > 0


def _book_exists(book_id: int) -> bool:
    books = get_collection("books")
    return books.count_documents({"book_id": book_id}) > 0


def _add_borrower(name: str, phone: str | None, email: str | None) -> int:
    borrowers = get_collection("borrowers")
    # tự tăng borrower_id = max hiện tại + 1
    last = borrowers.find_one(sort=[("borrower_id", -1)])
    new_id = int(last["borrower_id"]) + 1 if last else 1
    doc = {
        "borrower_id": new_id,
        "name": name,
        "phone": phone,
        "email": email,
    }
    borrowers.insert_one(doc)
    return new_id


def _update_borrower(bid: int, name: str, phone: str | None, email: str | None):
    borrowers = get_collection("borrowers")
    borrowers.update_one(
        {"borrower_id": bid},
        {"$set": {"name": name, "phone": phone, "email": email}},
    )


def _delete_borrower(bid: int):
    """
    XÓA CỨNG: chỉ cho xoá nếu không còn phiếu đang mượn
    (phiếu = loan_receipts; sách trong phiếu = loans).
    """
    if _has_open_loans(bid):
        raise Exception("Người mượn còn phiếu chưa trả — không thể xoá.")

    borrowers = get_collection("borrowers")
    loans = get_collection("loans")
    receipts = get_collection("loan_receipts")

    loans.delete_many({"borrower_id": bid})
    receipts.delete_many({"borrower_id": bid})
    borrowers.delete_one({"borrower_id": bid})


def _create_receipt(
    borrower_id: int,
    due_date: datetime.date | None,
    book_ids: list[int],
    employee_id: int | None = None,
) -> int:
    """
    Tạo 1 phiếu (loan_receipts + loans) cho tối đa 5 sách.
    Chỉ cho phép nếu KHÔNG còn phiếu mở.
    """
    if not (1 <= len(book_ids) <= 5):
        raise Exception("Một phiếu phải có từ 1 đến 5 sách.")

    if _has_open_loans(borrower_id):
        raise Exception("Độc giả đang có phiếu mượn chưa trả, không thể lập phiếu mới.")

    books = get_collection("books")
    loans = get_collection("loans")
    receipts = get_collection("loan_receipts")

    # Kiểm tra sách tồn tại & đang 'Có sẵn'
    for b_id in book_ids:
        bk = books.find_one({"book_id": b_id})
        if not bk:
            raise Exception(f"Sách ID {b_id} không tồn tại.")
        status = str(bk.get("status", "")).strip().lower()
        if status not in ["có sẵn", "co san", "available", "", "0"]:
            raise Exception(f"Sách ID {b_id} hiện không có sẵn (status={bk.get('status')}).")

    # receipt_id auto tăng = max + 1
    last_receipt = receipts.find_one(sort=[("receipt_id", -1)])
    receipt_id = int(last_receipt["receipt_id"]) + 1 if last_receipt else 1

    borrow_dt = datetime.datetime.now()
    if due_date:
        due_dt = datetime.datetime.combine(due_date, datetime.time())
    else:
        due_dt = None

    receipt_doc = {
        "receipt_id": receipt_id,
        "borrower_id": borrower_id,
        "borrow_date": borrow_dt,
        "due_date": due_dt,
        "return_date": None,
        "employee_id": employee_id,
        "note": None,
    }
    receipts.insert_one(receipt_doc)

    # loan_id auto tăng
    last_loan = loans.find_one(sort=[("loan_id", -1)])
    next_loan_id = int(last_loan["loan_id"]) + 1 if last_loan else 1

    for b_id in book_ids:
        loan_doc = {
            "loan_id": next_loan_id,
            "receipt_id": receipt_id,
            "borrower_id": borrower_id,
            "book_id": b_id,
            "employee_id": employee_id,
            "borrow_date": borrow_dt,
            "return_date": None,
            "is_returned": False,
        }
        loans.insert_one(loan_doc)
        next_loan_id += 1

        books.update_one(
            {"book_id": b_id},
            {"$set": {"status": "Đang mượn"}},
        )

    return receipt_id


def _list_receipts(borrower_id: int):
    """
    Danh sách phiếu: (receipt_id, borrow_date, due_date, return_date, book_count, status)
    """
    receipts = get_collection("loan_receipts")
    loans = get_collection("loans")

    all_receipts = list(
        receipts.find({"borrower_id": borrower_id}).sort(
            [("borrow_date", -1), ("receipt_id", -1)]
        )
    )

    result = []
    for r in all_receipts:
        rid = int(r["receipt_id"])
        borrow_date = r.get("borrow_date")
        due_date = r.get("due_date")
        return_date = r.get("return_date")
        book_count = loans.count_documents({"receipt_id": rid})
        status = "Đang mượn" if return_date is None else "Đã trả"
        result.append((rid, borrow_date, due_date, return_date, book_count, status))
    return result


def _receipt_lines(receipt_id: int):
    """
    Chi tiết sách trong phiếu:
        (book_id, title, borrow_date, return_date)
    """
    loans = get_collection("loans")
    books = get_collection("books")

    lines = []
    for l in loans.find({"receipt_id": receipt_id}).sort("loan_id", 1):
        book_id = int(l["book_id"])
        bk = books.find_one({"book_id": book_id}) or {}
        lines.append(
            (
                book_id,
                bk.get("title", ""),
                l.get("borrow_date"),
                l.get("return_date"),
            )
        )
    return lines


def _close_receipt(receipt_id: int):
    """Trả toàn bộ sách trong một phiếu."""
    loans = get_collection("loans")
    receipts = get_collection("loan_receipts")
    books = get_collection("books")

    now = datetime.datetime.now()

    # cập nhật loans
    loans.update_many(
        {"receipt_id": receipt_id, "return_date": None},
        {"$set": {"return_date": now, "is_returned": True}},
    )

    # cập nhật loan_receipts
    receipts.update_one(
        {"receipt_id": receipt_id, "return_date": None},
        {"$set": {"return_date": now}},
    )

    # đưa sách về 'Có sẵn'
    book_ids = {
        int(l["book_id"])
        for l in loans.find({"receipt_id": receipt_id})
    }
    if book_ids:
        books.update_many(
            {"book_id": {"$in": list(book_ids)}},
            {"$set": {"status": "Có sẵn"}},
        )

# ============================= MODAL FORM =============================

class MemberForm(tk.Toplevel):
    def __init__(self, master, title, name="", phone="", email=""):
        super().__init__(master)
        self.title(title)
        self.geometry("520x220")
        self.resizable(False, False)
        self.transient(master)
        self.configure(bg="#f8f9fa")

        self.var_name = tk.StringVar(value=name)
        self.var_phone = tk.StringVar(value=phone)
        self.var_email = tk.StringVar(value=email)
        self.result = None

        frm = tk.Frame(self, bg="#f8f9fa")
        frm.pack(fill="both", expand=True, padx=16, pady=14)

        tk.Label(frm, text="Họ tên:", bg="#f8f9fa").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        tk.Entry(frm, textvariable=self.var_name, width=40).grid(row=0, column=1, sticky="w", padx=6, pady=6)

        tk.Label(frm, text="SĐT:", bg="#f8f9fa").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        tk.Entry(frm, textvariable=self.var_phone, width=22).grid(row=1, column=1, sticky="w", padx=6, pady=6)

        tk.Label(frm, text="Email:", bg="#f8f9fa").grid(row=2, column=0, sticky="e", padx=6, pady=6)
        tk.Entry(frm, textvariable=self.var_email, width=40).grid(row=2, column=1, sticky="w", padx=6, pady=6)

        btns = tk.Frame(frm, bg="#f8f9fa")
        btns.grid(row=3, column=1, sticky="w", padx=6, pady=(10, 0))
        tk.Button(btns, text="OK", width=10, bg="#2ecc71", fg="white", command=self.on_ok).pack(
            side="left", padx=(0, 8)
        )
        tk.Button(btns, text="Huỷ", width=10, command=self.on_cancel).pack(side="left")

        self.grab_set()
        self.focus_force()
        self.bind("<Return>", lambda _e: self.on_ok())
        self.bind("<Escape>", lambda _e: self.on_cancel())
        self.wait_window(self)

    def on_ok(self):
        name = (self.var_name.get() or "").strip()
        phone = (self.var_phone.get() or "").strip() or None
        email = (self.var_email.get() or "").strip() or None

        if not name:
            messagebox.showwarning("Thiếu dữ liệu", "Họ tên không được rỗng.", parent=self)
            return

        if phone and not phone.replace(" ", "").isdigit():
            messagebox.showwarning("Sai định dạng", "SĐT chỉ chứa số và khoảng trắng.", parent=self)
            return

        self.result = (name, phone, email)
        self.destroy()

    def on_cancel(self):
        self.result = None
        self.destroy()

# ============================= MAIN UI =============================

class BorrowersFrame(tk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent, bg="white")
        self.controller = controller
        self._selected_id: int | None = None
        self._selected_receipt_id: int | None = None

        # Top: search & filter
        top = tk.Frame(self, bg="white")
        top.pack(fill="x", padx=16, pady=(10, 6))

        tk.Label(top, text="Tìm theo SĐT / tên:", bg="white").pack(side="left")
        self.var_kw = tk.StringVar()
        e = tk.Entry(top, textvariable=self.var_kw, width=28)
        e.pack(side="left", padx=(6, 8))
        e.bind("<Return>", lambda _: self.on_search())

        tk.Button(top, text="Tìm", command=self.on_search, bg="#1f6feb", fg="white").pack(side="left")
        tk.Button(top, text="Tải lại", command=self.reload, bg="#7f8c8d", fg="white").pack(
            side="left", padx=(8, 0)
        )
        tk.Button(top, text="Người đã trả sách", command=self.filter_returned, bg="#27ae60", fg="white").pack(
            side="left", padx=(16, 6)
        )
        tk.Button(top, text="Người đang mượn", command=self.filter_borrowing, bg="#e67e22", fg="white").pack(
            side="left"
        )

        # Bảng borrowers
        self.tree = ttk.Treeview(
            self,
            columns=("id", "name", "phone", "email", "status", "out", "total"),
            show="headings",
            height=12,
        )
        for k, t, w, a in [
            ("id", "ID", 60, "center"),
            ("name", "Họ tên", 230, "w"),
            ("phone", "SĐT", 130, "center"),
            ("email", "Email", 240, "w"),
            ("status", "Trạng thái", 110, "center"),
            ("out", "Đang mượn", 90, "center"),   # số phiếu đang mượn
            ("total", "Tổng lượt", 90, "center"),  # tổng số phiếu
        ]:
            self.tree.heading(k, text=t)
            self.tree.column(k, width=w, anchor=a)

        self.tree.pack(fill="both", expand=False, padx=16, pady=(0, 6))
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<<TreeviewSelect>>", self._auto_show_details, add="+")

        # Action buttons
        act = tk.Frame(self, bg="white")
        act.pack(fill="x", padx=16, pady=(0, 8))
        tk.Button(act, text="Thêm", command=self.on_add, bg="#2ecc71", fg="white", width=10).pack(
            side="left", padx=5
        )
        tk.Button(act, text="Sửa", command=self.on_edit, bg="#f1c40f", width=10).pack(
            side="left", padx=5
        )
        tk.Button(act, text="Xoá", command=self.on_delete, bg="#e74c3c", fg="white", width=10).pack(
            side="left", padx=5
        )
        tk.Button(
            act,
            text="Lập phiếu mượn",
            command=self.show_create_receipt_panel,
            bg="#3498db",
            fg="white",
            width=16,
        ).pack(side="left", padx=5)
        tk.Button(
            act,
            text="Chi tiết mượn–trả",
            command=self.show_receipt_detail_panel,
            bg="#34495e",
            fg="white",
            width=16,
        ).pack(side="left", padx=5)

        # Inline detail panel
        self.detail_panel = tk.Frame(self, bg="#f7f9fc", height=260)
        self.detail_panel.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        self.detail_panel.grid_propagate(False)

        self.reload()

    # -------- load/filter ----------
    def _fill_table(self, rows):
        for i in self.tree.get_children():
            self.tree.delete(i)

        for bid, name, phone, email, open_cnt, total, status in rows:
            phone_str = str(phone) if phone is not None else ""
            self.tree.insert(
                "",
                "end",
                values=(
                    bid,
                    str(name),
                    phone_str,
                    str(email) if email else "",
                    status,
                    open_cnt,
                    total,
                ),
            )
        self._selected_id = None

    def reload(self):
        self.clear_panel()
        self._fill_table(_build_rows())
        self.var_kw.set("")

    def on_search(self):
        self.clear_panel()
        kw = (self.var_kw.get() or "").strip()
        self._fill_table(_build_rows(keyword=kw))

    def filter_returned(self):
        self.clear_panel()
        self._fill_table(_build_rows(only_returned=True))

    def filter_borrowing(self):
        self.clear_panel()
        self._fill_table(_build_rows(only_borrowing=True))

    # -------- selection ----------
    def _on_select(self, _e=None):
        sel = self.tree.selection()
        self._selected_id = int(self.tree.item(sel[0])["values"][0]) if sel else None

    def _auto_show_details(self, _e=None):
        if self._selected_id:
            try:
                self.show_receipt_detail_panel()
            except Exception as ex:
                print("auto show details error:", ex)

    def _need_sel(self) -> bool:
        if self._selected_id is None:
            messagebox.showwarning("Chưa chọn", "Hãy chọn một độc giả.", parent=self)
            return False
        return True

    # -------- CRUD ----------
    def on_add(self):
        dlg = MemberForm(self, "Thêm độc giả")
        if not dlg.result:
            return
        name, phone, email = dlg.result
        try:
            bid = _add_borrower(name, phone, email)
            messagebox.showinfo("Thành công", f"Đã thêm độc giả #{bid}.", parent=self)
            self.reload()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e), parent=self)

    def on_edit(self):
        if not self._need_sel():
            return
        vals = self.tree.item(self.tree.selection()[0])["values"]
        cur_name = str(vals[1]) if len(vals) > 1 else ""
        cur_phone = (str(vals[2]).strip() if len(vals) > 2 and vals[2] is not None else "")
        cur_email = (str(vals[3]).strip() if len(vals) > 3 and vals[3] is not None else "")

        dlg = MemberForm(self, f"Sửa độc giả #{self._selected_id}", cur_name, cur_phone, cur_email)
        if not dlg.result:
            return

        try:
            name, phone, email = dlg.result
            _update_borrower(self._selected_id, name, phone, email)
            messagebox.showinfo("Thành công", "Đã cập nhật.", parent=self)
            self.reload()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e), parent=self)

    def on_delete(self):
        if not self._need_sel():
            return
        if not messagebox.askyesno(
            "Xác nhận",
            "Xoá độc giả này? Tất cả phiếu và lịch sử mượn–trả liên quan sẽ bị xoá vĩnh viễn.",
            parent=self,
        ):
            return
        try:
            _delete_borrower(self._selected_id)
            messagebox.showinfo("Thành công", "Đã xoá độc giả.", parent=self)
            self.reload()
            self.clear_panel()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e), parent=self)

    # -------- Panel helpers ----------
    def clear_panel(self):
        for w in self.detail_panel.winfo_children():
            w.destroy()
        self._selected_receipt_id = None

    # -------- Lập phiếu ----------
    def show_create_receipt_panel(self):
        if not self._need_sel():
            return
        if _has_open_loans(self._selected_id):
            messagebox.showwarning(
                "Không thể lập phiếu",
                "Độc giả còn phiếu đang mượn, hãy trả trước.",
                parent=self,
            )
            return

        self.clear_panel()
        wrapper = tk.Frame(self.detail_panel, bg="#f7f9fc")
        wrapper.pack(fill="x", padx=8, pady=8)

        tk.Label(
            wrapper,
            text=f"Lập phiếu mượn cho độc giả #{self._selected_id}",
            bg="#f7f9fc",
            font=("Segoe UI", 10, "bold"),
        ).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 6))

        tk.Label(wrapper, text="Số lượng sách muốn mượn:", bg="#f7f9fc").grid(
            row=1, column=0, sticky="e", padx=6, pady=4
        )
        self.var_num_books = tk.IntVar(value=1)
        spin = ttk.Spinbox(
            wrapper,
            from_=1,
            to=5,
            width=5,
            textvariable=self.var_num_books,
            command=self._render_book_inputs,
        )
        spin.grid(row=1, column=1, sticky="w", padx=6, pady=4)

        self.book_entry_frame = tk.Frame(wrapper, bg="#f7f9fc")
        self.book_entry_frame.grid(row=2, column=0, columnspan=4, sticky="w", padx=6, pady=(6, 4))

        tk.Label(wrapper, text="Hẹn trả (YYYY-MM-DD):", bg="#f7f9fc").grid(
            row=3, column=0, sticky="e", padx=6, pady=(8, 4)
        )
        self._due_var = tk.StringVar(
            value=(datetime.date.today() + datetime.timedelta(days=7)).isoformat()
        )
        tk.Entry(wrapper, textvariable=self._due_var, width=16).grid(
            row=3, column=1, sticky="w", padx=6, pady=(8, 4)
        )

        btns = tk.Frame(wrapper, bg="#f7f9fc")
        btns.grid(row=4, column=1, sticky="w", padx=6, pady=(10, 0))
        tk.Button(
            btns,
            text="Tạo phiếu",
            bg="#3498db",
            fg="white",
            width=12,
            command=self._on_create_receipt_submit,
        ).pack(side="left", padx=(0, 8))
        tk.Button(btns, text="Ẩn", width=10, command=self.clear_panel).pack(side="left")

        self._render_book_inputs()

    def _render_book_inputs(self):
        for w in self.book_entry_frame.winfo_children():
            w.destroy()
        n = self.var_num_books.get()
        self._book_vars = [tk.StringVar() for _ in range(n)]
        for i, var in enumerate(self._book_vars, start=1):
            tk.Label(self.book_entry_frame, text=f"Mã sách {i}:", bg="#f7f9fc").grid(
                row=i - 1, column=0, sticky="e", padx=6, pady=4
            )
            tk.Entry(self.book_entry_frame, textvariable=var, width=16).grid(
                row=i - 1, column=1, sticky="w", padx=6, pady=4
            )

    def _on_create_receipt_submit(self):
        ids: list[int] = []
        for v in self._book_vars:
            s = (v.get() or "").strip()
            if s == "":
                continue
            if not s.isdigit() or int(s) <= 0:
                messagebox.showwarning(
                    "Mã sách không hợp lệ",
                    "Mỗi mã sách phải là số nguyên dương.",
                    parent=self,
                )
                return
            ids.append(int(s))

        if not (1 <= len(ids) <= 5):
            messagebox.showwarning(
                "Thiếu dữ liệu",
                "Hãy nhập từ 1 đến 5 mã sách.",
                parent=self,
            )
            return

        ds = (self._due_var.get() or "").strip()
        try:
            due = datetime.date.fromisoformat(ds) if ds else None
        except ValueError:
            messagebox.showwarning(
                "Ngày không hợp lệ",
                "Hãy nhập ngày theo dạng YYYY-MM-DD.",
                parent=self,
            )
            return

        try:
            current_bid = self._selected_id
            rid = _create_receipt(current_bid, due, ids)
            messagebox.showinfo("Thành công", f"Đã lập phiếu #{rid}.", parent=self)
            self.reload()
            if current_bid is not None:
                self._select_row_by_id(current_bid)
                self.show_receipt_detail_panel()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e), parent=self)

    def _select_row_by_id(self, bid: int):
        for iid in self.tree.get_children():
            vals = self.tree.item(iid)["values"]
            if vals and int(vals[0]) == int(bid):
                self.tree.selection_set(iid)
                self.tree.focus(iid)
                self.tree.see(iid)
                self._selected_id = int(bid)
                break

    # -------- Chi tiết mượn–trả ----------
    def show_receipt_detail_panel(self):
        if not self._need_sel():
            return
        self.clear_panel()

        header = tk.Frame(self.detail_panel, bg="#f7f9fc")
        header.pack(fill="x", padx=8, pady=(8, 4))
        tk.Label(
            header,
            text=f"Chi tiết mượn–trả của độc giả #{self._selected_id}",
            bg="#f7f9fc",
            font=("Segoe UI", 10, "bold"),
        ).pack(side="left")

        body = tk.Frame(self.detail_panel, bg="#f7f9fc")
        body.pack(fill="both", expand=True, padx=8, pady=6)

        tk.Label(body, text="Danh sách phiếu:", bg="#f7f9fc").pack(anchor="w")
        self.tv_r = ttk.Treeview(
            body,
            columns=("rid", "borrow", "due", "returned", "count", "status"),
            show="headings",
            height=5,
        )
        for k, t, w, a in [
            ("rid", "Mã phiếu", 80, "center"),
            ("borrow", "Ngày mượn", 140, "center"),
            ("due", "Hẹn trả", 110, "center"),
            ("returned", "Ngày trả", 140, "center"),
            ("count", "Số sách", 80, "center"),
            ("status", "Trạng thái", 110, "center"),
        ]:
            self.tv_r.heading(k, text=t)
            self.tv_r.column(k, width=w, anchor=a)
        self.tv_r.pack(fill="x", pady=(2, 8))
        self.tv_r.bind("<<TreeviewSelect>>", self._on_select_receipt_inline)

        tk.Label(body, text="Sách trong phiếu:", bg="#f7f9fc").pack(anchor="w")
        self.tv_l = ttk.Treeview(
            body,
            columns=("book", "title", "borrow", "return"),
            show="headings",
            height=6,
        )
        for k, t, w, a in [
            ("book", "Mã sách", 90, "center"),
            ("title", "Tên sách", 380, "w"),
            ("borrow", "Ngày mượn", 140, "center"),
            ("return", "Ngày trả", 140, "center"),
        ]:
            self.tv_l.heading(k, text=t)
            self.tv_l.column(k, width=w, anchor=a)
        self.tv_l.pack(fill="both", expand=True)

        actions = tk.Frame(self.detail_panel, bg="#f7f9fc")
        actions.pack(fill="x", padx=8, pady=(4, 8))
        tk.Button(
            actions,
            text="Trả phiếu",
            bg="#9b59b6",
            fg="white",
            width=12,
            command=self._on_close_receipt_inline,
        ).pack(side="left")
        tk.Button(actions, text="Ẩn panel", width=10, command=self.clear_panel).pack(side="right")

        self._reload_receipts_inline()

    def _reload_receipts_inline(self):
        for i in getattr(self, "tv_r", []).get_children():
            self.tv_r.delete(i)
        for rid, borrow, due, returned, cnt, status in _list_receipts(self._selected_id):
            self.tv_r.insert(
                "",
                "end",
                values=(rid, borrow, due or "", returned or "", cnt, status),
            )
        for i in getattr(self, "tv_l", []).get_children():
            self.tv_l.delete(i)

    def _on_select_receipt_inline(self, _e=None):
        sel = self.tv_r.selection()
        for i in self.tv_l.get_children():
            self.tv_l.delete(i)
        if not sel:
            return
        rid = int(self.tv_r.item(sel[0])["values"][0])
        self._selected_receipt_id = rid
        for b, t, bd, rd in _receipt_lines(rid):
            self.tv_l.insert("", "end", values=(b, t or "", bd, rd or ""))

    def _on_close_receipt_inline(self):
        if self._selected_receipt_id is None:
            return
        rid = self._selected_receipt_id
        if not messagebox.askyesno(
            "Xác nhận",
            f"Trả toàn bộ sách trong phiếu #{rid}?",
            parent=self,
        ):
            return
        try:
            _close_receipt(rid)
            messagebox.showinfo("Thành công", "Đã trả phiếu.", parent=self)
            self._reload_receipts_inline()
            self.reload()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e), parent=self)