import random
import tkinter as tk
from datetime import datetime
from queue import Queue
from threading import Thread
from tkinter import *
from tkinter import ttk, colorchooser
from tkinter.filedialog import askopenfilename
import pywintypes
from PIL import Image, ImageTk
from markdown2 import Markdown
from sqlitedict import SqliteDict
from TkHtmlView import TkHtmlView
import sys, os
from ttkbootstrap.widgets.calendar import DateEntry
from window_effect import WindowEffect


class CountBoard(object):
    def __init__(self, title, icon, alpha, topmost, bg, width, height, width_adjust, higth_adjust, theme_name,
                 exe_dir_path,mydb_dict,mysetting_dict):
        # 传参
        self.title = title
        self.icon = icon
        self.alpha = alpha
        self.topmost = topmost
        self.width = width
        self.height = height
        self.width_adjust = width_adjust
        self.higth_adjust = higth_adjust
        self.bg = bg
        self.exe_dir_path = exe_dir_path
        self.mydb_dict = mydb_dict
        self.mysetting_dict = mysetting_dict


        # 窗口初始化
        self.root = tk.Toplevel()
        self.root.title(title)
        self.root.configure(bg=bg)
        self.root.iconbitmap(icon)
        self.root.wm_attributes('-alpha', alpha)
        self.root.wm_attributes('-topmost', topmost)
        self.root.geometry("%dx%d%+d%+d" % (width, height, width_adjust, higth_adjust))
        print("%dx%d%+d%+d" % (width, height, width_adjust, higth_adjust))
        self.root.maxsize(width, 2000)
        self.root.minsize(width, 80)
        self.root.overrideredirect(1)
        self.queue = Queue()  # 子线程与主线程的队列作为中继
        self.root.after(1000, self.relay)

        # 布局1
        self.frame_bottom = Frame(self.root, bg=self.bg, height=15, width=self.width)
        self.frame_bottom.pack(side=BOTTOM)
        self.frame_bottom.pack_propagate(0)
        # 自定义的sizegrip
        style = ttk.Style()
        style.configure('myname.TSizegrip', background=self.bg)
        self.sizegrip = ttk.Sizegrip(self.frame_bottom, style='myname.TSizegrip')

        # 布局2
        self.frame_top = Frame(self.root, bg=self.bg)
        self.frame_top.pack(side=TOP, fill="both", expand=True)
        # 画布
        self.canvas = Canvas(self.frame_top)
        self.canvas = Canvas(self.frame_top, bg=bg)
        self.canvas.config(highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill="both", expand=True)
        # 事件
        self.canvas.bind('<ButtonPress-1>', self._on_tap)
        self.canvas.bind('<ButtonRelease-1>', self._on_re)
        self.canvas.bind('<B1-Motion>', self._on_move)
        self.frame_bottom.bind('<ButtonPress-1>', self._on_tap)
        self.frame_bottom.bind('<ButtonRelease-1>', self._on_re)
        self.frame_bottom.bind('<B1-Motion>', self._on_move)

        # 其他初始化
        self.root_x, self.root_y, self.abs_x, self.abs_y = 0, 0, 0, 0

        # 获取句柄的两种方式
        self.hwnd = pywintypes.HANDLE(int(self.root.frame(), 16))
        # self.hwnd = win32gui.FindWindow(None, title)
        self.window_effect = WindowEffect()
        self.tile_theme_name = self.mysetting_dict['tile_theme_name'][0]
        self.tile_sizegrip = self.mysetting_dict['tile_sizegrip'][0]
        self.task_radius = self.mysetting_dict['task_radius'][0]
        self.set_sizegrip(self.tile_sizegrip)
        self.set_theme(tile_theme_name=self.tile_theme_name)

        # 任务列表
        self.tasks = Tasks(pre_window=self)
        self.tasks.show_all()

        # self.root.mainloop()

    def relay(self):
        """
        更新主线程UI
        """
        while not self.queue.empty():
            content = self.queue.get()
            print(content)
            if content == "show_sizegrip":
                self.update_sizegrip(1)
            elif content == "close_sizegrip":
                self.update_sizegrip(0)
            elif content == "update_theme_Acrylic":
                self.update_theme("Acrylic")
            elif content == "update_theme_Aero":
                self.update_theme("Aero")
            elif content == "set_task_right_angle":
                self.update_task_radius(0)
            elif content == "set_task_round_angle":
                self.update_task_radius(25)
            elif content == "set_window_top":
                self.set_top(1)
            elif content == "cancel_window_top":
                self.set_top(0)
            elif content == "refresh_tasks":
                self.tasks.refresh_tasks()

        self.root.after(100, self.relay)

    def update_theme(self, tile_theme_name):
        """
        外部调用，更新主题
        """
        self.tile_theme_name=tile_theme_name
        self.window_effect.removeBackgroundEffect(self.hwnd)
        if tile_theme_name == "Acrylic":
            self.window_effect.setAcrylicEffect(self.hwnd)
        else:
            self.window_effect.setAeroEffect(self.hwnd)

    def update_task_radius(self, task_radius):
        """
        外部调用，设置是否圆角
        """
        self.tasks.refresh_(task_radius)

    def update_sizegrip(self, flag):
        """
        外部调用，是否显示大小握把
        """
        if flag == 1:
            self.sizegrip.pack(side=RIGHT, anchor="ne")
            self.sizegrip.bind('<ButtonPress-1>', self._on_tap)
            self.sizegrip.bind('<ButtonRelease-1>', self._on_re)
            self.sizegrip.bind('<B1-Motion>', self.resize)
        else:
            self.sizegrip.pack_forget()
            self.sizegrip.unbind_all('<ButtonPress-1>')
            self.sizegrip.unbind_all('<ButtonRelease-1>')
            self.sizegrip.unbind_all('<B1-Motion>')

    def set_sizegrip(self, flag):
        """
        直接设置，是否显示大小握把
        """
        if flag == 1:
            self.sizegrip.pack(side=RIGHT, anchor="ne")
            self.sizegrip.bind('<ButtonPress-1>', self._on_tap)
            self.sizegrip.bind('<ButtonRelease-1>', self._on_re)
            self.sizegrip.bind('<B1-Motion>', self.resize)
        else:
            self.sizegrip.pack_forget()
            self.sizegrip.unbind_all('<ButtonPress-1>')
            self.sizegrip.unbind_all('<ButtonRelease-1>')
            self.sizegrip.unbind_all('<B1-Motion>')

    def resize(self, event):
        """
        握把的回调函数，用来控制大小
        """
        deltax = event.x_root - self.root.winfo_rootx()
        deltay = event.y_root - self.root.winfo_rooty()
        if deltax < 1:
            deltax = 1
        if deltay < 1:
            deltay = 1
        self.root.geometry("%sx%s" % (deltax, deltay))

    def set_theme(self, tile_theme_name):
        """
        直接设置，设置主题
        """
        if tile_theme_name == "Acrylic":
            self.window_effect.setAcrylicEffect(self.hwnd)
        else:
            self.window_effect.setAeroEffect(self.hwnd)

    def set_background(self, bg):
        """
        设置Acrylic模式下，进行移动时的窗口背景
        """
        self.root.configure(bg=bg)
        self.frame_top.configure(bg=bg)
        self.canvas.configure(bg=bg)
        self.frame_bottom.configure(bg=bg)

    def set_top(self, flag):
        """
        外部调用，设置是否置顶
        """
        if flag == 1:
            self.root.wm_attributes('-topmost', 1)
        else:
            self.root.wm_attributes('-topmost', 0)

    def _on_re(self, event):
        if self.tile_theme_name == "Acrylic":
            self.window_effect.setAcrylicEffect(self.hwnd)
            self.set_background(bg="black")

    def _on_move(self, event):
        offset_x = event.x_root - self.root_x
        offset_y = event.y_root - self.root_y
        if self.width and self.height:
            geo_str = "%sx%s+%s+%s" % (self.width, self.height,
                                       self.abs_x + offset_x, self.abs_y + offset_y)
        else:
            geo_str = "+%s+%s" % (self.abs_x + offset_x, self.abs_y + offset_y)
        self.root.geometry(geo_str)

    def _on_tap(self, event):
        if self.tile_theme_name == "Acrylic":
            self.set_background(bg="grey")
            self.window_effect.removeBackgroundEffect(self.hwnd)

        self.width = self.root.winfo_width()
        self.height = self.root.winfo_height()
        self.root_x, self.root_y = event.x_root, event.y_root
        self.abs_x, self.abs_y = self.root.winfo_x(), self.root.winfo_y()


