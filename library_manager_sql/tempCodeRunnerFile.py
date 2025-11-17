# tempCodeRunnerFile.py
import tkinter as tk
import sys, os
from tkinter import messagebox
from ui.frames.login_frame import LoginFrame
from ui.components.sidebar import Sidebar
from ui.components.header import Header
from ui.frames.books_frame import BooksFrame
from ui.frames.borrowers_frame import BorrowersFrame
from ui.frames.employees_frame import EmployeesFrame
from ui.frames.statistics_frame import StatisticsFrame  
sys.path.append(os.path.dirname(__file__))

class LibraryApp(tk.Tk):
    def __init__(self, user):
        super().__init__()
        self.title("Quản Lý Thư Viện")
        self.geometry("1200x700")  # ĐÃ SỬA: KHÔNG FULLSCREEN
        self.configure(bg="#f0f0f0")

        # Container chính
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

        # Render frames
        self.frames = {}
        for F in (BooksFrame, BorrowersFrame, EmployeesFrame, StatisticsFrame):
            frame = F(self.content_frame, self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("BooksFrame")

    def show_frame(self, name):
        frame = self.frames[name]
        frame.tkraise()

    def logout(self):
        if messagebox.askyesno("Đăng xuất", "Bạn có chắc muốn đăng xuất?"):
            self.destroy()
            main()

def main():
    root = tk.Tk()
    root.withdraw()
    login_window = LoginFrame(root, on_success=lambda user: (root.destroy(), LibraryApp(user).mainloop()))
    login_window.mainloop()

if __name__ == "__main__":
    main()