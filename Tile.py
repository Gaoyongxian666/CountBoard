# -*- coding: UTF-8 -*-
"""
@Project ：CountBoard
@File ：Tile.py
@Author ：Gao yongxian
@Date ：2021/11/8 11:00
@contact: g1695698547@163.com
"""
import json
import queue
import random
import tkinter as tk
import traceback
import webbrowser
from datetime import datetime
from pathlib import Path
from queue import Queue
from threading import Thread
from tkinter import *
import ttkbootstrap as ttk
from tkinter.filedialog import askopenfilename
import pywintypes
import requests
import win32gui
from markdown2 import Markdown
from CustomWindow import CustomWindow
from TkHtmlView import TkHtmlView
from ttkbootstrap.widgets.date_entry import DateEntry
from WindowEffect import WindowEffect


class Tile(CustomWindow):
    """磁贴窗口"""

    def __init__(self, bg, exe_dir_path, mydb_dict, mysetting_dict, tile_queue, logger, *args, **kwargs):
        self.root = tk.Toplevel()
        super().__init__(*args, **kwargs)

        # 布局初始化
        self.__init__2(bg, exe_dir_path, mydb_dict, mysetting_dict, tile_queue, logger, *args, **kwargs)

        # 开启更新UI队列
        self.root.after(1, self.relay)

        # 开启耗时操作线程
        self.initialization_thread = Thread(target=self.initialization)
        self.initialization_thread.setDaemon(True)
        self.initialization_thread.start()

        self.root.mainloop()

    def __init__2(self, bg, exe_dir_path, mydb_dict, mysetting_dict, tile_queue, logger, *args, **kwargs):
        """
        布局初始化(必须在主线程进行的操作，比如设置主题，窗口布局，变量初始化)
        """
        # 传参
        self.logger = logger
        self.bg = bg
        self.exe_dir_path = exe_dir_path
        self.mydb_dict = mydb_dict
        self.mysetting_dict = mysetting_dict
        self.tile_queue = tile_queue  # 子线程与主线程的队列作为中继
        # 布局
        self.frame_top = Frame(self.root, bg=self.bg)
        # self.frame_top.configure(highlightbackground="#202020")
        # self.frame_top.configure(highlightthickness=1)
        self.frame_top.pack(side=TOP, fill="both", expand=True)
        # 画布
        self.canvas = Canvas(self.frame_top)
        self.canvas.config(highlightthickness=1)
        self.canvas.configure(highlightbackground="#000000")
        self.canvas.pack(side=tk.LEFT, fill="both", expand=True)
        # 事件
        self.canvas.bind('<ButtonPress-1>', self._on_tap)
        self.canvas.bind('<ButtonRelease-1>', self._on_release)
        self.canvas.bind('<B1-Motion>', self._on_move)
        self.canvas.bind("<Button-3>", self._on_right_menu)  # 绑定右键鼠标事件
        self.menubar = Menu(self.canvas, tearoff=False)  # 创建一个菜单

        # 窗口特效
        self.hwnd = pywintypes.HANDLE(int(self.root.frame(), 16))
        self.window_effect = WindowEffect()

        # 保存单个日程的tag
        self.tag_name = tk.StringVar()
        # 父窗口句柄
        self.hhwnd = 0

    def _on_right_menu(self, event):
        self.tile_queue.put(("right_menu", (event.x_root, event.y_root)))

    def right_menu(self, content):
        event_x_root = content[0]
        event_y_root = content[1]
        self.menubar.delete(0, END)
        self.menubar.add_command(label='新建日程', command=self.open_new_winodw)
        if self.tag_name.get() != "":
            self.menubar.add_command(label='编辑日程', command=self.open_edit_winodw)
            self.menubar.add_command(label='删除日程', command=self.open_del_winodw)
        self.menubar.post(event_x_root, event_y_root)

    def open_new_winodw(self):
        """打开新窗口"""
        self.tile_queue.put("NewTaskWindow")

    def open_edit_winodw(self):
        """打开编辑窗口"""
        self.tile_queue.put("EidtTaskWindow")

    def open_del_winodw(self):
        self.tile_queue.put("DelTaskWindow")

    def modify_transparent(self, tile_transparent):
        """修改透明度"""
        if tile_transparent == 1:
            self.tile_transparent = tile_transparent
        else:
            self.tile_transparent = tile_transparent

        self.set_theme(self.tile_theme_name)

    '''-----------------------------------更新UI 线程-----------------------------------------------'''

    def relay(self):
        """更新UI队列"""
        try:
            # 队列不可阻塞
            content = self.tile_queue.get(False)
            self.logger.info(self.__class__.__name__ + " --Queue接收到消息:" + str(content))
            # 回调函数要在之前回调,因为如果在队列中打开窗体,窗体的 mailoop 会让函数卡死,死循环.
            self.root.after(1, self.relay)
            # 具体的更新Ui操作
            self.UpdateUI(content)
        except queue.Empty:
            self.root.after(200, self.relay)

    def UpdateUI(self, content):
        if content == "update_theme_Acrylic":
            self.set_theme("Acrylic")
        elif content == "update_theme_Aero":
            self.set_theme("Aero")
        elif content == "set_task_right_angle":
            self.set_task_radius(0)
        elif content == "set_task_round_angle":
            self.set_task_radius(25)
        elif content == "set_window_top":
            self.set_top(1)
        elif content == "cancel_window_top":
            self.set_top(0)
        elif content == "refresh_tasks":
            self.tasks.refresh_tasks()
        elif content == "show_all_tasks":
            self.tasks.show_all()
        elif content == "del_all":
            self.tasks.del_all()

        elif content == "NewTaskWindow":
            # 打开新建日程
            NewTaskWindow(title="新建日程", height=180, tile_queue=self.tile_queue)

        elif content == "exit":
            self.exit()

        elif content == "update_sqlite":
            self.tasks.update_sqlite_time()

        elif content == "set_tag_name_":
            self.tag_name.set("")

        elif content == "set_data":
            # 获取边框颜色
            self.windows_border_color = "#" + str(hex(self.windows_border))[-1] * 6
            self.canvas.config(highlightbackground=self.windows_border_color)
            self.tasks_border_color = "#" + str(hex(self.tasks_border))[-1] * 6
            # 设置主题
            self.set_theme(tile_theme_name=self.tile_theme_name, remove_=False)
            self.set_background(bg=self.bg)
            self.set_task_radius(self.task_radius, refresh_=False)
            self.set_top(self.tile_top)
            self.update_win_mode(self.win_mode)
            # 任务列表初始化
            self.tasks = Tasks(tile_queue=self.tile_queue, pre_window=self)

        elif content == "set_background":
            self.set_background(bg=self.bg)

        elif content == "EidtTaskWindow":
            for value in self.mydb_dict.itervalues():
                if value[4] == self.tag_name.get():
                    NewTaskWindow(
                        title="修改日程",
                        height=180,
                        tile_queue=self.tile_queue,
                        value=value)
                    return 1
            print("no!" + self.tag_name.get())
            self.tag_name.set("")

        elif content == "DelTaskWindow":
            for value in self.mydb_dict.itervalues():
                if value[4] == self.tag_name.get():
                    self.tasks.del_one(value[0])
                    self.tile_queue.put("refresh_tasks")
                    self.tag_name.set("")

        elif type(content) == tuple:
            if content[0] == "del_one":
                self.tasks.del_one(content[1])
            elif content[0] == "add_one":
                self.tasks.add_one(content[1])
            elif content[0] == "modify_offset":
                self.modify_offset(content[1])
            elif content[0] == "modify_auto_margin":
                self.modify_auto_margin(content[1])
            elif content[0] == "modify_transparent":
                self.modify_transparent(content[1])
            elif content[0] == "update_win_mode":
                self.update_win_mode(content[1])
            elif content[0] == "right_menu":
                self.right_menu(content[1])
            elif content[0] == "set_tag_name":
                self.tag_name.set(content[1])

    def update_win_mode(self, win_mode):
        # 实现代码很简单
        # 关于嵌入桌面的笔记：
        # 1.使用工具winspy（网上自行下载）查看窗口句柄
        # 2.SHELLDLL_DefView是你的桌面窗口类名，它的子窗口是图标窗口，但是默认情况它是在“Progman”窗口下。
        # 3.一旦你点击右下角的桌面按钮，或者使用Win+Tab， Win+D快捷键，你会发现桌面窗口跑到了“WorkerW”窗口下。
        # 4.经过测试发现SHELLDLL_DefView很灵活，如果你把自己的窗口设置为Progman的子窗口，那么SHELLDLL_DefView会自动设置顶层窗口，
        # 自己成为自己的主窗口。而你一旦进行桌面操作，它就自动跑到“WorkerW”窗口下。
        # 5.发现如果设置Progman的子窗口，并不能显示在桌面，只有在“WorkerW”窗口下才可以。
        # 6.另外“WorkerW”窗口默认是没有激活的，只有进行桌面相关操作才会激活（向桌面发送 0x052c）
        # 7.最后发现想要嵌入桌面，一种简单的做法就是直接把你的窗体的父窗口设置成“WorkerW”窗口

        # 网上的blog：
        # 默认的桌面窗口是“SHELLDLL_DefView”，在“Progman”窗口下，你写个程序检测，会发现，点击显示桌面后，这时，激活任意程序窗口，这个特殊状态就消失了，桌面又回到了“Progman”窗口下。
        # 其实系统的显示桌面功能，并不是将桌面上的所有应用程序窗口隐藏或最小化，而是一个特殊的状态，“WorkerW”默认是隐藏，当要显示桌面时，会被显示出来，并且窗口Z次序跑到顶层，
        # 然后将“SHELLDLL_DefView”桌面的父窗口由“Progman”改为“WorkerW”，这时的应用程序可能也是在某种特殊状态下。所以你用IsWindowVisble、IsIconic等函数是检测不出来的，除非点了显示桌面后，又激活了任意某个窗口。
        # 1. 使用win32api.EnumWindows()枚举窗口；
        # 2. 先找到"SHELLDLL_DefView"窗口的父窗口；
        # 3. 再找到该窗口的下一层窗口“WorkerW”;
        # 4. 将我们的窗口设为该“WorkerW”窗口的子窗口即可。

        if win_mode == "独立窗体":
            win32gui.SetParent(self.hwnd, 0)
        else:
            pWnd = win32gui.FindWindow("Progman", "Program Manager")
            win32gui.SendMessage(pWnd, 0x052c, 0, 0)
            win32gui.EnumWindows(self.get_workw_hwnd, 0)
            win32gui.SetParent(self.hwnd, self.hhwnd)

    def get_workw_hwnd(self, hwnd, lParam):
        """遍历找到workw"""
        if win32gui.IsWindowVisible(hwnd):
            hNextWin = win32gui.FindWindowEx(hwnd, None, "SHELLDLL_DefView", None)
            if hNextWin:
                self.hhwnd = hwnd

    def set_theme(self, tile_theme_name, remove_=True):
        """
        更新主题：remove_是否先去除效果
        """
        self.tile_theme_name = tile_theme_name
        if remove_:
            self.window_effect.removeBackgroundEffect(self.hwnd)
        if tile_theme_name == "Acrylic":
            self.window_effect.setAcrylicEffect(self.hwnd, self.tile_transparent)
        else:
            self.window_effect.setAeroEffect(self.hwnd)

    def set_task_radius(self, task_radius, refresh_=True):
        """
        设置是否圆角,refresh_是否刷新列表
        """
        self.task_radius = task_radius

        if refresh_:
            self.tasks.refresh_tasks()

    def set_background(self, bg):
        """设置背景"""
        self.root.configure(bg=bg)
        self.frame_top.configure(bg=bg)
        self.canvas.configure(bg=bg)
        self.canvas.config(highlightbackground=self.windows_border_color)

    def random_color(self):
        """随机颜色"""
        colors1 = '0123456789ABCDEF'
        num = "#"
        for i in range(6):
            num += random.choice(colors1)
        return num

    def set_top(self, flag):
        """
        设置是否置顶
        """
        if flag == 1:
            self.root.wm_attributes('-topmost', 1)
        else:
            self.root.wm_attributes('-topmost', 0)

    '''-----------------------------------耗时操作线程-----------------------------------------------'''

    def initialization(self):
        """
        执行耗时操作（先在布局初始化中设置变量，然后此线程中动态修改）
        """
        # 数据库读取数据
        self.tile_theme_name = self.mysetting_dict['tile_theme_name'][0]
        self.task_radius = self.mysetting_dict['task_radius'][0]
        self.task_geometry = self.mysetting_dict['task_geometry'][0]
        self.tile_top = self.mysetting_dict['tile_top'][0]
        self.tile_transparent = self.mysetting_dict['tile_transparent'][0]
        self.tasks_border = self.mysetting_dict['tasks_border'][0]
        self.windows_border = self.mysetting_dict['windows_border'][0]
        self.win_mode = self.mysetting_dict["win_mode"][0]
        # 数据初始化
        self.tile_queue.put("set_data")
        # 展示所以数据
        self.tile_queue.put("show_all_tasks")

    '''-----------------------------------重写父类方法-----------------------------------------------'''

    def _on_release(self, event, *kw):
        if self.tile_theme_name == "Acrylic":
            self.window_effect.setAcrylicEffect(self.hwnd, self.tile_transparent)
            self.set_background(bg=self.bg)
        super()._on_release(event, mysetting_dict=self.mysetting_dict)

    def _on_tap(self, event):
        if self.tile_theme_name == "Acrylic":
            self.set_background(bg="grey")
            self.window_effect.removeBackgroundEffect(self.hwnd)
        super()._on_tap(event)