class Tasks:
    def __init__(self, pre_window, **kwargs, ):
        # 传递的参数
        self.pre_window = pre_window
        self.root = pre_window.root
        self.width = pre_window.width
        self.exe_dir_path = pre_window.exe_dir_path
        self.canvas = pre_window.canvas
        self.mydb_dict = pre_window.mydb_dict
        self.mysetting_dict = pre_window.mysetting_dict
        self.task_radius = pre_window.task_radius

        # x左右边距，y上下边距
        self.task_init_x = 12
        self.task_init_y = 12
        # 高度，宽度，是否圆角
        self.task_width = 276
        self.task_height = 60

        self.__init_update_time()

    def __init_update_time(self):
        # 初始化更新时间
        from datetime import datetime
        for key, value in self.mydb_dict.iteritems():
            startdate = datetime.today()
            enddate = datetime.strptime(value[1], '%Y-%m-%d')
            days = str((enddate - startdate).days)
            self.mydb_dict[key] = [value[0], value[1], days, value[3], value[4], value[5]]

    def del_all(self):
        # 删除所有数据
        self.canvas.delete("all")
        for key in self.mydb_dict.iterkeys():
            self.mydb_dict.__delitem__(key)

    def show_all(self):
        # 展示当前数据库的所以元素
        self.canvas.delete("all")
        for value in sorted(self.mydb_dict.itervalues(), key=self.get_int_day):
            self.add_task(value)

    def get_int_day(self, value):
        # 返回第三个值,时间值
        return int(value[2])

    def round_rectangle(self, x1, y1, x2, y2, radius=25, **kwargs):
        points = [x1 + radius, y1,
                  x1 + radius, y1,
                  x2 - radius, y1,
                  x2 - radius, y1,
                  x2, y1,
                  x2, y1 + radius,
                  x2, y1 + radius,
                  x2, y2 - radius,
                  x2, y2 - radius,
                  x2, y2,
                  x2 - radius, y2,
                  x2 - radius, y2,
                  x1 + radius, y2,
                  x1 + radius, y2,
                  x1, y2,
                  x1, y2 - radius,
                  x1, y2 - radius,
                  x1, y1 + radius,
                  x1, y1 + radius,
                  x1, y1]
        self.canvas.create_polygon(points, **kwargs, smooth=True, width=1, outline="#080808")

    def add_task(self, value):
        self.task_main_text = value[0]
        self.task_time_text = value[1]
        mode = self.mysetting_dict["mode"][0]
        if mode == "普通模式":
            self.task_countdown_text = str(int(value[2]) + 1)
        else:
            self.task_countdown_text = value[2]
        self.task_color = value[3]
        self.task_tag_name = value[4]
        self.task_text_color = value[5]

        self.round_rectangle(self.task_init_x, self.task_init_y, self.task_init_x + self.task_width,
                             self.task_init_y + self.task_height, radius=self.task_radius,
                             fill=self.task_color,
                             tag=(self.task_tag_name))

        self.canvas.create_text(self.task_init_x + 8, self.task_init_y + 20,
                                text=self.task_main_text,
                                width=220,
                                font=('microsoft yahei', 15, 'normal'),
                                fill=self.task_text_color,
                                anchor=W,
                                justify=LEFT,
                                tag=(self.task_tag_name))

        self.canvas.create_text(self.task_init_x + 8,
                                self.task_init_y + 45,
                                text=self.task_time_text,
                                width=220,
                                font=('Times', 8, 'italic'),
                                fill=self.task_text_color,
                                anchor=W,
                                justify=LEFT,
                                tag=(self.task_tag_name))
        self.canvas.create_text(self.task_init_x + 250,
                                self.task_init_y + 30,
                                text=self.task_countdown_text + "天",
                                width=220,
                                font=('microsoft yahei', 20, 'bold'),
                                fill=self.task_text_color,
                                anchor=E,  # 以右侧为毛点
                                justify=RIGHT,
                                tag=(self.task_tag_name))
        # 添加绑定函数
        self.canvas.tag_bind(self.task_tag_name, '<Double-Button-1>',
                             func=self.handler_adaptor(self.task_DoubleClick, task_tag_name=self.task_tag_name))

        # # 更新数据库
        # self.mydict[value[0]]=value

        # 更新新添加的高度
        self.task_init_y = self.task_init_y + self.task_height + 15

    def add_one(self, value):
        # 更新数据库
        self.mydb_dict[value[0]] = value

    def handler_adaptor(self, fun, **kwds):
        return lambda event, fun=fun, kwds=kwds: fun(event, **kwds)

    def task_DoubleClick(self, event, task_tag_name):
        for value in self.mydb_dict.itervalues():
            if value[4] == task_tag_name:
                Newtask_window(
                    height=180,
                    pre_window=self.pre_window,
                    value=value)
                return 1
        print("no!" + task_tag_name)

    def del_one(self, value):
        self.mydb_dict.__delitem__(value)

    def refresh_tasks(self):
        # 画布删除,重新画
        self.canvas.delete("all")
        self.task_init_y = 15
        self.show_all()

    def refresh_(self, task_radius):
        # 画布删除,重新画
        self.task_radius = task_radius
        self.canvas.delete("all")
        self.task_init_y = 15
        self.show_all()


