# ui/frames/statistics_frame.py
import tkinter as tk
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

# Lấy hàm thống kê từ MongoDB (đã viết trong database/db.py)
from database.db import get_top_category, get_top_borrower


class StatisticsFrame(tk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent, bg="white")
        self.controller = controller

        tk.Label(
            self,
            text="📊 Thống kê mượn sách",
            font=("Segoe UI", 14, "bold"),
            bg="white",
        ).pack(pady=12)

        # Nút chuyển chế độ xem
        btn_frame = tk.Frame(self, bg="white")
        btn_frame.pack(pady=5)
        tk.Button(
            btn_frame,
            text="Xem Biểu đồ",
            command=self.show_chart,
            bg="#3498db",
            fg="white",
        ).pack(side="left", padx=8)
        tk.Button(
            btn_frame,
            text="Xem Bảng",
            command=self.show_table,
            bg="#2ecc71",
            fg="white",
        ).pack(side="left", padx=8)

        # Frame chứa biểu đồ
        self.chart_frame = tk.Frame(self, bg="white")
        self.chart_frame.pack(fill="both", expand=True)

        # Frame chứa bảng
        self.table_frame = tk.Frame(self, bg="white")

        # --- Bảng Thể loại ---
        tk.Label(
            self.table_frame,
            text="Thể loại được mượn nhiều nhất",
            font=("Segoe UI", 12, "bold"),
            bg="white",
        ).pack(pady=(5, 5))

        self.tree_category = ttk.Treeview(
            self.table_frame,
            columns=("stt", "category", "count"),
            show="headings",
            height=10,
        )
        self.tree_category.heading("stt", text="STT")
        self.tree_category.heading("category", text="Thể loại")
        self.tree_category.heading("count", text="Số lượt mượn")
        self.tree_category.column("stt", width=50, anchor="center")
        self.tree_category.column("category", width=250, anchor="center")
        self.tree_category.column("count", width=120, anchor="center")
        self.tree_category.pack(fill="x", padx=12, pady=(0, 12))

        # --- Bảng Khách hàng ---
        tk.Label(
            self.table_frame,
            text="Khách hàng mượn nhiều nhất",
            font=("Segoe UI", 12, "bold"),
            bg="white",
        ).pack(pady=(5, 5))

        self.tree_borrower = ttk.Treeview(
            self.table_frame,
            columns=("stt", "borrower", "count"),
            show="headings",
            height=15,
        )
        self.tree_borrower.heading("stt", text="STT")
        self.tree_borrower.heading("borrower", text="Khách hàng")
        self.tree_borrower.heading("count", text="Số lượt mượn")
        self.tree_borrower.column("stt", width=50, anchor="center")
        self.tree_borrower.column("borrower", width=250, anchor="center")
        self.tree_borrower.column("count", width=120, anchor="center")
        self.tree_borrower.pack(fill="x", padx=12, pady=(0, 12))

        # Mặc định mở biểu đồ
        self.show_chart()

    # ==================== CHUYỂN CHẾ ĐỘ XEM ====================
    def show_chart(self):
        self.table_frame.pack_forget()
        self.chart_frame.pack(fill="both", expand=True)
        self.hien_thi_bieu_do()

    def show_table(self):
        self.chart_frame.pack_forget()
        self.table_frame.pack(fill="both", expand=True)
        self.hien_thi_bang()

    # ==================== HIỂN THỊ BIỂU ĐỒ ====================
    def hien_thi_bieu_do(self):
        # Xóa biểu đồ cũ
        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        try:
            cat = get_top_category()  # [(category, so_luot), ...]
        except Exception as e:
            print("Error get_top_category:", e)
            cat = []

        if not cat:
            tk.Label(
                self.chart_frame,
                text="Không có dữ liệu để hiển thị",
                bg="white",
            ).pack(pady=30)
            return

        labels = [row[0] for row in cat]
        sizes = [row[1] for row in cat]

        fig, ax = plt.subplots(figsize=(5, 5))
        ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
        ax.set_title("Tỉ lệ mượn theo thể loại", fontsize=12)

        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(expand=True)
        plt.close(fig)

    # ==================== HIỂN THỊ BẢNG ====================
    def hien_thi_bang(self):
        try:
            cat = get_top_category()
            borrower = get_top_borrower()
        except Exception as e:
            print("Error statistics:", e)
            cat = []
            borrower = []

        # Xóa dữ liệu cũ
        for i in self.tree_category.get_children():
            self.tree_category.delete(i)
        for i in self.tree_borrower.get_children():
            self.tree_borrower.delete(i)

        # Thể loại
        if cat:
            for idx, row in enumerate(cat, start=1):
                self.tree_category.insert("", tk.END, values=(idx, row[0], row[1]))
        else:
            self.tree_category.insert(
                "", tk.END, values=("-", "Không có dữ liệu", "-")
            )

        # Người mượn
        if borrower:
            for idx, row in enumerate(borrower, start=1):
                self.tree_borrower.insert("", tk.END, values=(idx, row[0], row[1]))
        else:
            self.tree_borrower.insert(
                "", tk.END, values=("-", "Không có dữ liệu", "-")
            )