class Tasks:
    """任务列表"""

    def __init__(self, tile_queue, pre_window, **kwargs):

        # 传参
        self.pre_window = pre_window
        self.tile_queue = tile_queue
        # 数据初始化
        self.pre_window_root = pre_window.root
        self.exe_dir_path = pre_window.exe_dir_path
        self.canvas = pre_window.canvas
        self.mydb_dict = pre_window.mydb_dict
        self.mysetting_dict = pre_window.mysetting_dict
        self.tasks_border_color = pre_window.tasks_border_color

        # 更新时间
        self.update_sqlite_time()

    def update_sqlite_time(self):
        # 初始化更新时间
        from datetime import datetime
        for key, value in self.mydb_dict.iteritems():
            startdate = datetime.today()
            enddate = datetime.strptime(value[1], '%Y-%m-%d')
            days = str((enddate - startdate).days)
            self.mydb_dict[key] = [value[0], value[1], days, value[3], value[4], value[5]]

    def __get_int_day(self, value):
        """按照时间排序(返回第三个值,时间值)"""
        return int(value[2])

    def __round_rectangle(self, x1, y1, x2, y2, radius=25, **kwargs):
        """画长方形"""
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
        # self.canvas.create_polygon(points, **kwargs, smooth=True, width=1, outline="#080808")
        self.canvas.create_polygon(points, **kwargs, smooth=True, width=1, outline=self.tasks_border_color)

    def __handler(self, fun, **kwds):
        # 实际上是可以直接 lambda： button.bind("<Button-1>", lambda e: handler(e, a=1, b=2, c=3))
        return lambda event, fun=fun, kwds=kwds: fun(event, **kwds)

    def __add_task(self, value):
        """添加每一项任务"""
        self.task_main_text = value[0]
        self.task_time_text = value[1]
        mode = self.mysetting_dict["mode"][0]
        if mode == "普通模式":
            self.task_countdown_text = str(int(value[2]) + 1)
        else:
            self.task_countdown_text = value[2]
        self.task_color = value[3]
        self.task_tag_name = value[4]  # tag是组件的标识符
        self.task_text_color = value[5]
        self.task_text_color = value[5]

        self.__round_rectangle(
            self.task_margin_x,
            self.task_y,
            self.task_margin_x + self.task_width,
            self.task_y + self.task_height,
            radius=self.task_radius,
            fill=self.task_color,
            tag=(self.task_tag_name))

        self.canvas.create_text(
            self.task_margin_x + self.task_width / 25,
            self.task_y + self.task_height / 9,
            text=self.task_main_text,
            font=('microsoft yahei', self.title_scale, 'normal'),
            fill=self.task_text_color,
            anchor="nw",
            justify=LEFT,
            tag=(self.task_tag_name))

        self.canvas.create_text(
            self.task_margin_x + self.task_width / 25,
            self.task_y + self.task_height * 7 / 8,
            text=self.task_time_text,
            font=('Times', self.time_scale, 'normal'),
            fill=self.task_text_color,
            anchor="sw",
            justify=LEFT,
            tag=(self.task_tag_name))

        self.canvas.create_text(
            self.task_margin_x + self.task_width - self.task_width / 20,
            self.task_y + self.task_height / 2,
            text=self.task_countdown_text + "天",
            font=('microsoft yahei', self.count_scale, 'bold'),
            fill=self.task_text_color,
            anchor="e",  # 以右侧为毛点
            justify=RIGHT,
            tag=(self.task_tag_name))

        # 添加绑定函数
        self.canvas.tag_bind(
            self.task_tag_name,
            '<Double-Button-1>',
            func=self.__handler(self.__double_click, task_tag_name=self.task_tag_name))
        self.canvas.tag_bind(
            self.task_tag_name,
            '<Button-3>',
            func=self.__handler(self.__right_click, task_tag_name=self.task_tag_name))
        # self.canvas.unbind('<Button-3>')

    def __right_click(self, event, task_tag_name):
        self.tile_queue.put(("set_tag_name", task_tag_name))

    def __double_click(self, event, task_tag_name):
        for value in self.mydb_dict.itervalues():
            if value[4] == task_tag_name:
                NewTaskWindow(
                    title="修改日程",
                    height=180,
                    tile_queue=self.tile_queue,
                    value=value)
                return 1
        print("no!" + task_tag_name)

    def add_one(self, value):
        self.mydb_dict[value[0]] = value

    def del_one(self, value):
        self.mydb_dict.__delitem__(value)

    def refresh_tasks(self):
        # 画布删除,重新画
        self.canvas.delete("all")
        self.show_all()

    def del_all(self):
        """删除所有数据"""
        self.canvas.delete("all")
        self.tile_queue.put("set_tag_name_")
        for key in self.mydb_dict.iterkeys():
            self.mydb_dict.__delitem__(key)

    def show_all(self):
        """展示所有数据"""
        self.task_radius = self.mysetting_dict["task_radius"][0]
        self.task_geometry = self.mysetting_dict["task_geometry"][0]
        self.tile_geometry = self.mysetting_dict["tile_geometry"][0]
        self.time_scale = self.mysetting_dict["time_scale"][0]
        self.title_scale = self.mysetting_dict["title_scale"][0]
        self.count_scale = self.mysetting_dict["count_scale"][0]
        self.tasks_border = self.mysetting_dict['tasks_border'][0]
        self.windows_border = self.mysetting_dict['windows_border'][0]

        self.windows_border_color = "#" + str(hex(self.windows_border))[-1] * 6
        self.canvas.config(highlightbackground=self.windows_border_color)

        self.tasks_border_color = "#" + str(hex(self.tasks_border))[-1] * 6

        self.task_width = self.task_geometry[0]  # 高度，宽度，是否圆角
        self.task_height = self.task_geometry[1]
        self.task_margin_x = self.task_geometry[2]  # x左右边距，y上下边距
        self.task_margin_y = self.task_geometry[3]

        self.canvas.config(highlightbackground=self.windows_border_color)
        self.tasks_border_color = "#" + str(hex(self.tasks_border))[-1] * 6

        self.canvas.delete("all")

        self.task_y = self.task_margin_y

        # print("数据库中的tile_geometry：", self.tile_geometry)

        # 没有任务项目时的大小
        self.pre_window_root.geometry("%dx%d+%d+%d" % (self.task_width + self.task_margin_x * 2,
                                                       self.task_y + self.task_height + self.task_margin_y,
                                                       self.tile_geometry[2],
                                                       self.tile_geometry[3]))

        # print("没有任务项目时的tile_geometry：", (self.task_width + self.task_margin_x * 2,
        #                                  self.task_y + self.task_height + self.task_margin_y,
        #                                  self.tile_geometry[2],
        #                                  self.tile_geometry[3]))

        for value in sorted(self.mydb_dict.itervalues(), key=self.__get_int_day):
            self.__add_task(value)

            self.task_y = self.task_y + self.task_height + self.task_margin_y  # 更新新添加的高度

            self.pre_window_root.geometry("%dx%d+%d+%d" % (self.task_width + self.task_margin_x * 2,
                                                           self.task_y,
                                                           self.tile_geometry[2],
                                                           self.tile_geometry[3]))
        self.mysetting_dict["tile_geometry"] = [(self.task_width + self.task_margin_x * 2,
                                                self.task_y,
                                                self.tile_geometry[2],
                                                self.tile_geometry[3])]