class Newtask_window(object):
    def __init__(self, height, pre_window, **kwargs):
        # 传递参数
        self.pre_window = pre_window
        self.width, self.height = pre_window.width, height
        self.tasks = pre_window.tasks
        self.pre_window_root = pre_window.root
        self.exe_dir_path = pre_window.exe_dir_path

        # 窗口初始化
        self.root = tk.Toplevel()
        self.root.title('新建日程')
        self.root.iconbitmap("favicon.ico")
        self.root.wm_attributes('-topmost', 1)
        # 居中显示
        win_width = self.root.winfo_screenwidth()
        win_higth = self.root.winfo_screenheight()
        width_adjust = (win_width - self.width) / 2
        higth_adjust = (win_higth - self.height) / 2
        self.root.geometry("%dx%d-%d-%d" % (self.width, self.height, width_adjust, higth_adjust))

        # 窗口布局
        self.main_frame = ttk.Frame(self.root, padding=20)
        self.main_frame.pack(fill=tk.X)

        # 第一行框架
        entry_spin_frame = ttk.Frame(self.main_frame)
        entry_spin_frame.pack(fill=tk.X, pady=5)
        ttk.Label(
            master=entry_spin_frame,
            text='日程名称  '
        ).pack(side=tk.LEFT, fill=tk.X)
        self.task_name_entry = ttk.Entry(entry_spin_frame,validate="focus", validatecommand=self.clear)
        self.task_name_entry.pack(side=tk.LEFT, fill=tk.X, expand=tk.YES)

        # 第二行框架
        timer_frame = ttk.Frame(self.main_frame)
        timer_frame.pack(fill=tk.X, pady=5)
        ttk.Label(
            master=timer_frame,
            text='选择时间  '
        ).pack(side=tk.LEFT, fill=tk.X)
        self.date_entry = DateEntry(timer_frame)
        self.date_entry.pack(side=tk.LEFT, fill=tk.X, expand=tk.YES, padx=3)

        # 第三行框架
        ok_frame = ttk.Frame(self.main_frame)
        ok_frame.pack(fill=tk.X, pady=5)
        ttk.Button(
            master=ok_frame,
            text='确认',
            bootstyle='outline',
            command=self.ok,
        ).pack(side=tk.RIGHT, fill=tk.X, expand=tk.YES, padx=3)

        # 其他初始化
        self.modify_flag = 0
        self.task_name_entry.insert(0, "创建你的日程吧！")

        # '''***********************************下面区别于new_task**************************************************'''
        for key in kwargs:
            if key == "value":
                # 其他初始化
                self.modify_flag = 1
                self.root.title('修改日程')
                self.value = kwargs["value"]

                # 配置参数,初始化
                self.task_name_entry.delete(0, "end")
                self.task_name_entry.insert(0, self.value[0])

                self.date_entry.entry.delete(0, "end")
                self.date_entry.entry.insert(0, self.value[1])

                self.del_task_button=ttk.Button(
                    master=ok_frame,
                    text='删除',
                    style='danger.Outline.TButton',
                    command=self.del_task,
                ).pack(side=tk.LEFT, padx=3)
        self.root.mainloop()

    def del_task(self):
        self.tasks.del_one(self.value[0])
        self.tasks.refresh_tasks()
        self.root.destroy()

    def clear(self):
        # 点击输入框的回调,删除提示内容
        if "创建你的日程" in self.task_name_entry.get():
            self.task_name_entry.delete(0, "end")

    def ok(self):
        if self.modify_flag == 1:
            # 先删除一项,然后再添加一项
            self.tasks.del_one(self.value[0])

        # 点击确认按钮,更新数据库
        startdate = datetime.today()
        enddate = datetime.strptime(self.date_entry.entry.get(), '%Y-%m-%d')
        days = str((enddate - startdate).days)
        value = [self.task_name_entry.get(),
                 self.date_entry.entry.get(),
                 days,
                 "#080808",
                 ''.join(random.sample('zyxwvutsrqponmlkjihgfedcba1234567890', 5)),
                 "white"]
        print(value)
        self.tasks.add_one(value)
        self.tasks.refresh_tasks()
        self.root.destroy()


