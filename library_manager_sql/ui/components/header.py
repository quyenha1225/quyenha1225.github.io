import tkinter as tk

class Header(tk.Frame):
    def __init__(self, parent, logout_cmd, exit_cmd):
        super().__init__(parent, bg='#1f6feb', height=64)
        self.pack_propagate(0)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)
        self.columnconfigure(2, weight=1)

        self.title_label = tk.Label(self, text='QUẢN LÝ THƯ VIỆN', bg='#1f6feb', fg='white', font=('Segoe UI', 16, 'bold'))
        self.title_label.grid(row=0, column=1, sticky='nsew')

        right_frame = tk.Frame(self, bg='#1f6feb')
        right_frame.grid(row=0, column=2, sticky='e', padx=8)
        self.lbl_user = tk.Label(right_frame, text='', bg='#1f6feb', fg='white', font=('Segoe UI', 10))
        self.lbl_user.pack(side='left', padx=6)
        btn_exit = tk.Button(right_frame, text='Thoát', command=exit_cmd, bg='#ff6b6b', fg='white', relief='flat')
        btn_exit.pack(side='left', padx=6)