class NewTaskWindow(CustomWindow):
    """新建日程 or 修改日程"""

    def __init__(self, tile_queue, *args, **kwargs):
        self.root = tk.Toplevel()
        super().__init__(*args, **kwargs)

        # 传递参数
        self.tile_queue = tile_queue

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
        self.task_name_entry = ttk.Entry(entry_spin_frame, validate="focus", validatecommand=self.clear)
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
                self.value = kwargs["value"]

                # 配置参数,初始化
                self.task_name_entry.delete(0, "end")
                self.task_name_entry.insert(0, self.value[0])

                self.date_entry.entry.delete(0, "end")
                self.date_entry.entry.insert(0, self.value[1])

                self.del_task_button = ttk.Button(
                    master=ok_frame,
                    text='删除',
                    style='danger.Outline.TButton',
                    command=self.del_task,
                ).pack(side=tk.LEFT, padx=3)

        # self.root.mainloop()

    def del_task(self):
        """删除一项"""
        self.tile_queue.put(("del_one", self.value[0]))
        self.tile_queue.put("refresh_tasks")
        self.root.destroy()

    def clear(self):
        """点击输入框的回调,删除提示内容"""
        if "创建你的日程" in self.task_name_entry.get():
            self.task_name_entry.delete(0, "end")

    def ok(self):
        """点击确认"""
        if self.modify_flag == 1:
            # 先删除一项,然后再添加一项
            self.tile_queue.put(("del_one", self.value[0]))

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
        self.tile_queue.put(("add_one", value))
        self.tile_queue.put(("refresh_tasks"))

        self.root.destroy()