class Ask_del_window(object):
    def __init__(self, height, pre_window, **kwargs):
        # 传递参数
        self.pre_window = pre_window
        self.pre_window_root = pre_window.root
        self.width = pre_window.width
        self.tasks = pre_window.tasks
        self.height = height
        self.exe_dir_path = pre_window.exe_dir_path

        # 窗口初始化
        self.root = tk.Toplevel()
        self.root.title('删除全部')
        self.root.iconbitmap("favicon.ico")
        self.root.wm_attributes('-topmost', 1)

        # 居中显示
        win_width = self.root.winfo_screenwidth()
        win_higth = self.root.winfo_screenheight()
        width_adjust = (win_width - self.width) / 2
        higth_adjust = (win_higth - self.height) / 2
        self.root.geometry("%dx%d-%d-%d" % (self.width, self.height, width_adjust, higth_adjust))

        # 布局
        self.frame_top = Frame(self.root)
        self.frame_top.pack(side=TOP, padx=20, pady=5, expand=True, fill=X)
        self.frame_bottom = Frame(self.root)
        self.frame_bottom.pack(side=BOTTOM, padx=20, expand=True, fill=X)

        self.lable = ttk.Label(self.frame_top, text="是否要删除全部?")
        self.lable.pack(side=tk.LEFT, padx=5, pady=2, expand=True, fill=X)

        self.cancel_button = ttk.Button(
            master=self.frame_bottom,
            text='取消',
            bootstyle='outline',
            command=self.cancel, )
        self.cancel_button.pack(side=tk.RIGHT, fill=tk.X, expand=tk.YES, padx=3)

        self.ok_button = ttk.Button(
            master=self.frame_bottom,
            text='确认',
            bootstyle='outline',
            command=self.ok, )
        self.ok_button.pack(side=tk.RIGHT, fill=tk.X, expand=tk.YES, padx=3)

        self.root.mainloop()

    def cancel(self):
        self.root.destroy()

    def ok(self):
        self.tasks.del_all()
        self.root.destroy()


