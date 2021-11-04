# -*- coding: UTF-8 -*-
"""
@Project ：CountBoard
@File ：Main_window.py
@Author ：Gao yongxian
@Date ：2021/11/2 14:00
@contact: g1695698547@163.com
"""
import os
import sys
import tkinter as tk
from queue import Queue
from threading import Thread
from tkinter import  BOTTOM, TOP, X
from tkinter.ttk import Frame
from sqlitedict import SqliteDict
from CountBoard import CountBoard, Help_window, Ask_del_window, Newtask_window
from SysTrayIcon import SysTrayIcon
from ttkbootstrap import Style
from tkinter import ttk


class Wait_window(object):
    def __init__(self, pre_window, width, height, position, title, content, icon='favicon.ico'):
        # 读参
        self.pre_window = pre_window
        self.width = width
        self.height = height
        self.position = position
        self.title = title
        self.content = content
        self.icon = icon

        # 初始化
        self.root = tk.Toplevel()
        self.root.title(self.title)
        self.root.iconbitmap(self, icon)
        self.root.wm_attributes('-topmost', 1)
        self.set_position(self.position, self.pre_window)

        # 布局
        self.frame_bottom = Frame(self.root)
        self.frame_bottom.pack(side=BOTTOM, padx=15, pady=10, expand=True, fill=X)
        self.frame_top = Frame(self.root)
        self.frame_top.pack(side=TOP, padx=5, pady=10)

        # 进度条
        self.bar = ttk.Progressbar(self.frame_bottom, mode="indeterminate", orient=tk.HORIZONTAL)
        self.bar.pack(expand=True, fill=X)
        self.bar.start(10)

        # 提示内容
        self.content_lable = tk.Label(self.frame_top, text=self.content)
        self.content_lable.pack()

        # 无法使用threading启动mainloop，main_loop方法必须在主线程当中进行。
        # 子线程直接操作UI会有很大的隐患。推荐使用队列与主线程交互
        # 另外mainloop()是一个阻塞函数，无法在外部调用其函数
        # self.root.mainloop()

    def set_position(self, position, pre_window):
        if position == "center":
            # 中心位置
            win_width = self.root.winfo_screenwidth()
            win_higth = self.root.winfo_screenheight()
            width_adjust = (win_width - self.width) / 2
            higth_adjust = (win_higth - self.height) / 2
            self.root.geometry("%dx%d-%d-%d" % (self.width, self.height, width_adjust, higth_adjust))
        elif position == "follow":
            # 跟随上一个窗体,在上一个窗体正下方，且宽度一致
            self.pre_window_root = pre_window.root
            self.width = pre_window.width
            self.pre_window_root_x, self.pre_window_root_y, self.pre_window_root_w, self.pre_window_root_h = \
                self.pre_window_root.winfo_x(), \
                self.pre_window_root.winfo_y(), \
                self.pre_window_root.winfo_width(), \
                self.pre_window_root.winfo_height()
            self.width_adjust = self.pre_window_root_x
            self.height_adjust = self.pre_window_root_y + self.pre_window_root_h + 40
            self.root.geometry("%dx%d+%d+%d" % (self.width, self.height, self.width_adjust, self.height_adjust))

    def close(self):
        self.root.destroy()