class AskDelWindow(CustomWindow):
    def __init__(self, tile_queue, *args, **kwargs):
        self.root = tk.Toplevel()
        super().__init__(*args, **kwargs)

        # 传递参数
        self.tile_queue = tile_queue

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

        # self.root.mainloop()

    def cancel(self):
        self.root.destroy()

    def ok(self):
        self.tile_queue.put("del_all")
        self.tile_queue.put("refresh_tasks")
        self.root.destroy()


class AskResetWindow(CustomWindow):
    def __init__(self, main_window_queue, *args, **kwargs):
        self.root = tk.Toplevel()
        super().__init__(*args, **kwargs)

        # 传递参数
        self.main_window_queue = main_window_queue

        # 布局
        self.frame_top = Frame(self.root)
        self.frame_top.pack(side=TOP, padx=20, pady=5, expand=True, fill=X)
        self.frame_bottom = Frame(self.root)
        self.frame_bottom.pack(side=BOTTOM, padx=20, expand=True, fill=X)

        self.lable = ttk.Label(self.frame_top, text="是否要恢复默认（将会自动关闭软件）?")
        self.lable.pack(side=tk.TOP, padx=5, pady=2, expand=True, fill=X)

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

        # self.root.mainloop()

    def cancel(self):
        self.root.destroy()

    def ok(self):
        self.main_window_queue.put("reset")
        self.root.destroy()
        self.main_window_queue.put("exit")