class Setting_window(object):
    def __init__(self, height, pre_window, **kwargs):
        self.root = tk.Toplevel()
        self.root.title('设置')
        self.root.iconbitmap("favicon.ico")
        self.exe_dir_path = pre_window.exe_dir_path

        self.pre_window = pre_window
        self.tasks = pre_window.tasks
        self.pre_window_root = pre_window.root
        self.width = pre_window.width
        self.height = height

        # setting 数据库
        self.mydict = SqliteDict(self.exe_dir_path + '/setting.sqlite', autocommit=True)
        self.theme_color_str = tk.StringVar()
        self.mode_combobox_str = tk.StringVar()
        self.theme_color_str.set(self.mydict["theme"][0])
        self.mode_combobox_str.set(self.mydict["mode"][0])

        # 获取上一个窗体的坐标
        self.pre_window_root_x, self.pre_window_root_y, self.pre_window_root_w, self.pre_window_root_h = \
            self.pre_window_root.winfo_x(), \
            self.pre_window_root.winfo_y(), \
            self.pre_window_root.winfo_width(), \
            self.pre_window_root.winfo_height()
        self.width_adjust = self.pre_window_root_x
        self.height_adjust = self.pre_window_root_y + self.pre_window_root_h + 40

        # 右上角显示
        self.root.geometry("%dx%d+%d+%d" % (self.width, self.height, self.width_adjust, self.height_adjust))

        # 布局
        self.frame_top = Frame(self.root)
        self.frame_top.pack(side=TOP, padx=20, pady=10)
        self.frame_middle = Frame(self.root)
        self.frame_middle.pack(side=TOP, padx=20, pady=1)
        self.frame_bottom = Frame(self.root)
        self.frame_bottom.pack(side=BOTTOM, padx=20, expand=True, fill=X)

        # 背景颜色
        self.theme_lable = ttk.Label(self.frame_top, text="主题颜色")
        self.theme_lable.pack(side=tk.LEFT, padx=5, pady=2)
        self.theme_color_frame = tk.Entry(self.frame_top, width=10, textvariable=self.theme_color_str)  # 10个字符的宽度
        self.theme_color_frame.pack(side=tk.LEFT)
        self.theme_color_photo_image = ImageTk.PhotoImage(
            Image.open(self.exe_dir_path + "/img/" + "颜色.png").resize((15, 15)))
        self.theme_color_button = tk.Button(self.frame_top,
                                            command=self.theme_onChoose,
                                            text="背景颜色",
                                            image=self.theme_color_photo_image, relief="flat", overrelief="groove")
        self.theme_color_button.pack(side=tk.LEFT)
        # 设置颜色块颜色
        self.theme_color_frame.config(background=self.theme_color_str.get())

        # 设置很长的lable,可以固定左侧
        tk.Label(self.frame_top, state="disable", width=1000).pack(side=tk.LEFT, expand=True, fill=X)

        # 计时模式
        self.mode_lable = ttk.Label(self.frame_middle, text="计时模式")
        self.mode_lable.pack(side=tk.LEFT, padx=5, pady=2)
        self.mode_combobox = ttk.Combobox(self.frame_middle, width=26, values=["普通模式", "紧迫模式"], state="readonly",
                                          textvariable=self.mode_combobox_str)
        self.mode_combobox.pack(side=tk.LEFT, padx=0, pady=2)
        tk.Label(self.frame_middle, state="disable", width=1000).pack(side=tk.LEFT, expand=True, fill=X)

        # 取消按钮
        self.cancel_image = ImageTk.PhotoImage(Image.open(self.exe_dir_path + "/img/" + "取消.png").resize((18, 18)))
        self.cancel_button = tk.Button(self.frame_bottom,
                                       command=self.cancel,
                                       image=self.cancel_image,
                                       relief="flat",
                                       overrelief="groove")
        self.cancel_button.pack(side=tk.RIGHT, padx=5, pady=2)

        # 确定按钮
        self.ok_image = ImageTk.PhotoImage(Image.open(self.exe_dir_path + "/img/" + "确认.png").resize((18, 18)))
        self.ok_button = tk.Button(self.frame_bottom,
                                   command=self.ok,
                                   image=self.ok_image,
                                   relief="flat",
                                   overrelief="groove")
        self.ok_button.pack(side=tk.RIGHT, padx=5, pady=2)

        self.root.mainloop()

    def cancel(self):
        self.root.destroy()

    def theme_onChoose(self):
        (rgb, hx) = colorchooser.askcolor()
        self.theme_color_frame.config(background=hx)
        self.theme_color_frame.delete(0, 'end')
        self.theme_color_frame.insert(0, hx)

    def ok(self):
        # 更新数据库
        self.mydict["theme"] = [self.theme_color_str.get()]
        self.mydict["mode"] = [self.mode_combobox_str.get()]

        # 主窗体更新UI
        self.pre_window.set_theme(bg=self.theme_color_str.get())

        self.root.destroy()


