import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import core


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Character Counter")
        self.geometry("620x700")
        self.path = tk.StringVar()
        self.marker = tk.StringVar(value="1.")
        self.target = tk.StringVar(value="3890")
        self.spaces = tk.BooleanVar(value=True)
        pad = {"padx": 6, "pady": 5}

        top = ttk.Frame(self)
        top.pack(fill="x", **pad)
        ttk.Entry(top, textvariable=self.path).pack(side="left", fill="x", expand=True)
        ttk.Button(top, text="파일 선택", command=self.pick).pack(side="left", padx=(6, 0))

        row = ttk.Frame(self)
        row.pack(fill="x", **pad)
        ttk.Label(row, text="회차 구분").pack(side="left")
        ttk.Combobox(row, textvariable=self.marker, values=list(core.MARKERS), state="readonly", width=8).pack(side="left", padx=6)
        ttk.Entry(row, textvariable=self.target, width=8, justify="center").pack(side="left")
        ttk.Button(row, text="글자수 세기", command=self.run).pack(side="left", padx=6)
        ttk.Button(row, text="결과지우기", command=self.clear).pack(side="left")
        ttk.Checkbutton(self, text="공백 포함해서 세기", variable=self.spaces).pack(anchor="w", padx=8)

        self.info = ttk.Label(self, text="", wraplength=580, justify="left")
        self.info.pack(fill="x", **pad)

        self.tree = ttk.Treeview(self, columns=("ep", "n", "d"), show="headings", height=22)
        for c, t, w in (("ep", "회차", 120), ("n", "글자수", 140), ("d", "목표 대비", 140)):
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor="center")
        self.tree.pack(fill="both", expand=True, **pad)

    def pick(self):
        p = filedialog.askopenfilename(filetypes=[("문서", "*.hwp *.hwpx *.txt"), ("모든 파일", "*.*")])
        if p:
            self.path.set(p)

    def clear(self):
        self.tree.delete(*self.tree.get_children())
        self.info.config(text="")

    def run(self):
        p = self.path.get().strip().strip('"')
        if not os.path.isfile(p):
            return messagebox.showwarning("파일 없음", "파일을 먼저 선택해 주세요.")
        try:
            goal = int(self.target.get().replace(",", "") or 0)
        except ValueError:
            return messagebox.showwarning("목표 글자수", "목표 글자수는 숫자로 입력해 주세요.")
        try:
            res = core.analyze(p, self.marker.get(), self.spaces.get())
        except Exception as e:
            return messagebox.showerror("읽기 실패", str(e))
        self.clear()
        if not res:
            self.info.config(text="'%s' 형식의 회차 구분을 찾지 못했어요. 구분 형식을 바꿔 보세요." % self.marker.get())
            return
        short = 0
        for ep, n in res:
            diff = ""
            if goal and n < goal:
                diff = "%d" % (n - goal)
                short += 1
            self.tree.insert("", "end", values=(ep, "{:,}".format(n), diff))
        self.info.config(text="%s\n총 %d회차 / 목표 미달 %d회차" % (p, len(res), short))


if __name__ == "__main__":
    App().mainloop()