class Main_window(Style):
    """主窗体"""

    def __init__(self, title, icon, alpha, topmost, width, height):
        super().__init__()
        # 传参
        self.title = title
        self.icon = icon
        self.alphe = alpha
        self.topmost = topmost
        self.width = width
        self.height = height

        # 窗口初始化
        self.root = self.master
        self.root.title(title)
        self.root.iconbitmap(icon)
        self.root.wm_attributes('-topmost', 1)
        self.queue = Queue()  # 子线程与主线程的队列作为中继
        self.root.after(1000, self.relay)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.set_position("center", None)

        # 其他初始化
        self.__init__2()

        # 开启常驻后台线程
        self.backend_thread = Thread(target=self.backend)
        self.backend_thread.setDaemon(True)
        self.backend_thread.start()

        # 开启耗时操作线程
        self.initialization_thread = Thread(target=self.initialization)
        self.initialization_thread.setDaemon(True)
        self.initialization_thread.start()

        self.root.mainloop()

    def initialization(self):
        """
        执行耗时操作，先设置默认变量，然后线程中动态修改
        """
        self.queue.put("show_wait_window")

        self.exe_dir_path = os.path.dirname(sys.argv[0])
        if not os.path.exists(self.exe_dir_path + "/my_setting.sqlite"):
            print("第一次运行")
            self.reset()

        self.mydb_dict = SqliteDict(self.exe_dir_path + '/my_db.sqlite', autocommit=True)
        self.mysetting_dict = SqliteDict(self.exe_dir_path + '/my_setting.sqlite', autocommit=True)
        # print([(x, i) for x, i in self.mysetting_dict.items()])

        self.tile_position = self.mysetting_dict["tile_position"][0]
        self.theme_name.set(self.mysetting_dict["theme_name"][0])
        self.tile_theme_name.set(self.mysetting_dict["tile_theme_name"][0])
        self.mode.set(self.mysetting_dict["mode"][0])
        self.tile_top.set(self.mysetting_dict["tile_top"][0])
        self.task_radius.set(self.mysetting_dict["task_radius"][0])
        self.reopen_to_backend.set(self.mysetting_dict["reopen_to_backend"][0])
        self.tile_sizegrip.set(self.mysetting_dict['tile_sizegrip'][0])

        self.queue.put("judge_reopen_to_backend")
        self.queue.put("show_countboard")
        self.queue.put("change_theme")
        self.queue.put("close_wait_window")

    def reset(self):
        """
        恢复默认配置
        """
        mydb_dict = SqliteDict(self.exe_dir_path + '/my_db.sqlite', autocommit=True)
        mysetting_dict = SqliteDict(self.exe_dir_path + '/my_setting.sqlite', autocommit=True)
        mydb_dict.clear()
        mysetting_dict.clear()
        mysetting_dict['theme_name'] = ["sandstone"]
        mysetting_dict['tile_theme_name'] = ["Acrylic"]
        mysetting_dict['tile_position'] = [(300, 100, -20, +20)]
        mysetting_dict['tile_top'] = [1]
        mysetting_dict['tile_sizegrip'] = [1]
        mysetting_dict['mode'] = ["普通模式"]
        mysetting_dict['task_radius'] = [0]
        mysetting_dict['reopen_to_backend'] = [0]

    def __init__2(self):
        """
        其他初始化(必须在主线程进行的操作，比如设置主题)
        """
        # 设置主题
        self.theme_use()
        self.theme_name = tk.StringVar()
        self.tile_theme_name = tk.StringVar()
        self.mode = tk.StringVar()
        self.tile_top = tk.IntVar()
        self.task_radius = tk.IntVar()
        self.reopen_to_backend = tk.IntVar()
        self.tile_sizegrip = tk.IntVar()

        # 界面布局
        self.main_frame = ttk.Frame(self.root, style='custom.TFrame', padding=10)
        self.main_frame.pack(side=BOTTOM, fill="both", expand=True)
        self.nb = ttk.Notebook(self.main_frame)
        self.nb.pack(fill=tk.BOTH, expand=tk.YES)
        self.main_tab = self.create_main_tab
        self.nb.add(self.main_tab, text='主页')
        self.orhter_tab = self.create_orther_tab()
        self.nb.add(self.orhter_tab, text='其他')
        self.about_tab = self.create_about_tab()
        self.nb.add(self.about_tab, text='关于')

    def set_position(self, position, pre_window):
        """
        设置窗体位置
        """
        if position == "center":
            # 中心位置
            win_width = self.root.winfo_screenwidth()
            win_higth = self.root.winfo_screenheight()
            width_adjust = (win_width - self.width) / 2
            higth_adjust = (win_higth - self.height) / 2
            self.root.geometry("%dx%d-%d-%d" % (self.width, self.height, width_adjust, higth_adjust))
        elif position == "follow":
            # 跟随上一个窗体,在上一个窗体正下方，且宽度一致
            self.pre_window_root = pre_window.root
            self.width = pre_window.width
            self.pre_window_root_x, self.pre_window_root_y, self.pre_window_root_w, self.pre_window_root_h = \
                self.pre_window_root.winfo_x(), \
                self.pre_window_root.winfo_y(), \
                self.pre_window_root.winfo_width(), \
                self.pre_window_root.winfo_height()
            self.width_adjust = self.pre_window_root_x
            self.height_adjust = self.pre_window_root_y + self.pre_window_root_h + 40
            self.root.geometry("%dx%d+%d+%d" % (self.width, self.height, self.width_adjust, self.height_adjust))

    def relay(self):
        """
        主线程更新
        """
        while not self.queue.empty():
            content = self.queue.get()
            if content == "show_wait_window":
                self.wait_window = Wait_window(
                    pre_window=self, width=300,
                    height=80,
                    position="center",
                    title="读取数据",
                    content="正在初始化,请不要操作，请耐心等待......")

            elif content == "close_wait_window":
                self.wait_window.close()

            elif content == "show_countboard":
                self.countboard = CountBoard(
                    title="CountBoard",
                    icon="favicon.ico",
                    alpha=1,
                    topmost=self.tile_top.get(),
                    bg="#000000",
                    width=self.tile_position[0],
                    height=self.tile_position[1],
                    width_adjust=self.tile_position[2],
                    higth_adjust=self.tile_position[3],
                    theme_name=self.tile_theme_name,
                    exe_dir_path=self.exe_dir_path,
                    mydb_dict=self.mydb_dict,
                    mysetting_dict=self.mysetting_dict
                )
            elif content == "judge_reopen_to_backend":
                if self.reopen_to_backend.get() == 1:
                    self.root.withdraw()
            elif content == "change_theme":
                self.change_theme(None)

        self.root.after(100, self.relay)

    def del_all(self):
        """
        删除所有task
        """
        Ask_del_window(
            height=150,
            pre_window=self.countboard)

    def help(self, **kwargs):
        """
        打开使用说明
        """
        Help_window(
            width=1000,
            height=600,
            path=self.exe_dir_path + "/README.md")

    def create_task(self):
        """
        新建日程
        """
        # self.nb.select(self.nb.tabs()[2])
        Newtask_window(
            height=180,
            pre_window=self.countboard)

    def backend(self, icon='favicon.ico', hover_text="CountBoard"):
        """
        后台图标线程
        """
        menu_options = (('主页', None, self.show),)
        self.SysTrayIcon = SysTrayIcon(
            icon,  # 图标
            hover_text=hover_text,  # 光标停留显示文字
            menu_options=menu_options,  # 右键菜单
            on_quit=self.exit,  # 退出调用
            tk_window=self.root,  # Tk窗口
        )
        self.SysTrayIcon.activation()

    def close(self):
        """
        重写了关闭按钮
        """
        self.root.withdraw()

    def show(self, _sysTrayIcon=None):
        """
        显示隐藏的窗体
        """
        self.root.deiconify()

    def exit(self, _sysTrayIcon=None):
        """
        全部退出
        """
        print("后台退出")
        self.root.destroy()

    def change_mode(self, event):
        """
        修改计时模式
        """
        self.mysetting_dict["mode"] = [self.mode.get()]
        self.countboard.queue.put("refresh_tasks")

    def change_title_theme(self, event):
        """
        修改磁贴的主题
        """
        if self.tile_theme_name.get() == "Acrylic":
            self.countboard.queue.put("update_theme_Acrylic")
        else:
            self.countboard.queue.put("update_theme_Aero")
        self.mysetting_dict['tile_theme_name'] = [self.tile_theme_name.get()]

    def change_theme(self, event):
        """
        更改界面主题
        """
        self.main_tab.destroy()
        new_theme = self.theme_name.get()
        self.theme_use(new_theme)
        self.main_tab = self.create_main_tab
        self.nb.insert(0, self.main_tab, text='主页')
        self.nb.select(self.nb.tabs()[0])
        self.theme_name.set(new_theme)
        # 因为会重置TSizegrip，所以要重新设置
        style = ttk.Style()
        style.configure('myname.TSizegrip', background="black")
        self.countboard.sizegrip.config(style='myname.TSizegrip')
        self.mysetting_dict["theme_name"] = [new_theme]

    @property
    def create_main_tab(self):
        tab = ttk.Frame(self.nb, padding=10)

        # 布局1
        widget_frame1 = ttk.LabelFrame(
            master=tab,
            text='主要功能',
            padding=10
        )
        widget_frame1.pack(fill=tk.X, pady=8)
        self.button_frame(widget_frame1)

        # 布局2
        widget_frame2 = ttk.LabelFrame(
            master=tab,
            text='计时模式',
            padding=10
        )
        widget_frame2.pack(fill=tk.X, pady=8)
        mode_list = ['普通模式', '紧迫模式']
        mode_cbo = ttk.Combobox(
            widget_frame2,
            values=mode_list,
            state="readonly",
            textvariable=self.mode)
        mode_cbo.pack(fill=tk.X, pady=5)
        mode_cbo.bind("<<ComboboxSelected>>", self.change_mode)

        # 布局3
        widget_frame3 = ttk.LabelFrame(
            master=tab,
            text='磁贴主题',
            padding=10
        )
        widget_frame3.pack(fill=tk.X, pady=8)
        title_theme_list = ['Acrylic', 'Aero']
        title_theme_cbo = ttk.Combobox(
            widget_frame3,
            values=title_theme_list,
            state="readonly",
            textvariable=self.tile_theme_name, )
        title_theme_cbo.pack(fill=tk.X, pady=5)
        title_theme_cbo.bind("<<ComboboxSelected>>", self.change_title_theme)

        # 布局4
        widget_frame4 = ttk.LabelFrame(
            master=tab,
            text='界面主题',
            padding=10
        )
        widget_frame4.pack(fill=tk.X, pady=8)
        themes = [t for t in sorted(self._theme_definitions.keys())]
        themes_cbo = ttk.Combobox(
            widget_frame4,
            values=themes,
            state="readonly",
            textvariable=self.theme_name, )
        themes_cbo.pack(fill=tk.X, pady=5)
        themes_cbo.bind("<<ComboboxSelected>>", self.change_theme)

        return tab

    def create_orther_tab(self):
        """
        其他设置
        """
        tab = ttk.Frame(self.nb, padding=10)

        widget_frame = ttk.LabelFrame(
            master=tab,
            text='其他设置',
            padding=10
        )
        widget_frame.pack(fill=tk.X, pady=15)

        cb2 = ttk.Checkbutton(widget_frame, text='是否开启磁贴的置顶功能', variable=self.tile_top, command=self.set_tile_top)
        cb2.pack(side=tk.TOP, fill=tk.X, expand=tk.YES, pady=5)

        cb3 = ttk.Checkbutton(widget_frame, text='是否开启磁贴的圆角功能', variable=self.task_radius, onvalue=25, offvalue=0,
                              command=self.set_task_radius)
        cb3.pack(side=tk.TOP, fill=tk.X, expand=tk.YES, pady=5)

        cb4 = ttk.Checkbutton(widget_frame, text='是否打开软件直接进入后台（自动关闭主页）', variable=self.reopen_to_backend,
                              command=self.set_reopen_to_backend)
        cb4.pack(side=tk.TOP, fill=tk.X, expand=tk.YES, pady=5)

        cb1 = ttk.Checkbutton(widget_frame, text='是否开启磁贴的控制大小功能（磁贴右下角）', variable=self.tile_sizegrip,
                              command=self.set_tile_sizegrip)
        cb1.pack(side=tk.TOP, fill=tk.X, expand=tk.YES, pady=5)

        return tab

    def set_tile_top(self):
        self.mysetting_dict["tile_top"] = [self.tile_top.get()]
        if self.tile_top.get() == 1:
            self.countboard.queue.put("set_window_top")
        else:
            self.countboard.queue.put("cancel_window_top")

    def set_task_radius(self):
        self.mysetting_dict["task_radius"] = [self.task_radius.get()]
        if self.task_radius.get() == 0:
            self.countboard.queue.put("set_task_right_angle")
        else:
            self.countboard.queue.put("set_task_round_angle")

    def set_reopen_to_backend(self):
        self.mysetting_dict["reopen_to_backend"] = [self.reopen_to_backend.get()]

    def set_tile_sizegrip(self):
        self.mysetting_dict["tile_sizegrip"] = [self.tile_sizegrip.get()]
        if self.tile_sizegrip.get() == 0:
            self.countboard.queue.put("close_sizegrip")
        else:
            self.countboard.queue.put("show_sizegrip")

    def create_about_tab(self):
        tab = ttk.Frame(self.nb, padding=10)
        widget_frame4 = ttk.LabelFrame(
            master=tab,
            text='关于软件',
            padding=10
        )
        widget_frame4.pack(fill=tk.X, pady=15)

        ttk.Label(
            master=widget_frame4,
            text='CountBoard 是一个基于Tkinter开源的桌面日程倒计时应用。'
        ).pack(side=tk.TOP, fill=tk.X)

        ttk.Separator(
            master=widget_frame4,
            orient=tk.HORIZONTAL
        ).pack(fill=tk.X, pady=(10, 15))

        ttk.Label(
            master=widget_frame4,
            text='主题美化：TTkbootstrap'
        ).pack(side=tk.TOP, fill=tk.X)

        ttk.Label(
            master=widget_frame4,
            text='当前版本：CountBoard V1.1'
        ).pack(side=tk.TOP, fill=tk.X)
        ttk.Separator(
            master=widget_frame4,
            orient=tk.HORIZONTAL
        ).pack(fill=tk.X, pady=(10, 15))

        add1 = ttk.Label(
            master=widget_frame4,
            text='项目地址：https://github.com/Gaoyongxian666/CountBoard'
        )
        add1.pack(side=tk.TOP, fill=tk.X)

        add2 = ttk.Label(
            master=widget_frame4,
            text='国内仓库：https://gitee.com/gao_yongxian/CountBoard'
        )
        add2.pack(side=tk.TOP, fill=tk.X)

        # 绑定label单击时间
        add1.bind("<Button-1>", self.open_url1)
        add2.bind("<Button-1>", self.open_url2)

        return tab

    def open_url1(self, event):
        pass
        # webbrowser.open("https://github.com/Gaoyongxian666/CountBoard", new=0)

    def open_url2(self, event):
        pass
        # webbrowser.open("https://gitee.com/gao_yongxian/CountBoard", new=0)


    def button_frame(self, widget_frame):
        btn_frame = ttk.Frame(widget_frame)

        b2 = ttk.Button(
            master=btn_frame,
            text='新建日程',
            bootstyle='outline',
            command=self.create_task)
        b2.pack(side=tk.LEFT, fill=tk.X, expand=tk.YES, padx=(0, 5))

        b3 = ttk.Button(
            master=btn_frame,
            text='删除全部',
            bootstyle='outline',
            command=self.del_all)
        b3.pack(side=tk.LEFT, fill=tk.X, padx=(0, 5), expand=tk.YES)

        b1 = ttk.Button(
            btn_frame,
            text='使用说明',
            bootstyle='outline',
            command=self.help)
        b1.pack(side=tk.LEFT, fill=tk.X, expand=tk.YES, padx=(0, 5))

        btn_frame.pack(fill=tk.X, pady=5)


class Scale_frame:
    def __init__(self, widget_frame, name, init_value, from_, to):
        one_frame = ttk.Frame(widget_frame)
        one_frame.pack(side=tk.TOP, fill=tk.X, expand=tk.YES, pady=5)

        ttk.Label(master=one_frame, text=name).pack(side=tk.LEFT, fill=tk.X, padx=(0, 2))

        self.scale_var = tk.IntVar(value=init_value)
        ttk.Scale(master=one_frame, variable=self.scale_var, from_=from_, to=to).pack(side=tk.LEFT, fill=tk.X,
                                                                                      expand=tk.YES, padx=(0, 2))
        ttk.Entry(one_frame, textvariable=self.scale_var, width=2).pack(side=tk.RIGHT)

    def get_value(self):
        return self.scale_var

    def set_value(self, value):
        self.scale_var.set(value)


if __name__ == "__main__":
    main = Main_window(
        title="CountBoard",
        icon="favicon.ico",
        alpha=1,
        topmost=1,
        width=450,
        height=460)

