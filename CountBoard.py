# -*- coding: UTF-8 -*-
"""
@Project ：CountBoard
@File ：CountBoard.py
@Author ：Gao yongxian
@Date ：2021/11/8 11:00
@contact: g1695698547@163.com
"""
import functools
import logging
import os
import time
from pathlib import Path
import win32api
import win32con
from sqlitedict import SqliteDict
from Tile import *
from CustomWindow import CustomWindow
from SysTrayIcon import SysTrayIcon
from ttkbootstrap import Style
from tkinter import ttk


class MainWindow(CustomWindow, Style):
    """主窗体"""

    def __init__(self, version, icon, logger, exe_dir_path, *args, **kwargs):
        self.root = tk.Tk()
        super().__init__(*args, **kwargs)

        # 传参
        self.version = version
        self.logger = logger
        self.exe_dir_path = exe_dir_path
        self.icon = icon

        # 布局初始化
        self.__init__2()

        # 自定义关闭按钮
        self.root.protocol("WM_DELETE_WINDOW", self.close_)
        self.set_position("center")

        # 开启更新UI队列
        self.queue = Queue()  # 子线程与主线程的队列作为中继
        self.root.after(1000, self.relay)

        # 开启常驻后台线程
        self.backend_thread = Thread(target=self.backend)
        self.backend_thread.setDaemon(True)
        self.backend_thread.start()

        # 开启耗时操作线程
        self.initialization_thread = Thread(target=self.initialization)
        self.initialization_thread.setDaemon(True)
        self.initialization_thread.start()

        self.root.mainloop()

    def __init__2(self):
        """
        布局初始化(必须在主线程进行的操作，比如设置主题，窗口布局,变量初始化)
        """
        # 设置主题,变量初始化
        self.theme_use()
        self.theme_name = tk.StringVar()
        self.tile_theme_name = tk.StringVar()
        self.mode = tk.StringVar()
        self.tile_top = tk.IntVar()
        self.task_radius = tk.IntVar()
        self.reopen_to_backend = tk.IntVar()
        self.auto_run = tk.IntVar()
        self.tile_auto_margin = tk.IntVar()
        self.tile_transparent = tk.IntVar()
        self.tile_auto_margin_length = tk.IntVar()

        # 界面布局
        self.main_frame = ttk.Frame(self.root, style='custom.TFrame', padding=10)
        self.main_frame.pack(side=BOTTOM, fill="both", expand=True)
        self.nb = ttk.Notebook(self.main_frame)
        self.nb.pack(fill=tk.BOTH, expand=tk.YES)
        self.main_tab = self.create_main_tab
        self.nb.add(self.main_tab, text='主页')

        self.control_tab = self.create_control_tab
        self.nb.add(self.control_tab, text='控制')

        self.orhter_tab = self.create_orther_tab
        self.nb.add(self.orhter_tab, text='其他')

        self.about_tab = self.create_about_tab
        self.nb.add(self.about_tab, text='关于')

    '''-----------------------------------更新UI 线程-----------------------------------------------'''

    def relay(self):
        """
        更新UI
        """
        while not self.queue.empty():
            content = self.queue.get()
            if content == "show_wait_window":
                self.wait_window = WaitWindow(width=300, height=80, title="读取数据")

            elif content == "close_wait_window":
                self.wait_window.close()

            elif content == "show_tile":
                self.tile = Tile(
                    title="CountBoardTile",
                    topmost=self.tile_top.get(),
                    bg="#000000",
                    position="custom",
                    overrideredirect=1,
                    theme_name=self.tile_theme_name,
                    exe_dir_path=self.exe_dir_path,
                    mydb_dict=self.mydb_dict,
                    mysetting_dict=self.mysetting_dict,
                    logger=self.logger,
                    _auto_margin=self.tile_auto_margin.get(),
                    offset=self.tile_auto_margin_length.get(),
                    _geometry=self.tile_geometry
                )
            elif content == "judge_reopen_to_backend":
                if self.reopen_to_backend.get() == 1:
                    self.root.withdraw()
            elif content == "change_theme":
                self.change_theme(None)

        self.root.after(100, self.relay)

    '''-----------------------------------耗时操作线程-----------------------------------------------'''

    def initialization(self):
        """
        执行耗时操作，先布局设变量，然后在此线程中动态修改
        """
        self.queue.put("show_wait_window")

        if not os.path.exists(self.exe_dir_path + "/my_setting.sqlite"):
            self.logger.info("第一次运行")
            self.reset()

        # 读取数据库
        self.mydb_dict = SqliteDict(self.exe_dir_path + '/my_db.sqlite', autocommit=True)
        self.mysetting_dict = SqliteDict(self.exe_dir_path + '/my_setting.sqlite', autocommit=True)
        self.logger.info([(x, i) for x, i in self.mysetting_dict.items()])

        self.tile_geometry = self.mysetting_dict["tile_geometry"][0]
        self.task_geometry = self.mysetting_dict["task_geometry"][0]

        self.theme_name.set(self.mysetting_dict["theme_name"][0])
        self.tile_theme_name.set(self.mysetting_dict["tile_theme_name"][0])
        self.mode.set(self.mysetting_dict["mode"][0])
        self.tile_top.set(self.mysetting_dict["tile_top"][0])
        self.task_radius.set(self.mysetting_dict["task_radius"][0])
        self.reopen_to_backend.set(self.mysetting_dict["reopen_to_backend"][0])
        self.auto_run.set(self.mysetting_dict['auto_run'][0])
        self.tile_auto_margin.set(self.mysetting_dict['tile_auto_margin'][0])
        self.tile_auto_margin_length.set(self.mysetting_dict['tile_auto_margin_length'][0])
        self.tile_transparent.set(self.mysetting_dict['tile_transparent'][0])

        self.time_scale.set_value(self.mysetting_dict["time_scale"][0])
        self.title_scale.set_value(self.mysetting_dict["title_scale"][0])
        self.count_scale.set_value(self.mysetting_dict["count_scale"][0])

        self.task_width_scale.set_value(self.task_geometry[0])
        self.task_height_scale.set_value(self.task_geometry[1])
        self.task_margin_x_scale.set_value(self.task_geometry[2])
        self.task_margin_y_scale.set_value(self.task_geometry[3])

        self.queue.put("judge_reopen_to_backend")

        self.queue.put("show_tile")
        # self.queue.put("change_theme")  # 解决因主题改变导致resize控件样式改变
        self.queue.put("close_wait_window")

    def reset(self):
        """
        恢复默认配置或者初始化配置
        """
        mydb_dict = SqliteDict(self.exe_dir_path + '/my_db.sqlite', autocommit=True)
        mysetting_dict = SqliteDict(self.exe_dir_path + '/my_setting.sqlite', autocommit=True)
        mydb_dict.clear()
        mysetting_dict.clear()

        mysetting_dict['tile_theme_name'] = ["Acrylic"]
        mysetting_dict['tile_geometry'] = [(300, 84, 20, 20)]
        mysetting_dict['tile_top'] = [1]
        mysetting_dict['tile_auto_margin'] = [1]
        mysetting_dict['tile_auto_margin_length'] = [3]
        mysetting_dict['tile_transparent'] = [0]

        mysetting_dict['theme_name'] = ["sandstone"]
        mysetting_dict['mode'] = ["普通模式"]
        mysetting_dict['reopen_to_backend'] = [0]
        mysetting_dict['auto_run'] = [0]

        mysetting_dict['task_geometry'] = [(276, 60, 12, 12)]
        mysetting_dict['task_radius'] = [0]
        mysetting_dict['time_scale'] = [8]
        mysetting_dict['title_scale'] = [14]
        mysetting_dict['count_scale'] = [20]

    '''-----------------------------------后台线程-----------------------------------------------'''

    def backend(self, hover_text="CountBoard"):
        """
        后台图标线程
        """
        menu_options = (('主页', None, self.show),)
        self.SysTrayIcon = SysTrayIcon(
            icon=self.icon,  # 图标
            hover_text=hover_text,  # 光标停留显示文字
            menu_options=menu_options,  # 右键菜单
            on_quit=self.exit,  # 退出调用
            tk_window=self.root,  # Tk窗口
        )
        self.SysTrayIcon.activation()

    def close_(self):
        """
        重写关闭按钮
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
        self.logger.info("后台退出")
        self.root.destroy()

    '''-----------------------------------主页页面-----------------------------------------------'''

    @property
    def create_main_tab(self):
        """
        主页页面布局
        """
        tab = ttk.Frame(self.nb, padding=10)

        # 布局1
        widget_frame1 = ttk.LabelFrame(
            master=tab,
            text='主要功能',
            padding=10
        )
        widget_frame1.pack(fill=tk.X, pady=8)
        self.__button_frame(widget_frame1)

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

    def __button_frame(self, widget_frame):
        """主要功能按钮"""
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

        b4 = ttk.Button(
            btn_frame,
            text='检查更新',
            bootstyle='outline',
            command=self.set_update)
        b4.pack(side=tk.LEFT, fill=tk.X, expand=tk.YES, padx=(0, 5))

        b5 = ttk.Button(
            btn_frame,
            text='恢复默认',
            bootstyle='outline',
            command=self.set_reset)
        b5.pack(side=tk.LEFT, fill=tk.X, expand=tk.YES, padx=(0, 5))

        btn_frame.pack(fill=tk.X, pady=5)

    def set_update(self):
        """
        检查更新
        """
        UpdateWindow(title="检查更新", height=100, per_window=self, version=self.version)

    def set_reset(self):
        """
        恢复默认
        """
        AskResetWindow(title="恢复默认", pre_window=self, height=150)

    def del_all(self):
        """
        删除所有
        """
        AskDelWindow(title="删除全部", pre_window=self.tile, height=150)

    def help(self, **kwargs):
        """
        使用说明
        """
        HelpWindow(title='使用说明', width=1000, height=600, path=self.exe_dir_path + "/README.md")

    def create_task(self):
        """
        新建日程
        """
        NewTaskWindow(pre_window=self.tile, title="新建日程", height=180)

    def change_mode(self, event):
        """
        修改计时模式
        """
        self.mysetting_dict["mode"] = [self.mode.get()]
        self.tile.queue.put("refresh_tasks")

    def change_title_theme(self, event):
        """
        修改磁贴的主题
        """
        if self.tile_theme_name.get() == "Acrylic":
            self.tile.queue.put("update_theme_Acrylic")
        else:
            self.tile.queue.put("update_theme_Aero")
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
        # # 因为会重置TSizegrip，所以要重新设置
        # style = ttk.Style()
        # style.configure('myname.TSizegrip', background="black")
        # self.tile.sizegrip.config(style='myname.TSizegrip')
        self.mysetting_dict["theme_name"] = [new_theme]

    '''-----------------------------------其他页面-----------------------------------------------'''

    @property
    def create_orther_tab(self):
        """
        其他页面布局
        """
        tab = ttk.Frame(self.nb, padding=10)

        # 布局1
        widget_frame = ttk.LabelFrame(
            master=tab,
            text='其他设置',
            padding=10
        )
        widget_frame.pack(fill=tk.X, pady=15)

        ttk.Checkbutton(widget_frame, text='是否允许开机自启', variable=self.auto_run,
                        command=self.set_auto_run).pack(side=tk.TOP, fill=tk.X, expand=tk.YES, pady=5)

        ttk.Checkbutton(widget_frame, text='是否开启磁贴的置顶功能', variable=self.tile_top,
                        command=self.set_tile_top).pack(side=tk.TOP, fill=tk.X, expand=tk.YES, pady=5)

        ttk.Checkbutton(widget_frame, text='是否开启磁贴的圆角功能', variable=self.task_radius, onvalue=25, offvalue=0,
                        command=self.set_task_radius).pack(side=tk.TOP, fill=tk.X, expand=tk.YES, pady=5)

        ttk.Checkbutton(widget_frame, text='是否打开软件直接进入后台（自动关闭主页）', variable=self.reopen_to_backend,
                        command=self.set_reopen_to_backend).pack(side=tk.TOP, fill=tk.X, expand=tk.YES, pady=5)

        widget_frame3 = ttk.LabelFrame(
            master=tab,
            text='Acrylic设置',
            padding=10
        )
        widget_frame3.pack(fill=tk.X, pady=5)

        ttk.Checkbutton(widget_frame3, text='是否开启全透明效果（仅Acrylic）', variable=self.tile_transparent,
                        command=self.set_tile_transparent).pack(side=tk.TOP, fill=tk.X, expand=tk.YES, pady=5)

        widget_frame2 = ttk.LabelFrame(
            master=tab,
            text='贴边设置',
            padding=10
        )
        widget_frame2.pack(fill=tk.X, pady=15)

        ttk.Checkbutton(widget_frame2, text='是否开启磁贴的自动贴边功能', variable=self.tile_auto_margin,
                        command=self.set_tile_auto_margin).pack(side=tk.TOP, fill=tk.X, expand=tk.YES, pady=5)
        ttk.Label(master=widget_frame2, text='贴边边距：').pack(side=tk.LEFT)
        ttk.Spinbox(master=widget_frame2, values=[i for i in range(20)],
                    textvariable=self.tile_auto_margin_length).pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=tk.YES,
                                                                    pady=5)
        ttk.Button(master=widget_frame2, text='更改', bootstyle='outline', command=self.set_auto_margin_length).pack(
            side=tk.LEFT, padx=10)

        return tab

    def set_tile_transparent(self):
        """设置全透明"""
        self.mysetting_dict["tile_transparent"] = [self.tile_transparent.get()]

        self.tile.modify_transparent(self.tile_transparent.get())

    def set_auto_margin_length(self):
        """设置贴边大小"""
        self.mysetting_dict["tile_auto_margin_length"] = [self.tile_auto_margin_length.get()]

        self.tile.modify_offset(self.tile_auto_margin_length.get())

    def set_auto_run(self):
        """是否开启软件自启"""
        self.mysetting_dict["auto_run"] = [self.auto_run.get()]

        name = 'CountBoard'  # 要添加的项值名称
        path = str(Path(self.exe_dir_path).joinpath("CountBoard.exe"))  # 要添加的exe路径
        # KeyName = "SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run"  # 注册表项名
        # key = win32api.RegOpenKey(win32con.HKEY_LOCAL_MACHINE, KeyName, 0, win32con.KEY_ALL_ACCESS)

        KeyName = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"  # 注册表项名
        key = win32api.RegOpenKey(win32con.HKEY_CURRENT_USER, KeyName, 0, win32con.KEY_ALL_ACCESS)

        if self.auto_run.get():
            win32api.RegSetValueEx(key, name, 0, win32con.REG_SZ, path)
            print('开启软件自启动')
            print(win32api.RegQueryValueEx(key, name))
        else:
            # 偷懒了，不想修改注册表直接删除了事
            win32api.RegDeleteValue(key, name)
            print('关闭软件自启动')
        win32api.RegCloseKey(key)

    # @property
    # def is_admin(self):
    #     try:
    #         return ctypes.windll.shell32.IsUserAnAdmin()
    #     except:
    #         return False
    #
    # def set_auto_run(self):
    #     """是否开启软件自启"""
    #     self.mysetting_dict["auto_run"] = [self.auto_run.get()]
    #     name = 'CountBoard'  # 要添加的项值名称
    #     path = str(Path(self.exe_dir_path).joinpath("CountBoard.exe"))  # 要添加的exe路径
    #     cmd_reg = \
    #         "reg add HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Run /v %s /t REG_SZ /d %s /f" % (
    #             name, path)
    #     cmd_del_reg = \
    #         "REG DELETE HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Run /v %s" % (
    #             name)
    #
    #     if self.is_admin:
    #         # 将要运行的代码加到这里
    #         if self.auto_run.get() == 1:
    #             os.system(cmd_reg)
    #             print('开启软件自启动')
    #         else:
    #             # 偷懒了，不想修改注册表直接删除了事
    #             os.system(cmd_del_reg)
    #             print('关闭软件自启动')
    #     else:
    #         # 将要运行的代码加到这里
    #         if self.auto_run.get() == 1:
    #             ctypes.windll.shell32.ShellExecuteW(None, "runas", "cmd.exe", "/C %s" % cmd_reg, None, 1)
    #             print('开启软件自启动')
    #         else:
    #             # 偷懒了，不想修改注册表直接删除了事
    #             ctypes.windll.shell32.ShellExecuteW(None, "runas", "cmd.exe", "/C %s" % cmd_del_reg, None, 1)
    #             print('关闭软件自启动')

    def set_tile_auto_margin(self):
        """是否开启自动贴边"""
        self.mysetting_dict["tile_auto_margin"] = [self.tile_auto_margin.get()]

        self.tile.modify_auto_margin(self.tile_auto_margin.get())

    def set_tile_top(self):
        """是否开启磁贴的置顶功能"""
        self.mysetting_dict["tile_top"] = [self.tile_top.get()]

        if self.tile_top.get() == 1:
            self.tile.queue.put("set_window_top")
        else:
            self.tile.queue.put("cancel_window_top")

    def set_task_radius(self):
        """是否开启磁贴的圆角功能"""
        self.mysetting_dict["task_radius"] = [self.task_radius.get()]

        if self.task_radius.get() == 0:
            self.tile.queue.put("set_task_right_angle")
        else:
            self.tile.queue.put("set_task_round_angle")

    def set_reopen_to_backend(self):
        """是否打开软件直接进入后台"""
        self.mysetting_dict["reopen_to_backend"] = [self.reopen_to_backend.get()]

    '''-----------------------------------关于页面-----------------------------------------------'''

    @property
    def create_about_tab(self):
        """
        关于页面布局
        """
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

        # 分割
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
            text='当前版本：CountBoard V' + self.version
        ).pack(side=tk.TOP, fill=tk.X)

        # 分割
        ttk.Separator(
            master=widget_frame4,
            orient=tk.HORIZONTAL
        ).pack(fill=tk.X, pady=(10, 15))

        ttk.Label(
            master=widget_frame4,
            text='国内仓库：https://gitee.com/gao_yongxian/CountBoard'
        ).pack(side=tk.TOP, fill=tk.X)

        ttk.Label(
            master=widget_frame4,
            text='项目地址：https://github.com/Gaoyongxian666/CountBoard'
        ).pack(side=tk.TOP, fill=tk.X)

        return tab

    '''-----------------------------------控制页面-----------------------------------------------'''

    @property
    def create_control_tab(self):
        """
        控制页面布局
        """
        tab = ttk.Frame(self.nb, padding=10)

        # 布局1
        widget_frame = ttk.LabelFrame(
            master=tab,
            text='位置大小',
            padding=10
        )
        widget_frame.pack(fill=tk.X, pady=15)

        self.task_width_scale = ScaleFrame(widget_frame, "日程宽度", 200, 200, 320, self.control_task_width)
        self.task_height_scale = ScaleFrame(widget_frame, "日程高度", 40, 40, 80, self.control_task_height)
        self.task_margin_x_scale = ScaleFrame(widget_frame, "左右边距", 1, 1, 20, self.control_task_margin_x)
        self.task_margin_y_scale = ScaleFrame(widget_frame, "上下边距", 1, 1, 20, self.control_task_margin_y)

        self.task_height_scale.pack(side=tk.TOP, fill=tk.X, expand=tk.YES, pady=5)
        self.task_width_scale.pack(side=tk.TOP, fill=tk.X, expand=tk.YES, pady=5)
        self.task_margin_x_scale.pack(side=tk.TOP, fill=tk.X, expand=tk.YES, pady=5)
        self.task_margin_y_scale.pack(side=tk.TOP, fill=tk.X, expand=tk.YES, pady=5)

        # 布局2
        widget_frame2 = ttk.LabelFrame(
            master=tab,
            text='字号设置',
            padding=10
        )
        widget_frame2.pack(fill=tk.X, pady=5)

        self.title_scale = ScaleFrame(widget_frame2, "标题", 1, 1, 20, self.control_title)
        self.time_scale = ScaleFrame(widget_frame2, "时间", 1, 1, 20, self.control_time)
        self.count_scale = ScaleFrame(widget_frame2, "计数", 1, 1, 30, self.control_count)

        self.title_scale.pack(side=tk.TOP, fill=tk.X, expand=tk.YES, pady=5)
        self.time_scale.pack(side=tk.TOP, fill=tk.X, expand=tk.YES, pady=5)
        self.count_scale.pack(side=tk.TOP, fill=tk.X, expand=tk.YES, pady=5)

        return tab

    def control_title(self, event):
        """
        控制任务的字号
        """
        self.mysetting_dict["title_scale"] = [self.title_scale.get_value()]
        self.tile.tasks.refresh_tasks()

    def control_time(self, event):
        """
        控制任务的字号
        """
        self.mysetting_dict["time_scale"] = [self.time_scale.get_value()]
        self.tile.tasks.refresh_tasks()

    def control_count(self, event):
        """
        控制任务的字号
        """
        self.mysetting_dict["count_scale"] = [self.count_scale.get_value()]
        self.tile.tasks.refresh_tasks()

    def control_task_width(self, event):
        """
        控制任务的宽度
        """
        self.mysetting_dict["task_geometry"] = \
            [(self.task_width_scale.get_value(), self.mysetting_dict["task_geometry"][0][1],
              self.mysetting_dict["task_geometry"][0][2], self.mysetting_dict["task_geometry"][0][3])]

        self.tile.tasks.refresh_tasks()

    def control_task_height(self, event):
        """
        控制任务的高度
        """
        self.mysetting_dict["task_geometry"] = \
            [(self.mysetting_dict["task_geometry"][0][0], self.task_height_scale.get_value(),
              self.mysetting_dict["task_geometry"][0][2], self.mysetting_dict["task_geometry"][0][3])]

        self.tile.tasks.refresh_tasks()

    def control_task_margin_x(self, event):
        """
        控制任务的左右边距
        """
        self.mysetting_dict["task_geometry"] = \
            [(self.mysetting_dict["task_geometry"][0][0], self.mysetting_dict["task_geometry"][0][1],
              self.task_margin_x_scale.get_value(), self.mysetting_dict["task_geometry"][0][3])]

        self.tile.tasks.refresh_tasks()

    def control_task_margin_y(self, event):
        """
        控制任务的上下边距
        """
        self.mysetting_dict["task_geometry"] = \
            [(self.mysetting_dict["task_geometry"][0][0], self.mysetting_dict["task_geometry"][0][1],
              self.mysetting_dict["task_geometry"][0][2], self.task_margin_y_scale.get_value())]

        self.tile.tasks.refresh_tasks()


def just_one_instance(func):
    """
    保证只能运行一个Python实例，方法是程序运行时监听一个特定端口，如果失败则说明已经有实例在跑。
    """

    @functools.wraps(func)
    def f(*args, **kwargs):
        import socket
        try:
            # 全局属性，否则变量会在方法退出后被销毁
            global s
            s = socket.socket()
            host = socket.gethostname()
            s.bind((host, 60123))
        except:

            print('程序已经在运行了')

            return None
        return func(*args, **kwargs)

    return f


@just_one_instance
def main():
    # pathlib可以根据平台自动转换斜杠，不过返回的不是str，还需要转化
    # exe_dir_path=str(Path(sys.argv[0]).parent)

    exe_dir_path = os.path.dirname(sys.argv[0])
    print(exe_dir_path)

    os.environ['REQUESTS_CA_BUNDLE'] = os.path.join(exe_dir_path, 'cacert.pem')
    print(os.environ['REQUESTS_CA_BUNDLE'] )

    # 创建logs文件夹
    if not os.path.exists(exe_dir_path + r"/logs/"):
        os.mkdir(exe_dir_path + r"/logs/")

    logger = logging.getLogger()  # 开启日志记录:创建一个logger
    logger.setLevel(logging.INFO)  # Log等级总开关
    formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")  # 日志格式
    # 创建一个handler，用于写入日志文件
    fh = logging.FileHandler(
        exe_dir_path + '/logs/' + time.strftime('%Y%m%d%H%M', time.localtime(time.time())) + '.log', mode='w',encoding="utf8")
    fh.setLevel(logging.INFO)  # 输出到file的log等级的开关
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    # 创建一个handler，用于写入控制台
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)  # 输出到console的log等级的开关
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # 打开主窗口
    try:
        MainWindow(
            title="CountBoard",
            icon=str(Path(exe_dir_path).joinpath("favicon.ico")),
            topmost=1,
            width=499,
            height=466,
            version="1.2",
            logger=logger,
            exe_dir_path=exe_dir_path)
    except:
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    main()

# -w不带控制行
# 用户名带空格-->用引号 C:\Users\Gao yongxian\PycharmProjects\CountBoard
# pyinstaller -F -i "C:\Users\Gao yongxian\PycharmProjects\CountBoard\favicon.ico" "C:\Users\Gao yongxian\PycharmProjects\CountBoard\CountBoard.py" -w
# pyinstaller -F -i "C:\Users\Gao yongxian\PycharmProjects\CountBoard\favicon.ico" "C:\Users\Gao yongxian\PycharmProjects\CountBoard\CountBoard.py"
