import tkinter as tk
import tkinter.ttk as ttk
import tkinter.simpledialog as simpledialog
import tkinter.messagebox as messagebox
import tkinter.filedialog as filedialog
import json
import os
import subprocess

class PlanApp:
    def __init__(self, root):
        self.root = root
        self.root.title("计划应用")

        # Treeview with two columns: 'Plan' and 'File'
        self.plan_tree = ttk.Treeview(root, columns=('Plan', 'File'), show='headings')
        self.plan_tree.heading('Plan', text='计划')
        self.plan_tree.column('Plan', stretch=tk.YES, width=350)
        self.plan_tree.heading('File', text='文件')
        self.plan_tree.column('File', stretch=tk.YES, width=150)
        self.plan_tree.pack(pady=20, expand=True, fill=tk.BOTH)

        # Hidden row
        self.dummy_target = self.plan_tree.insert("", tk.END, values=("", ""))
        self.plan_tree.item(self.dummy_target, tags="hidden")
        self.plan_tree.tag_configure("hidden", foreground="white", background="white")

        # Dragging
        self.plan_tree.bind("<Button-1>", self.on_treeview_click)
        self.plan_tree.bind("<B1-Motion>", self.on_drag_motion)
        self.plan_tree.bind("<ButtonRelease-1>", self.on_drag_release)
        self.dragging_item = None
        self.dragging_target = None

        # Buttons
        self.button_frame = tk.Frame(root)
        self.button_frame.pack(pady=20)

        self.add_button = tk.Button(self.button_frame, text="添加计划 (Alt+A)", command=self.add_plan)
        self.add_button.grid(row=0, column=0, padx=10)

        self.edit_button = tk.Button(self.button_frame, text="编辑计划 (Alt+E)", command=self.edit_plan)
        self.edit_button.grid(row=0, column=1, padx=10)

        # Shortcuts
        self.root.bind('<Alt-a>', self.add_plan)
        self.root.bind('<Alt-d>', self.delete_plan)
        self.root.bind('<Alt-e>', self.edit_plan)
        self.root.bind('<Control-d>', self.clear_all_plans)

        # Load data
        self.load_data()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.plan_tree.bind("<Double-Button-1>", self.start_edit)
        self.current_edit_item = None

        self.create_context_menu()
        self.plan_tree.bind("<Button-3>", self.on_treeview_right_click)  # <Button-2> for MacOS

        self.load_window_size()

        # 绑定窗口尺寸变化事件
        self.root.bind("<Configure>", self.on_window_resize)

        self.center_window()

    def on_treeview_click(self, event):
        item = self.plan_tree.identify('item', event.x, event.y)
        column = self.plan_tree.identify('column', event.x, event.y)
        if item and item != self.dummy_target:
            if column == "#1":
                self.dragging_item = item

    def on_drag_motion(self, event):
        if self.dragging_item:
            target = self.plan_tree.identify('item', event.x, event.y)
            if target and target != self.dragging_item:
                self.dragging_target = target

    def on_drag_release(self, event):
        if self.dragging_item:
            if self.dragging_target:
                plan_data = self.plan_tree.item(self.dragging_item, 'values')
                self.plan_tree.delete(self.dragging_item)
                if self.dragging_target == self.dummy_target:
                    self.plan_tree.insert("", self.plan_tree.index(self.dummy_target), values=plan_data)
                else:
                    self.plan_tree.insert("", self.plan_tree.index(self.dragging_target), values=plan_data)
            self.dragging_item = None
            self.dragging_target = None

    def add_plan(self, event=None):
        plan = simpledialog.askstring("添加计划", "请输入您的计划：")
        if plan:
            self.plan_tree.insert("", self.plan_tree.index(self.dummy_target), values=(plan, ""))
            self.save_data()

    def edit_plan(self, event=None):
        selected_item = self.plan_tree.selection()
        if not selected_item:
            return
        old_plan = self.plan_tree.item(selected_item, 'values')[0]
        new_plan = simpledialog.askstring("编辑计划", "修改您的计划：", initialvalue=old_plan)
        if new_plan:
            self.plan_tree.item(selected_item, values=(new_plan, self.plan_tree.item(selected_item, 'values')[1]))
            self.save_data()

    def delete_plan(self, event=None):
        selected_item = self.plan_tree.selection()
        if selected_item and selected_item[0] != self.dummy_target:
            self.plan_tree.delete(selected_item[0])
            self.save_data()
    def clear_all_plans(self, event=None):
        answer = messagebox.askyesno("确认删除", "您确定要删除所有计划吗?")
        if answer:
            for item in self.plan_tree.get_children():
                if item != self.dummy_target:
                    self.plan_tree.delete(item)
            self.save_data()

    def save_data(self):
        plans = [self.plan_tree.item(item, 'values') for item in self.plan_tree.get_children() if item != self.dummy_target]
        with open('plans.json', 'w') as f:
            json.dump(plans, f)

    def create_context_menu(self):
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="链接文件", command=self.link_file)
        self.context_menu.add_command(label="打开文件", command=self.open_file)

    def on_treeview_right_click(self, event):
        item = self.plan_tree.identify('item', event.x, event.y)
        if item:
            self.context_menu.post(event.x_root, event.y_root)
            
    def link_file(self):
        selected_item = self.plan_tree.selection()
        if selected_item:
            # 如果没有文件路径，则弹出一个文件选择对话框
            file_path = filedialog.askopenfilename(title="选择文件")
            if file_path:
                self.plan_tree.set(selected_item[0], "File", file_path)

    def open_file(self):
        selected_item = self.plan_tree.selection()
        if selected_item:
            file_path = self.plan_tree.set(selected_item, "File")
            if file_path and os.path.exists(file_path):
                if os.name == "nt":  # for Windows
                    os.startfile(file_path)
                elif os.name == "posix":  # for Linux, Mac
                    subprocess.run(["open", file_path], check=True)
            else:
                tk.messagebox.showwarning("错误", "文件路径不存在：{}".format(file_path))
    def load_data(self):
        try:
            with open('plans.json', 'r') as f:
                plans = json.load(f)
                for plan, file_path in plans:
                    self.plan_tree.insert("", self.plan_tree.index(self.dummy_target), values=(plan, file_path))
        except FileNotFoundError:
            pass

    def on_closing(self):
        self.save_data()
        self.root.destroy()

    def center_window(self):
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 360  
        window_height = 300  

        position_x = int((screen_width / 2) - (window_width / 2))
        position_y = int((screen_height / 2) - (window_height / 2) - 30 )

        self.root.geometry(f"{window_width}x{window_height}+{position_x}+{position_y}")

    def start_edit(self, event):
        col = self.plan_tree.identify_column(event.x)
        item = self.plan_tree.identify_row(event.y)
        
        if self.current_edit_item:
            self.save_edit(self.current_edit_item, "#1")
            self.cancel_edit()

        if item == self.dummy_target or col != "#1":
            return

        bbox_result = self.plan_tree.bbox(item, column=col)
        if not bbox_result or len(bbox_result) != 4:
            return  

        x, y, width, height = bbox_result

        self.edit_entry = tk.Entry(self.plan_tree)
        self.edit_entry.place(x=x, y=y, width=width, height=height)

        self.edit_entry.insert(0, self.plan_tree.item(item, 'values')[0])
        self.edit_entry.focus()

        self.edit_entry.bind('<Return>', lambda e: self.save_edit(item, col))
        self.edit_entry.bind('<Escape>', lambda e: self.cancel_edit())
            
        self.current_edit_item = item  

    def save_edit(self, item, col):
        value = self.edit_entry.get()
        self.plan_tree.set(item, column=col, value=value)
        self.current_edit_item = None
        self.edit_entry.destroy()

    def cancel_edit(self):
        self.current_edit_item = None
        self.edit_entry.destroy()

    def on_window_resize(self, event):
        # 保存窗口尺寸
        window_size = {"width": self.root.winfo_width(), "height": self.root.winfo_height()}
        with open("window_size.json", "w") as file:
            json.dump(window_size, file)

    def load_window_size(self):
        # 读取窗口尺寸
        if os.path.exists("window_size.json"):
            with open("window_size.json", "r") as file:
                window_size = json.load(file)
                self.root.geometry(f"{window_size['width']}x{window_size['height']}")

