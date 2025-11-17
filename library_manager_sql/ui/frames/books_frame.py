# ui/frames/books_frame.py
import tkinter as tk
from tkinter import ttk, messagebox

from database.db import get_collection


# ===================== Helpers về ID tăng dần =====================

def _get_next_id(collection_name: str, field: str) -> int:
    col = get_collection(collection_name)
    doc = col.find_one(sort=[(field, -1)])
    return int(doc[field]) + 1 if doc and field in doc else 1


# ===================== QUERY HELPERS (Mongo) =====================

def _list_books(keyword: str | None = None):
    """
    Trả về list tuple cho Treeview:
    (book_id, title, author, year, category, status)
    Chỉ lấy các document có trường book_id (bỏ qua dữ liệu test cũ không chuẩn).
    """
    books = get_collection("books")
    query = {}
    kw = (keyword or "").strip()
    if kw:
        regex = {"$regex": kw, "$options": "i"}
        query = {
            "$or": [
                {"title": regex},
                {"author": regex},
                {"category": regex},
            ]
        }

    docs = list(books.find(query))
    # Chỉ lấy những doc có book_id, sort theo book_id tăng dần
    docs = [d for d in docs if "book_id" in d]
    docs.sort(key=lambda d: int(d.get("book_id", 0)))

    rows = []
    for d in docs:
        rows.append(
            (
                int(d.get("book_id")),
                d.get("title", ""),
                d.get("author", ""),
                d.get("published_year", ""),
                d.get("category", ""),
                d.get("status", "Có sẵn"),
            )
        )
    return rows


def _book_in_open_loan(book_id: int) -> bool:
    """
    Kiểm tra sách có đang được mượn không:
    loans: is_returned != True hoặc return_date == None
    """
    loans = get_collection("loans")
    doc = loans.find_one(
        {
            "book_id": int(book_id),
            "$or": [
                {"return_date": None},
                {"is_returned": {"$ne": True}},
            ],
        }
    )
    return doc is not None


def _add_book(title: str, author: str, year: int | None,
             category: str, status: str = "Có sẵn") -> int:
    books = get_collection("books")
    new_id = _get_next_id("books", "book_id")
    books.insert_one(
        {
            "book_id": new_id,
            "title": title,
            "author": author,
            "published_year": year,
            "category": category,
            "status": status or "Có sẵn",
        }
    )
    return new_id


def _update_book(book_id: int, title: str, author: str,
                 year: int | None, category: str, status: str):
    books = get_collection("books")
    books.update_one(
        {"book_id": int(book_id)},
        {
            "$set": {
                "title": title,
                "author": author,
                "published_year": year,
                "category": category,
                "status": status,
            }
        },
    )


def _delete_book(book_id: int):
    """
    Không cho xóa nếu sách đang được mượn (có loans chưa trả).
    """
    if _book_in_open_loan(book_id):
        raise Exception("Sách này đang được mượn, không thể xóa.")

    books = get_collection("books")
    loans = get_collection("loans")

    # Xóa lịch sử loan liên quan tới sách này (nếu muốn giữ FK mềm)
    loans.delete_many({"book_id": int(book_id)})
    books.delete_one({"book_id": int(book_id)})


# ===================== FORM THÊM / SỬA SÁCH =====================