class HelpWindow(CustomWindow):
    def __init__(self, path, *args, **kwargs):
        self.root = tk.Toplevel()
        super().__init__(*args, **kwargs)

        # 传递参数
        self.path = path

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
        self.p.setDaemon(True)
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
            self.HtmlView.set_html(html)


class ScaleFrame(Frame):
    """自定义滑动条"""

    def __init__(self, widget_frame, name, init_value, from_, to, func, **kw):
        super().__init__(master=widget_frame, **kw)

        ttk.Label(master=self, text=name).pack(side=tk.LEFT, fill=tk.X, padx=(0, 2))
        self.scale_var = tk.IntVar(value=init_value)
        ttk.Scale(master=self, variable=self.scale_var, from_=from_, to=to, command=func).pack(side=tk.LEFT, fill=tk.X,
                                                                                               expand=tk.YES,
                                                                                               padx=(0, 2))
        ttk.Entry(self, textvariable=self.scale_var, width=4).pack(side=tk.RIGHT)

    def get_value(self):
        return self.scale_var.get()

    def set_value(self, value):
        self.scale_var.set(value)


class WaitWindow(CustomWindow):
    """自定义等待窗体"""

    def __init__(self, queue, *args, **kwargs):
        self.root = tk.Toplevel()
        super(WaitWindow, self).__init__(*args, **kwargs)

        # 窗体布局1
        self.frame_bottom = Frame(self.root)
        self.frame_bottom.pack(side=BOTTOM, padx=15, pady=10, expand=True, fill=X)
        # 进度条
        self.bar = ttk.Progressbar(self.frame_bottom, mode="indeterminate", orient=tk.HORIZONTAL)
        self.bar.pack(expand=True, fill=X)
        self.bar.start(10)

        # 窗体布局2
        self.frame_top = Frame(self.root)
        self.frame_top.pack(side=TOP, padx=5, pady=10)
        # 提示内容
        self.content_lable = tk.Label(self.frame_top, text="正在初始化,请不要操作，请耐心等待......")
        self.content_lable.pack()

        self.queue = queue  # 子线程与主线程的队列作为中继
        self.root.after(1000, self.relay)

        # root.mainloop()
        # 1.无法在threading中启动mainloop，main_loop方法必须在主线程当中进行。子线程直接操作UI会有很大的隐患。推荐使用队列与主线程交互。
        # 2.另外mainloop()是一个阻塞函数，在外部调用其函数，会阻塞，除非那种一次性的回调（例如按钮的点击事件）
        self.root.mainloop()

    def relay(self):
        """更新UI队列"""
        try:
            # 队列不可阻塞
            content = self.queue.get(False)
            # self.logger.info(self.__class__.__name__ + " Queue接收到消息:" + str(content))
            # 回调函数要在之前回调,因为如果在队列中打开窗体,窗体的 mailoop 会让函数卡死,死循环.
            self.root.after(1, self.relay)
            # 具体的更新Ui操作
            self.UpdateUI(content)
        except queue.Empty:
            self.root.after(200, self.relay)

    def UpdateUI(self, content):
        if content == "exit":
            self.exit()