class Help_window(object):
    def __init__(self, width, height, path):
        # 传递参数
        self.path = path
        self.width, self.height = width, height

        # 窗口初始化
        self.root = tk.Toplevel()
        self.root.title('使用说明')
        self.root.iconbitmap("favicon.ico")
        self.root.wm_attributes('-topmost', 1)

        # 居中显示
        win_width = self.root.winfo_screenwidth()
        win_higth = self.root.winfo_screenheight()
        width_adjust = (win_width - self.width) / 2
        higth_adjust = (win_higth - self.height) / 2
        self.root.geometry("%dx%d+%d+%d" % (self.width, self.height, width_adjust, higth_adjust))

        # 窗口布局
        self.frame_bottom = ttk.Frame(self.root)
        self.frame_bottom.pack(side=tk.BOTTOM, fill=BOTH, expand=False)
        self.frame_top = ttk.Frame(self.root, padding=20)
        self.frame_top.pack(side=tk.TOP, fill=BOTH, expand=True)

        self.HtmlView = TkHtmlView(self.frame_top, background="white")
        self.HtmlView.pack(fill='both', expand=True)

        self.filename = tk.StringVar()
        ttk.Entry(self.frame_bottom, textvariable=self.filename).pack(side=tk.LEFT, padx=20, pady=10, fill='x',
                                                                      expand=True)
        ttk.Button(self.frame_bottom, text='选择文件', command=self.open_file).pack(side=tk.LEFT, padx=20, pady=10)

        # 加载默认md文件
        self.p = Thread(target=self.init_file)
        self.p.start()

        self.root.mainloop()

    def init_file(self):
        with open(self.path, encoding='utf-8') as f:
            self.filename.set(self.path)
            md2html = Markdown()
            html = md2html.convert(f.read())
            self.HtmlView.set_html(html)

    def open_file(self):
        path = askopenfilename()
        if not path:
            return
        with open(path, encoding='utf-8') as f:
            self.filename.set(path)
            md2html = Markdown()
            html = md2html.convert(f.read())
            print(html)
            self.HtmlView.set_html(html)


if __name__ == "__main__":
    exe_dir_path = os.path.dirname(sys.argv[0])
    print(exe_dir_path)
    if not os.path.exists(exe_dir_path + "/setting.sqlite"):
        print("第一次运行")
        mydict = SqliteDict(exe_dir_path + '/setting.sqlite')
        mydict["theme"] = ["white"]
        mydict["mode"] = ["普通模式"]
        mydict.commit()
        mydict.close()

    bg = SqliteDict(exe_dir_path + '/setting.sqlite').__getitem__("theme")[0]
    countboard = CountBoard(title="CountBoard",
                            icon="favicon.ico",
                            alpha=0.9,
                            topmost=0,
                            bg="#000000",
                            width=300,
                            height=190,
                            width_adjust=20,
                            higth_adjust=20)

# -w不带控制行
# 用户名带空格--用引号C:\Users\Gao yongxian\PycharmProjects\CountBoard
# pyinstaller -F -i "C:\Users\Gao yongxian\PycharmProjects\CountBoard\favicon.ico" "C:\Users\Gao yongxian\PycharmProjects\CountBoard\Main_window.py" -w