class FloatingBall:
    def __init__(self, master, plan_app):
        self.master = master
        self.plan_app = plan_app
        self.float_ball = tk.Toplevel(self.master)
        self.float_ball.overrideredirect(True)
        self.float_ball.geometry("200x100+100+100")
        self.float_ball.attributes("-alpha", 0.9, "-topmost", True)  # set topmost
        self.float_ball.configure(bg="white")

        self.text_widget = tk.Text(self.float_ball, height=4, width=25)
        self.text_widget.pack(pady=10, padx=10)
        self.text_widget.configure(state=tk.DISABLED)

        self.is_dragging = False
        self.float_ball.bind("<Button-1>", self.start_drag)
        self.float_ball.bind("<B1-Motion>", self.do_drag)
        self.float_ball.bind("<ButtonRelease-1>", self.stop_drag)
        self.float_ball.bind("<Double-Button-1>", self.restore_app)

        self.update_text()

        self.hide()

        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()

        # Calculate the initial position for the floating ball
        ball_width = 200
        ball_height = 100
        position_x = screen_width - ball_width - 10  # 10 pixels from the right edge
        position_y = int(screen_height / 4)  # place it a quarter way down from the top

        self.float_ball.geometry(f"{ball_width}x{ball_height}+{position_x}+{position_y}")
        self.float_ball.configure(bg="white", bd=1, relief="solid")  # Add a black border

    def update_text(self):
        plans = [self.plan_app.plan_tree.item(item, 'values')[0] for item in self.plan_app.plan_tree.get_children() if item != self.plan_app.dummy_target][:3]
        self.text_widget.configure(state=tk.NORMAL)
        self.text_widget.delete("1.0", tk.END)
        for plan in plans:
            self.text_widget.insert(tk.END, plan + '\n')
        self.text_widget.configure(state=tk.DISABLED)

    def show(self):
        self.float_ball.deiconify()

    def hide(self):
        self.float_ball.withdraw()

    def start_drag(self, event):
        self.is_dragging = True
        self.start_x = event.x
        self.start_y = event.y

    def do_drag(self, event):
        if self.is_dragging:
            x = self.float_ball.winfo_x() - self.start_x + event.x
            y = self.float_ball.winfo_y() - self.start_y + event.y
            self.float_ball.geometry(f"+{x}+{y}")

    def stop_drag(self, event):
        self.is_dragging = False

    def restore_app(self, event):
        self.master.deiconify()
        self.hide()

class PlanAppExtended(PlanApp):
    def __init__(self, root):
        super().__init__(root)

        # Floating Ball
        self.float_ball = FloatingBall(self.root, self)

        # Button to enable floating ball mode
        self.float_mode_button = tk.Button(self.button_frame, text="悬浮球模式", command=self.enable_float_mode)
        self.float_mode_button.grid(row=0, column=2, padx=10)

        # Overriding the on_closing method to handle float ball
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing_extended)

    def enable_float_mode(self):
        self.root.withdraw()
        self.float_ball.show()

    def on_closing_extended(self):
        # When closing the app, also destroy the float ball
        self.float_ball.float_ball.destroy()
        self.on_closing()

# Test the extended app with the floating ball
if __name__ == "__main__":
    root = tk.Tk()
    app = PlanAppExtended(root)
    root.mainloop()