class BookForm(tk.Toplevel):
    def __init__(self, master, title, init_data=None):
        super().__init__(master)
        self.title(title)
        self.geometry("520x260")
        self.resizable(False, False)
        self.configure(bg="#f8f9fa")
        self.transient(master)

        init_data = init_data or {}
        self.var_title = tk.StringVar(value=init_data.get("title", ""))
        self.var_author = tk.StringVar(value=init_data.get("author", ""))
        self.var_year = tk.StringVar(
            value=str(init_data.get("published_year") or "")
        )
        self.var_category = tk.StringVar(value=init_data.get("category", ""))
        self.var_status = tk.StringVar(value=init_data.get("status", "Có sẵn"))

        self.result = None

        frm = tk.Frame(self, bg="#f8f9fa")
        frm.pack(fill="both", expand=True, padx=16, pady=14)

        row = 0
        tk.Label(frm, text="Tiêu đề:", bg="#f8f9fa").grid(row=row, column=0, sticky="e", padx=6, pady=4)
        tk.Entry(frm, textvariable=self.var_title, width=40).grid(row=row, column=1, sticky="w", padx=6, pady=4)

        row += 1
        tk.Label(frm, text="Tác giả:", bg="#f8f9fa").grid(row=row, column=0, sticky="e", padx=6, pady=4)
        tk.Entry(frm, textvariable=self.var_author, width=40).grid(row=row, column=1, sticky="w", padx=6, pady=4)

        row += 1
        tk.Label(frm, text="Năm:", bg="#f8f9fa").grid(row=row, column=0, sticky="e", padx=6, pady=4)
        tk.Entry(frm, textvariable=self.var_year, width=10).grid(row=row, column=1, sticky="w", padx=6, pady=4)

        row += 1
        tk.Label(frm, text="Thể loại:", bg="#f8f9fa").grid(row=row, column=0, sticky="e", padx=6, pady=4)
        tk.Entry(frm, textvariable=self.var_category, width=40).grid(row=row, column=1, sticky="w", padx=6, pady=4)

        row += 1
        tk.Label(frm, text="Tình trạng:", bg="#f8f9fa").grid(row=row, column=0, sticky="e", padx=6, pady=4)
        cb_status = ttk.Combobox(
            frm,
            textvariable=self.var_status,
            values=["Có sẵn", "Đã mượn", "Hỏng", "Mất"],
            state="readonly",
            width=15,
        )
        cb_status.grid(row=row, column=1, sticky="w", padx=6, pady=4)
        if not self.var_status.get():
            self.var_status.set("Có sẵn")

        row += 1
        btns = tk.Frame(frm, bg="#f8f9fa")
        btns.grid(row=row, column=1, sticky="w", padx=6, pady=(10, 0))
        tk.Button(btns, text="OK", width=10, bg="#2ecc71", fg="white",
                  command=self.on_ok).pack(side="left", padx=(0, 8))
        tk.Button(btns, text="Huỷ", width=10, command=self.on_cancel).pack(side="left")

        self.grab_set()
        self.focus_force()
        self.bind("<Return>", lambda _e: self.on_ok())
        self.bind("<Escape>", lambda _e: self.on_cancel())
        self.wait_window(self)

    def on_ok(self):
        title = (self.var_title.get() or "").strip()
        author = (self.var_author.get() or "").strip()
        year_s = (self.var_year.get() or "").strip()
        category = (self.var_category.get() or "").strip()
        status = (self.var_status.get() or "").strip() or "Có sẵn"

        if not title:
            messagebox.showwarning("Thiếu dữ liệu", "Tiêu đề không được rỗng.", parent=self)
            return

        year = None
        if year_s:
            if not year_s.isdigit():
                messagebox.showwarning("Sai định dạng", "Năm phải là số.", parent=self)
                return
            year = int(year_s)

        self.result = {
            "title": title,
            "author": author,
            "year": year,
            "category": category,
            "status": status,
        }
        self.destroy()

    def on_cancel(self):
        self.result = None
        self.destroy()


# ===================== MAIN UI =====================