class UpdateWindow(CustomWindow):
    """检查更新页面"""

    def __init__(self, version, logger, *args, **kwargs):
        self.root = tk.Toplevel()
        super().__init__(*args, **kwargs)

        self.version = version
        self.logger = logger

        self.update_version = version
        self.update_url = ""

        # 布局
        self.frame_top = Frame(self.root)
        self.frame_top.pack(side=TOP, padx=20, pady=5, expand=True, fill=X)
        self.frame_bottom = Frame(self.root)
        self.frame_bottom.pack(side=BOTTOM, padx=20, expand=True, fill=X)

        self.lable = ttk.Label(self.frame_top, text="正在检查更新中......")
        self.lable.pack(side=tk.TOP, padx=5, pady=2, expand=True, fill=X)

        # 开启更新UI队列
        self.queue = Queue()  # 子线程与主线程的队列作为中继
        self.root.after(500, self.relay)

        # 开启请求线程
        self.update_thread = Thread(target=self.update)
        self.update_thread.setDaemon(True)
        self.update_thread.start()

        # self.root.mainloop()

    '''-----------------------------------更新UI 线程-----------------------------------------------'''

    def relay(self):
        """
        更新UI
        """
        while not self.queue.empty():
            content = self.queue.get()
            if content == "需要更新":
                self.lable.config(text="发现新版本：CountBoard V" + self.update_version)

                self.cancel_button = ttk.Button(
                    master=self.frame_bottom,
                    text='取消',
                    bootstyle='outline',
                    command=self.cancel, )
                self.cancel_button.pack(side=tk.RIGHT, fill=tk.X, expand=tk.YES, padx=3)

                self.ok_button = ttk.Button(
                    master=self.frame_bottom,
                    text='更新',
                    bootstyle='outline',
                    command=self.ok, )
                self.ok_button.pack(side=tk.RIGHT, fill=tk.X, expand=tk.YES, padx=3)

            elif content == "不需更新":
                self.lable.config(text="当前已经是最新版本")

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

            elif content == "网络错误":
                self.lable.config(text="当前网络错误（请检查网络，关闭代理）")

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
                    command=self.cancel)
                self.ok_button.pack(side=tk.RIGHT, fill=tk.X, expand=tk.YES, padx=3)

        self.root.after(100, self.relay)

    def ok(self):
        if self.version != self.update_version:
            webbrowser.open_new_tab(self.update_url)
        self.root.destroy()

    def cancel(self):
        self.root.destroy()

    '''-----------------------------------请求线程-----------------------------------------------'''

    def update(self):
        update_path = str(Path(self.exe_dir_path).joinpath("update.txt"))
        try:
            with open(update_path, "wb") as f:
                f.write(requests.get("https://aidcs-1256440297.cos.ap-beijing.myqcloud.com/update.txt").content)
            with open(update_path, "r", encoding='utf8') as f:
                config = f.readline()
            config_dict = json.loads(config)
            self.update_version = config_dict["version"]
            self.update_url = config_dict["url"]
            if self.version != self.update_version:
                self.queue.put("需要更新")
            else:
                self.queue.put("不需更新")
        except:
            self.logger.info(traceback.format_exc())
            self.queue.put("网络错误")


class ResizingCanvas(Canvas):
    """
    自定义缩放画布
    """

    def __init__(self, parent, **kwargs):
        Canvas.__init__(self, parent, **kwargs)
        self.bind("<Configure>", self.on_resize)
        self.height = self.winfo_reqheight()
        self.width = self.winfo_reqwidth()

    def on_resize(self, event):
        wscale = float(event.width) / self.width
        hscale = float(event.height) / self.height
        self.width = event.width
        self.height = event.height
        self.config(width=self.width, height=self.height)
        self.scale("", 0, 0, wscale, hscale)
        # self.scale("all", 0, 0, wscale, hscale)
