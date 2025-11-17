import tkinter as tk

class Sidebar(tk.Frame):
    def __init__(self, parent, on_select):
        super().__init__(parent, bg='#0f1724', width=220)
        self.on_select = on_select
        self.pack_propagate(0)
        buttons = [
            ('Người mượn', 'BorrowersFrame'),
            ('Sách', 'BooksFrame'),
            ('Nhân viên', 'EmployeesFrame'),
            ('Thống kê', 'StatisticsFrame'),
        ]
        for text, name in buttons:
            b = tk.Button(self, text=text, fg='white', bg='#0b1220', activebackground='#1f6feb', relief='flat',
                          font=('Segoe UI', 10, 'bold'), command=lambda n=name: self.on_select(n))
            b.pack(fill='x', padx=12, pady=8, ipadx=5, ipady=8)