class BooksFrame(tk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent, bg="white")
        self.controller = controller
        self._selected_id = None

        # Top search
        top = tk.Frame(self, bg="white")
        top.pack(fill="x", padx=16, pady=(10, 6))

        tk.Label(top, text="Tìm kiếm:", bg="white").pack(side="left")
        self.var_kw = tk.StringVar()
        ent = tk.Entry(top, textvariable=self.var_kw, width=30)
        ent.pack(side="left", padx=(6, 6))
        ent.bind("<Return>", lambda _e: self.on_search())

        tk.Button(top, text="Tìm", bg="#3498db", fg="white",
                  command=self.on_search).pack(side="left", padx=(0, 4))
        tk.Button(top, text="Làm mới", bg="#7f8c8d", fg="white",
                  command=self.reload).pack(side="left")

        # Table
        self.tree = ttk.Treeview(
            self,
            columns=("id", "title", "author", "year", "category", "status"),
            show="headings",
            height=18,
        )
        for key, text, width, anchor in [
            ("id", "ID", 80, "center"),
            ("title", "Tiêu đề", 260, "w"),
            ("author", "Tác giả", 160, "w"),
            ("year", "Năm", 80, "center"),
            ("category", "Thể loại", 140, "center"),
            ("status", "Tình trạng", 120, "center"),
        ]:
            self.tree.heading(key, text=text)
            self.tree.column(key, width=width, anchor=anchor)

        self.tree.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # Buttons
        btns = tk.Frame(self, bg="white")
        btns.pack(pady=(0, 10))

        tk.Button(btns, text="Thêm", bg="#2ecc71", fg="white",
                  width=12, command=self.on_add).pack(side="left", padx=5)
        tk.Button(btns, text="Sửa", bg="#f1c40f",
                  width=12, command=self.on_edit).pack(side="left", padx=5)
        tk.Button(btns, text="Xóa", bg="#e74c3c", fg="white",
                  width=12, command=self.on_delete).pack(side="left", padx=5)

        self.reload()

    # ------ helpers ------
    def _fill_table(self, rows):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for row in rows:
            self.tree.insert("", "end", values=row)
        self._selected_id = None

    def reload(self):
        self._fill_table(_list_books())
        self.var_kw.set("")

    def on_search(self):
        self._fill_table(_list_books(self.var_kw.get()))

    def _on_select(self, _e=None):
        sel = self.tree.selection()
        if sel:
            vals = self.tree.item(sel[0])["values"]
            # cột 0 là book_id (int)
            self._selected_id = int(vals[0])
        else:
            self._selected_id = None

    def _need_sel(self) -> bool:
        if self._selected_id is None:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn sách.", parent=self)
            return False
        return True

    # ------ CRUD ------
    def on_add(self):
        dlg = BookForm(self, "Thêm sách")
        if not dlg.result:
            return
        d = dlg.result
        try:
            new_id = _add_book(
                d["title"], d["author"], d["year"], d["category"], d["status"]
            )
            messagebox.showinfo("Thành công", f"Đã thêm sách #{new_id}.", parent=self)
            self.reload()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e), parent=self)

    def on_edit(self):
        if not self._need_sel():
            return

        # Lấy dữ liệu hiện tại trên dòng
        sel = self.tree.selection()[0]
        vals = self.tree.item(sel)["values"]
        current = {
            "title": vals[1],
            "author": vals[2],
            "published_year": vals[3],
            "category": vals[4],
            "status": vals[5],
        }

        dlg = BookForm(self, f"Sửa sách #{self._selected_id}", init_data=current)
        if not dlg.result:
            return

        d = dlg.result
        try:
            _update_book(
                self._selected_id,
                d["title"],
                d["author"],
                d["year"],
                d["category"],
                d["status"],
            )
            messagebox.showinfo("Thành công", "Đã cập nhật sách.", parent=self)
            self.reload()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e), parent=self)

    def on_delete(self):
        if not self._need_sel():
            return
        if not messagebox.askyesno(
            "Xác nhận",
            "Bạn có chắc muốn xóa sách này?\nNếu sách đang được mượn sẽ không xóa được.",
            parent=self,
        ):
            return
        try:
            _delete_book(self._selected_id)
            messagebox.showinfo("Thành công", "Đã xóa sách.", parent=self)
            self.reload()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e), parent=self)