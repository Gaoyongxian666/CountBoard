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
import win32api
import win32con
from apscheduler.schedulers.background import BackgroundScheduler
from pywin10 import TaskBarIcon
from sqlitedict import SqliteDict
from Tile import *
from CustomWindow import CustomWindow
import ttkbootstrap as ttk
from ttkbootstrap.style import utility


# from tzlocal import get_localzone


class MainWindow(CustomWindow):
    """主窗体模块"""

    def __init__(self, version, icon, logger, exe_dir_path, first_dict, *args, **kwargs):
        self.root = tk.Tk()

        self.first_dict = first_dict
        if first_dict["scaling_flag"][0]:
            self.root.tk.call('tk', 'scaling', first_dict["scaling"][0] / 100)
        logger.info("默认窗口缩放:" + str(self.root.tk.call('tk', 'scaling')))

        self.style = ttk.Style()
        super().__init__(*args, **kwargs)

        # 布局初始化
        self.__init__2(version, icon, logger, exe_dir_path)

        # 为了使各个窗体独立开来，让其互不干扰，通过队列实现窗体之间的通信。
        self.tile_queue = Queue()
        self.main_window_queue = Queue()
        self.wait_window_queue = Queue()

        # 开启更新UI队列
        self.root.after(1, self.relay)

        # 开启常驻后台线程(系统托盘)
        self.backend_thread = Thread(target=self.backend)
        self.backend_thread.setDaemon(True)
        self.backend_thread.start()

        # 开启耗时操作线程
        self.initialization_thread = Thread(target=self.initialization)
        self.initialization_thread.setDaemon(True)
        self.initialization_thread.start()

        self.root.mainloop()

    '''-----------------------------------布局、基本设置-----------------------------------------------'''

    def __init__2(self, version, icon, logger, exe_dir_path):
        """
        布局初始化(一个窗体基本的设置:比如设置主题，窗口布局,变量初始化(当前不赋值))
        """
        # 传参
        self.version = version
        self.logger = logger
        self.exe_dir_path = exe_dir_path
        self.icon = icon

        # 设置主题
        # utility.enable_high_dpi_awareness()

        # 变量初始化（在耗时线程中赋值）
        self.theme_name = tk.StringVar()
        self.tile_theme_name = tk.StringVar()
        self.mode = tk.StringVar()
        self.win_mode = tk.StringVar()
        self.tile_top = tk.IntVar()
        self.taskbar_icon = tk.IntVar()
        self.task_radius = tk.IntVar()
        self.auto_run = tk.IntVar()
        self.tile_auto_margin = tk.IntVar()
        self.scaling_flag = tk.IntVar()
        self.scaling = tk.IntVar()
        self.tile_transparent = tk.IntVar()
        self.tile_auto_margin_length = tk.IntVar()
        self.regular_notify_flag = tk.IntVar()
        self.regular_notify_h = tk.IntVar()
        self.regular_notify_m = tk.IntVar()
        self.regular_notify_s = tk.IntVar()
        self.regular_notify_title = tk.StringVar()
        self.regular_notify_content = tk.StringVar()
        self.interval_notify_flag = tk.IntVar()
        self.interval_notify_h = tk.IntVar()
        self.interval_notify_m = tk.IntVar()
        self.interval_notify_s = tk.IntVar()
        self.interval_notify_title = tk.StringVar()
        self.interval_notify_content = tk.StringVar()

        # 界面布局
        self.main_frame = ttk.Frame(self.root, style='custom.TFrame', padding=10)
        self.main_frame.pack(side=BOTTOM, fill="both", expand=True)
        self.nb = ttk.Notebook(self.main_frame)
        self.nb.pack(fill=tk.BOTH, expand=tk.YES)
        self.main_tab = self.create_main_tab
        self.nb.add(self.main_tab, text='主页')

        self.control_tab = self.create_control_tab
        self.nb.add(self.control_tab, text='控制')

        self.orhter_tab = self.create_timer_tab
        self.nb.add(self.orhter_tab, text='提醒')

        self.about_tab = self.create_about_tab
        self.nb.add(self.about_tab, text='关于')

        # 自定义关闭按钮
        self.root.protocol("WM_DELETE_WINDOW", self.close_)

        # 大名鼎鼎的apscheduler
        # self.scheduler = BackgroundScheduler(timezone='Asia/Shanghai')
        self.scheduler = BackgroundScheduler(timezone='Asia/Shanghai')
        self.scheduler.add_job(self.refresh_, 'cron', hour=0, minute=0)
        self.scheduler.start()

    def close_(self):
        """重写关闭按钮"""
        self.root.withdraw()

    def show_(self):
        """显示隐藏的窗体"""
        self.root.deiconify()

    def refresh_(self):
        """每天凌晨刷新数据库"""
        self.tile_queue.put("update_sqlite")
        self.tile_queue.put("refresh_tasks")

    '''-----------------------------------更新UI 线程-----------------------------------------------'''

    def relay(self):
        """更新UI队列"""
        try:
            # 队列不可阻塞
            content = self.main_window_queue.get(False)
            self.logger.info(self.__class__.__name__ + " --Queue接收到消息:" + str(content))
            # 回调函数要在之前回调,因为如果在队列中打开窗体,窗体的 mailoop 会让函数卡死,死循环.
            self.root.after(1, self.relay)
            # 具体的更新Ui操作
            self.UpdateUI(content)
        except queue.Empty:
            self.root.after(200, self.relay)

    def UpdateUI(self, content):
        """更新UI的具体操作"""
        if content == "show_wait_window":
            # 打开等待窗体
            WaitWindow(width=300, height=80, title="读取数据", queue=self.wait_window_queue)

        elif content == "close_wait_window":
            # 关闭等待窗体
            self.wait_window_queue.put("exit")

        elif content == "show_tile":
            # 打开磁贴窗体
            Tile(title="CountBoardTile",
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
                 _geometry=self.tile_geometry,
                 tile_queue=self.tile_queue,
                 )

        elif content == "change_theme":
            # 解决因主界面主题改变导致resize控件样式改变的问题
            self.change_theme(None)

        elif content == "UpdateWindow":
            # 打开检查更新窗体
            UpdateWindow(title="检查更新", logger=self.logger, height=100, exe_dir_path=self.exe_dir_path,
                         version=self.version)

        elif content == "AskResetWindow":
            # 打开恢复默认窗体
            AskResetWindow(title="恢复默认", main_window_queue=self.main_window_queue, height=150)

        elif content == "AskDelWindow":
            # 打开删除全部窗体
            AskDelWindow(title="删除全部", height=150, tile_queue=self.tile_queue)

        elif content == "HelpWindow":
            # 打开使用说明窗体
            HelpWindow(title='使用说明', width=1000, height=600, path=self.exe_dir_path + "/introduction.md")

        elif content == "NewTaskWindow":
            # 打开新建日程
            NewTaskWindow(title="新建日程", height=180, tile_queue=self.tile_queue)

        elif content == "reset":
            # 恢复配置
            self.reset()

        elif content == "exit":
            sys.exit(1)

            try:
                self.scheduler.shutdown(True)
                time.sleep(1)
                self.exit()
            except:
                print("ddddddddddddddddddddddd")

            # import win32con
            # self.hwnd = pywintypes.HANDLE(int(self.root.frame(), 16))
            # win32gui.PostMessage(self.hwnd, win32con.WM_CLOSE, 0, 0)
            # print()

        elif content == "show_":
            # 显示窗体
            self.show_()

        elif content == "set_theme":
            # 设置主题
            self.style.theme_use(self.theme_name.get())

        elif content == "set_scaling":
            # 自定义缩放：此选项只能设置之后的缩放，已经绘制的控件无法更改
            # ScaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0)
            # root.tk.call('tk', 'scaling', ScaleFactor / 75)
            self.scaling = self.root.tk.call('tk', 'scaling', 3)
            # print("scaling")

        elif content == "set_regular_notify":
            # 设置主题
            if self.regular_notify_flag.get():
                self.regular_notify_job = self.scheduler.add_job(
                    self.regular_notify_, 'cron',
                    hour=self.regular_notify_h.get(),
                    minute=self.regular_notify_m.get(),
                    second=self.regular_notify_s.get(),
                    max_instances=3)
            else:
                try:
                    self.regular_notify_job.remove()
                except:
                    self.logger.info("没有：self.regular_notify_job.remove()")

        elif content == "set_interval_notify":
            # 设置主题
            if self.interval_notify_flag.get():
                self.interval_notify_job = self.scheduler.add_job(
                    self.interval_notify_, 'interval',
                    hours=self.interval_notify_h.get(),
                    minutes=self.interval_notify_m.get(),
                    seconds=self.interval_notify_s.get(),
                    max_instances=3)
            else:
                try:
                    self.interval_notify_job.remove()
                except:
                    self.logger.info("没有：self.interval_notify_job.remove()")

    def interval_notify_(self):
        self.t.ShowToast(title=self.interval_notify_title.get(), msg=self.interval_notify_content.get())

    def regular_notify_(self):
        self.t.ShowToast(title=self.regular_notify_title.get(), msg=self.regular_notify_content.get())

    '''-----------------------------------耗时操作线程-----------------------------------------------'''

    def initialization(self):
        """执行耗时操作,例如从数据库读取数据(先布局—_init2__设变量，然后在此线程中动态赋值)"""
        # self.main_window_queue.put("show_wait_window")

        # self.main_window_queue.put("set_scaling")

        # 判断是否第一次运行(执行恢复默认操作)
        if not os.path.exists(self.exe_dir_path + "/my_setting.sqlite"):
            self.logger.info("第一次运行")
            self.reset()

        # 读取数据库
        self.mydb_dict = SqliteDict(self.exe_dir_path + '/my_db.sqlite', autocommit=True)
        self.mysetting_dict = SqliteDict(self.exe_dir_path + '/my_setting.sqlite', autocommit=True)
        self.logger.info([(x, i) for x, i in self.mysetting_dict.items()])

        # 其他变量
        # 磁贴位置，传入Tile窗体
        self.tile_geometry = self.mysetting_dict["tile_geometry"][0]
        # 日程条信息，传入控制页面
        self.task_geometry = self.mysetting_dict["task_geometry"][0]
        # 定时提醒信息，传入提醒页面
        self.regular_notify = self.mysetting_dict["regular_notify"][0]
        # 定时提醒信息，传入提醒页面
        self.interval_notify = self.mysetting_dict["interval_notify"][0]

        # 主页变量赋值
        # 模式设置
        self.theme_name.set(self.mysetting_dict["theme_name"][0])
        self.tile_theme_name.set(self.mysetting_dict["tile_theme_name"][0])
        self.mode.set(self.mysetting_dict["mode"][0])
        self.win_mode.set(self.mysetting_dict["win_mode"][0])
        # 其他设置
        self.task_radius.set(self.mysetting_dict["task_radius"][0])
        self.auto_run.set(self.mysetting_dict['auto_run'][0])
        self.tile_top.set(self.mysetting_dict["tile_top"][0])
        self.taskbar_icon.set(self.mysetting_dict["taskbar_icon"][0])
        # 贴边设置
        self.tile_auto_margin.set(self.mysetting_dict['tile_auto_margin'][0])
        self.tile_auto_margin_length.set(self.mysetting_dict['tile_auto_margin_length'][0])
        # Acrylic设置
        self.tile_transparent.set(self.mysetting_dict['tile_transparent'][0])

        # 控制页面的变量赋值
        self.time_scale.set_value(self.mysetting_dict["time_scale"][0])
        self.title_scale.set_value(self.mysetting_dict["title_scale"][0])
        self.count_scale.set_value(self.mysetting_dict["count_scale"][0])
        self.task_width_scale.set_value(self.task_geometry[0])
        self.task_height_scale.set_value(self.task_geometry[1])
        self.task_margin_x_scale.set_value(self.task_geometry[2])
        self.task_margin_y_scale.set_value(self.task_geometry[3])
        self.tasks_border.set_value(self.mysetting_dict["tasks_border"][0])
        self.windows_border.set_value(self.mysetting_dict["windows_border"][0])

        # 提醒页面的变量赋值
        self.regular_notify_flag.set(self.regular_notify["flag"])
        self.regular_notify_h.set(self.regular_notify["h"])
        self.regular_notify_m.set(self.regular_notify["m"])
        self.regular_notify_s.set(self.regular_notify["s"])
        self.regular_notify_title.set(self.regular_notify["title"])
        self.regular_notify_content.set(self.regular_notify["content"])

        self.interval_notify_flag.set(self.interval_notify["flag"])
        self.interval_notify_h.set(self.interval_notify["h"])
        self.interval_notify_m.set(self.interval_notify["m"])
        self.interval_notify_s.set(self.interval_notify["s"])
        self.interval_notify_title.set(self.interval_notify["title"])
        self.interval_notify_content.set(self.interval_notify["content"])

        self.scaling_flag.set(self.first_dict["scaling_flag"][0])
        self.scaling.set(self.first_dict["scaling"][0])

        # self.main_window_queue.put("set_theme")
        # self.queue.put("change_theme")  # 解决因主题改变导致resize控件样式改变

        # 设置主题
        self.main_window_queue.put("set_theme")
        # 打开tile
        self.main_window_queue.put("show_tile")
        # 关闭等待窗体
        # self.main_window_queue.put("close_wait_window")
        self.main_window_queue.put("set_interval_notify")
        self.main_window_queue.put("set_regular_notify")

    def reset(self):
        """恢复默认配置或者初始化配置"""
        mydb_dict = SqliteDict(self.exe_dir_path + '/my_db.sqlite', autocommit=True)
        mysetting_dict = SqliteDict(self.exe_dir_path + '/my_setting.sqlite', autocommit=True)
        mydb_dict.clear()
        mysetting_dict.clear()

        mysetting_dict['tile_theme_name'] = ["Acrylic"]
        mysetting_dict['tile_geometry'] = [(300, 84, 20, 20)]
        mysetting_dict['tile_top'] = [1]
        mysetting_dict['taskbar_icon'] = [1]

        mysetting_dict['tile_auto_margin'] = [1]
        mysetting_dict['tile_auto_margin_length'] = [3]
        mysetting_dict['tile_transparent'] = [0]

        mysetting_dict['theme_name'] = ["sandstone"]
        mysetting_dict['mode'] = ["普通模式"]
        mysetting_dict['win_mode'] = ["独立窗体"]

        mysetting_dict['auto_run'] = [0]

        mysetting_dict['task_geometry'] = [(276, 60, 12, 12)]
        mysetting_dict['task_radius'] = [0]
        mysetting_dict['time_scale'] = [8]
        mysetting_dict['title_scale'] = [14]
        mysetting_dict['count_scale'] = [20]
        mysetting_dict['tasks_border'] = [0]
        mysetting_dict['windows_border'] = [1]

        mysetting_dict['regular_notify'] = [{"flag": 0, "h": 0, "m": 0, "s": 10, "title": "定时标题", "content": "请输入内容"}]
        mysetting_dict['interval_notify'] = [{"flag": 0, "h": 0, "m": 0, "s": 10, "title": "间隔标题", "content": "请输入内容"}]

    '''-----------------------------------托盘图标-----------------------------------------------'''

    def backend(self):
        """后台图标线程"""
        with SqliteDict(self.exe_dir_path + '/my_setting.sqlite') as mydict:  # re-open the same DB
            try:
                taskbar_icon = mydict["taskbar_icon"][0]
            except:
                self.logger.info(traceback.format_exc())
                taskbar_icon = 1

        self.t = TaskBarIcon(
            left_click=self.show__,
            icon=self.icon,
            hover_text=self.title,
            menu_options=[
                ['退出', "exit.ico", self.exit__, 1],  # 菜单项格式:["菜单项名称","菜单项图标路径或None",回调函数或者子菜单列表,id数字(随便写不要重复即可)]

                ["分隔符", None, None, 111],
                ['检查更新', "update.ico", self.update__, 4],
                ['使用说明', "help.ico", self.help__, 3],

                ["分隔符", None, None, 222],
                ['恢复默认', "recovery.ico", self.reset__, 16],
                ['开源地址', "github.ico", self.github__, 42],
                ['主界面', "home.ico", self.show__, 2],

                ["分隔符", None, None, 111],
                ['删除全部', "del.ico", self.delall__, 7],
                ['新建日程', "edit.ico", self.newtask__, 6]
            ],
            menu_style="iconic" if taskbar_icon else "normal",
            icon_x_pad=12
            # 设置右键菜单的模式,可以不设置:normal(不展示图标),iconic(展示图标)
        )
        # 注意这是死循环，类似与tkinter中的mainloop,
        # 因为都是死循环,所以与mainloop会冲突,放到线程里面执行.
        win32gui.PumpMessages()

    def show__(self):
        """显示隐藏的窗体"""
        self.main_window_queue.put("show_")

    def exit__(self):
        """退出"""
        self.logger.info("后台退出")
        win32gui.DestroyWindow(self.t.hwnd)
        self.tile_queue.put("exit")
        self.main_window_queue.put("exit")

    def update__(self):
        """检查更新"""
        self.main_window_queue.put("UpdateWindow")

    def reset__(self):
        """恢复默认"""
        self.main_window_queue.put("AskResetWindow")

    def delall__(self):
        """删除所有"""
        self.main_window_queue.put("AskDelWindow")

    def help__(self, **kwargs):
        """使用说明"""
        self.main_window_queue.put("HelpWindow")

    def newtask__(self):
        """新建日程"""
        self.main_window_queue.put("NewTaskWindow")

    def github__(self):
        webbrowser.open("https://github.com/Gaoyongxian666/CountBoard")

    '''-----------------------------------主页页面-----------------------------------------------'''

    @property
    def create_main_tab(self):
        """主页页面布局"""
        tab = ttk.Frame(self.nb, padding=10)

        lframe = ttk.Frame(tab, padding=5)
        lframe.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.YES)

        rframe = ttk.Frame(tab, padding=5)
        rframe.pack(side=tk.RIGHT, fill=tk.BOTH, expand=tk.YES)

        # 布局1
        widget_frame1 = ttk.LabelFrame(
            master=rframe,
            text='磁贴模式',
            padding=10
        )
        # ttk.Label(widget_frame1, text="建议嵌入桌面模式下开启边框").pack(anchor="nw", )

        widget_frame1.pack(fill=tk.X, pady=8)
        win_mode_list = ['嵌入桌面', '独立窗体']
        mode_cbo2 = ttk.Combobox(
            widget_frame1,
            values=win_mode_list,
            state="readonly",
            textvariable=self.win_mode)
        mode_cbo2.pack(fill=tk.X, pady=5)
        mode_cbo2.bind("<<ComboboxSelected>>", self.change_win_mode)

        # 布局2
        widget_frame2 = ttk.LabelFrame(
            master=rframe,
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
            master=rframe,
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
            master=rframe,
            text='界面主题',
            padding=10
        )
        widget_frame4.pack(fill=tk.X, pady=8)
        themes = [t for t in sorted(self.style.theme_names())]
        themes_cbo = ttk.Combobox(
            widget_frame4,
            values=themes,
            state="readonly",
            textvariable=self.theme_name, )
        themes_cbo.pack(fill=tk.X, pady=5)
        themes_cbo.bind("<<ComboboxSelected>>", self.change_theme)

        # 布局17
        widget_frame17 = ttk.LabelFrame(
            master=rframe,
            text='组件缩放',
            padding=10
        )
        widget_frame17.pack(fill=tk.X, pady=8)

        ttk.Checkbutton(widget_frame17, text='是否开启组件缩放（通常不开启）',
                        variable=self.scaling_flag,
                        bootstyle="square-toggle",
                        command=self.set_scaling_flag).pack(side=tk.TOP, fill=tk.X, expand=tk.YES, pady=5)
        ttk.Label(master=widget_frame17, text='针对2K，4K高分辨率屏幕，需要重启生效').pack(side=tk.TOP, fill=tk.X, expand=tk.YES,
                                                                           pady=5)

        ttk.Label(master=widget_frame17, text='缩放大小：').pack(side=tk.LEFT)
        ttk.Spinbox(master=widget_frame17, values=[i for i in range(100, 300)], width=3,
                    textvariable=self.scaling).pack(side=tk.LEFT, padx=(5, 0),
                                                    # fill=tk.X, expand=tk.YES,
                                                    pady=5)
        ttk.Button(master=widget_frame17, text='更改', bootstyle='outline', command=self.set_scaling).pack(
            side=tk.LEFT, padx=10)

        # 布局11
        widget_frame11 = ttk.LabelFrame(
            master=lframe,
            text='主要功能',
            padding=10
        )
        widget_frame11.pack(fill=tk.X, pady=8)
        self.set_button_frame(widget_frame11)

        # 布局5
        widget_frame5 = ttk.LabelFrame(
            master=lframe,
            text='其他设置',
            padding=10
        )
        widget_frame5.pack(fill=tk.X, pady=8)
        ttk.Checkbutton(widget_frame5, text='是否允许开机自启', variable=self.auto_run, bootstyle="square-toggle",
                        command=self.set_auto_run).pack(side=tk.TOP, fill=tk.X, expand=tk.YES, pady=5)
        ttk.Checkbutton(widget_frame5, text='是否开启磁贴的置顶功能', variable=self.tile_top, bootstyle="square-toggle",
                        command=self.set_tile_top).pack(side=tk.TOP, fill=tk.X, expand=tk.YES, pady=5)
        ttk.Checkbutton(widget_frame5, text='是否开启磁贴的圆角功能', variable=self.task_radius, onvalue=25, offvalue=0,
                        bootstyle="square-toggle",
                        command=self.set_task_radius).pack(side=tk.TOP, fill=tk.X, expand=tk.YES, pady=5)
        ttk.Checkbutton(widget_frame5, text='是否显示右键菜单图标(需要重启生效)', variable=self.taskbar_icon, bootstyle="square-toggle",
                        command=self.set_taskbar_icon).pack(side=tk.TOP, fill=tk.X, expand=tk.YES, pady=5)

        # 布局6
        widget_frame6 = ttk.LabelFrame(
            master=lframe,
            text='Acrylic设置',
            padding=10
        )
        widget_frame6.pack(fill=tk.X, pady=5)

        ttk.Checkbutton(widget_frame6, text='是否开启全透明效果（仅Acrylic）', variable=self.tile_transparent,
                        bootstyle="square-toggle",
                        command=self.set_tile_transparent).pack(side=tk.TOP, fill=tk.X, expand=tk.YES, pady=5)

        # 布局7
        widget_frame7 = ttk.LabelFrame(
            master=lframe,
            text='贴边设置',
            padding=10
        )
        widget_frame7.pack(fill=tk.X, pady=8)

        ttk.Checkbutton(widget_frame7, text='是否开启磁贴的自动贴边功能', variable=self.tile_auto_margin, bootstyle="square-toggle",
                        command=self.set_tile_auto_margin).pack(side=tk.TOP, fill=tk.X, expand=tk.YES, pady=5)
        ttk.Label(master=widget_frame7, text='贴边边距：').pack(side=tk.LEFT)
        ttk.Spinbox(master=widget_frame7, values=[i for i in range(20)], width=3,

                    textvariable=self.tile_auto_margin_length).pack(side=tk.LEFT, padx=(5, 0),
                                                                    # fill=tk.X, expand=tk.YES,
                                                                    pady=5)
        ttk.Button(master=widget_frame7, text='更改', bootstyle='outline', command=self.set_auto_margin_length).pack(
            side=tk.LEFT, padx=10)

        return tab

    def set_button_frame(self, widget_frame):
        """主要功能按钮"""
        top_frame = ttk.Frame(widget_frame)
        top_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.YES, pady=5)
        bottom_frame = ttk.Frame(widget_frame)
        bottom_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.YES, pady=5)

        b2 = ttk.Button(
            master=top_frame,
            text='新建日程',
            bootstyle='outline',
            command=self.newtask__)
        b2.pack(side=tk.LEFT, fill=tk.X, expand=tk.YES, padx=(0, 5))

        b3 = ttk.Button(
            master=top_frame,
            text='删除全部',
            bootstyle='outline',
            command=self.delall__)
        b3.pack(side=tk.LEFT, fill=tk.X, padx=(0, 5), expand=tk.YES)

        b1 = ttk.Button(
            top_frame,
            text='使用说明',
            bootstyle='outline',
            command=self.help__)
        b1.pack(side=tk.LEFT, fill=tk.X, expand=tk.YES, padx=(0, 5))

        b4 = ttk.Button(
            bottom_frame,
            text='检查更新',
            bootstyle='outline',
            command=self.update__)
        b4.pack(side=tk.LEFT, fill=tk.X, expand=tk.YES, padx=(0, 5))

        b5 = ttk.Button(
            bottom_frame,
            text='恢复默认',
            bootstyle='outline',
            command=self.reset__)
        b5.pack(side=tk.LEFT, fill=tk.X, expand=tk.YES, padx=(0, 5))

        b6 = ttk.Button(
            bottom_frame,
            text='开源地址',
            bootstyle='outline',
            command=self.github__)
        b6.pack(side=tk.LEFT, fill=tk.X, expand=tk.YES, padx=(0, 5))

    def set_scaling_flag(self):
        self.first_dict["scaling_flag"] = [self.scaling_flag.get()]

    def set_scaling(self):
        self.first_dict["scaling"] = [self.scaling.get()]

    def change_win_mode(self, event):
        """修改磁贴的模式"""
        self.mysetting_dict["win_mode"] = [self.win_mode.get()]
        self.tile_queue.put(("update_win_mode", self.win_mode.get()))

    def change_mode(self, event):
        """修改计时模式"""
        self.mysetting_dict["mode"] = [self.mode.get()]
        self.tile_queue.put("refresh_tasks")

    def change_title_theme(self, event):
        """修改磁贴的主题"""
        self.mysetting_dict['tile_theme_name'] = [self.tile_theme_name.get()]
        if self.tile_theme_name.get() == "Acrylic":
            self.tile_queue.put("update_theme_Acrylic")
        else:
            self.tile_queue.put("update_theme_Aero")

    def change_theme(self, event):
        """更改界面主题"""
        self.main_tab.destroy()
        new_theme = self.theme_name.get()
        self.mysetting_dict["theme_name"] = [new_theme]
        self.style.theme_use(new_theme)
        self.main_tab = self.create_main_tab
        self.nb.insert(0, self.main_tab, text='主页')
        self.nb.select(self.nb.tabs()[0])
        self.theme_name.set(new_theme)

        # # 因为重置tile，所以要重新设置
        self.tile_queue.put("set_background")

        # # 因为会重置TSizegrip，所以要重新设置
        # style = ttk.Style()
        # style.configure('myname.TSizegrip', background="black")
        # self.tile.sizegrip.config(style='myname.TSizegrip')

    def set_taskbar_icon(self):
        """设置菜单图标"""
        self.mysetting_dict["taskbar_icon"] = [self.taskbar_icon.get()]

    def set_tile_transparent(self):
        """设置全透明"""
        self.mysetting_dict["tile_transparent"] = [self.tile_transparent.get()]
        self.tile_queue.put(("modify_transparent", self.tile_transparent.get()))

    def set_auto_margin_length(self):
        """设置贴边大小"""
        self.mysetting_dict["tile_auto_margin_length"] = [self.tile_auto_margin_length.get()]
        self.tile_queue.put(("modify_offset", self.tile_auto_margin_length.get()))

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
        self.tile_queue.put(("modify_auto_margin", self.tile_auto_margin.get()))

    def set_tile_top(self):
        """是否开启磁贴的置顶功能"""
        self.mysetting_dict["tile_top"] = [self.tile_top.get()]

        if self.tile_top.get() == 1:
            self.tile_queue.put("set_window_top")
        else:
            self.tile_queue.put("cancel_window_top")

    def set_task_radius(self):
        """是否开启磁贴的圆角功能"""
        self.mysetting_dict["task_radius"] = [self.task_radius.get()]

        if self.task_radius.get() == 0:
            self.tile_queue.put("set_task_right_angle")
        else:
            self.tile_queue.put("set_task_round_angle")

    '''-----------------------------------关于页面-----------------------------------------------'''

    @property
    def create_about_tab(self):
        """关于页面布局"""
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

        ttk.Label(
            master=widget_frame4,
            text='更新时间：2021年12月02日'
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

    '''-----------------------------------提醒页面-----------------------------------------------'''

    def set_regular_notify_flag(self):
        """保存regular_notify配置"""
        self.mysetting_dict["regular_notify"] = \
            [{"flag": self.regular_notify_flag.get(),
              "h": self.regular_notify_h.get(),
              "m": self.regular_notify_m.get(),
              "s": self.regular_notify_s.get(),
              "title": self.regular_notify_title.get(),
              "content": self.regular_notify_content.get()}]

        self.main_window_queue.put("set_regular_notify")

    def save_regular_notify(self):
        """保存regular_notify配置"""
        self.mysetting_dict["regular_notify"] = \
            [{"flag": self.regular_notify_flag.get(),
              "h": self.regular_notify_h.get(),
              "m": self.regular_notify_m.get(),
              "s": self.regular_notify_s.get(),
              "title": self.regular_notify_title.get(),
              "content": self.regular_notify_content.get()}]

    def set_interval_notify_flag(self):
        """设置是否开启interval_notify"""
        self.mysetting_dict["interval_notify"] = \
            [{"flag": self.interval_notify_flag.get(),
              "h": self.interval_notify_h.get(),
              "m": self.interval_notify_m.get(),
              "s": self.interval_notify_s.get(),
              "title": self.interval_notify_title.get(),
              "content": self.interval_notify_content.get()}]

        self.main_window_queue.put("set_interval_notify")

    def save_interval_notify(self):
        """设置是否开启interval_notify"""
        self.mysetting_dict["interval_notify"] = \
            [{"flag": self.interval_notify_flag.get(),
              "h": self.interval_notify_h.get(),
              "m": self.interval_notify_m.get(),
              "s": self.interval_notify_s.get(),
              "title": self.interval_notify_title.get(),
              "content": self.interval_notify_content.get()}]

    @property
    def create_timer_tab(self):
        tab = ttk.Frame(self.nb, padding=10)

        '''#####################定时提醒#####################'''
        widget_frame1 = ttk.LabelFrame(
            master=tab,
            text='定时提醒',
            padding=10
        )
        widget_frame1.pack(fill=tk.X, pady=8)
        # （每天固定时间进行提醒）
        ttk.Checkbutton(
            master=widget_frame1,
            text='是否开启定时提醒',
            bootstyle="squared-toggle",
            variable=self.regular_notify_flag,
            command=self.set_regular_notify_flag
        ).pack(fill=tk.X, pady=5)

        middle_frame1 = ttk.Frame(master=widget_frame1)
        middle_frame1.pack(side=tk.TOP, fill=tk.X, pady=9)
        bottom_frame1 = ttk.Frame(master=widget_frame1)
        bottom_frame1.pack(side=tk.TOP, fill=tk.X, pady=9)
        top_frame1 = ttk.Frame(master=widget_frame1)
        top_frame1.pack(side=tk.TOP, fill=tk.X, pady=9)

        ttk.Label(
            master=top_frame1,
            text='时间：'
        ).pack(side=tk.LEFT, padx=(5, 2))
        self.regular_notify_h_spinbox = ttk.Spinbox(
            master=top_frame1, values=[i for i in range(60)],
            width=3,
            textvariable=self.regular_notify_h)
        self.regular_notify_h_spinbox.pack(
            side=tk.LEFT, padx=(5, 0),
        )
        ttk.Label(
            master=top_frame1,
            text='时'
        ).pack(side=tk.LEFT, padx=(5, 2))
        ttk.Spinbox(
            master=top_frame1, values=[i for i in range(60)],
            width=3,
            textvariable=self.regular_notify_m).pack(side=tk.LEFT, padx=(5, 2))
        ttk.Label(
            master=top_frame1,
            text='分'
        ).pack(side=tk.LEFT, padx=(5, 2))
        ttk.Spinbox(
            master=top_frame1, values=[i for i in range(60)],
            width=3,
            textvariable=self.regular_notify_s).pack(
            side=tk.LEFT, padx=(5, 2),
        )
        ttk.Label(
            master=top_frame1,
            text='秒'
        ).pack(side=tk.LEFT, padx=(5, 2))
        ttk.Button(
            master=top_frame1,
            text='保存',
            bootstyle='outline',
            command=self.save_regular_notify).pack(
            side=tk.LEFT, padx=9)

        ttk.Label(
            master=middle_frame1,
            text='标题：'
        ).pack(side=tk.LEFT, padx=(5, 2))
        ttk.Entry(middle_frame1, textvariable=self.regular_notify_title).pack(side=tk.LEFT, fill=tk.X, padx=(5, 2),
                                                                              expand=tk.YES)

        ttk.Label(
            master=bottom_frame1,
            text='内容：'
        ).pack(side=tk.LEFT, padx=(5, 2))
        ttk.Entry(bottom_frame1, textvariable=self.regular_notify_content).pack(side=tk.LEFT, fill=tk.X, padx=(5, 2),
                                                                                expand=tk.YES)

        '''#####################间隔提醒#####################'''
        widget_frame5 = ttk.LabelFrame(
            master=tab,
            text='间隔提醒',
            padding=10
        )
        widget_frame5.pack(fill=tk.X, pady=8)
        # （每隔多少时间进行提醒）
        cb2 = ttk.Checkbutton(
            master=widget_frame5,
            text='是否开启间隔提醒',
            bootstyle="squared-toggle",
            variable=self.interval_notify_flag,
            command=self.set_interval_notify_flag
        )
        cb2.pack(fill=tk.X, pady=5)

        middle_frame = ttk.Frame(master=widget_frame5)
        middle_frame.pack(side=tk.TOP, fill=tk.X, pady=9)
        bottom_frame = ttk.Frame(master=widget_frame5)
        bottom_frame.pack(side=tk.TOP, fill=tk.X, pady=9)
        top_frame = ttk.Frame(master=widget_frame5)
        top_frame.pack(side=tk.TOP, fill=tk.X, pady=9)

        ttk.Label(
            master=top_frame,
            text='时间：'
        ).pack(side=tk.LEFT, padx=(5, 2))
        ttk.Spinbox(
            master=top_frame, values=[i for i in range(60)],
            width=3,
            textvariable=self.interval_notify_h).pack(
            side=tk.LEFT, padx=(5, 0),
        )
        ttk.Label(
            master=top_frame,
            text='时'
        ).pack(side=tk.LEFT, padx=(5, 2))
        ttk.Spinbox(
            master=top_frame, values=[i for i in range(60)],
            width=3,
            textvariable=self.interval_notify_m).pack(side=tk.LEFT, padx=(5, 2))
        ttk.Label(
            master=top_frame,
            text='分'
        ).pack(side=tk.LEFT, padx=(5, 2))
        ttk.Spinbox(
            master=top_frame, values=[i for i in range(60)],
            width=3,
            textvariable=self.interval_notify_s).pack(
            side=tk.LEFT, padx=(5, 2),
        )
        ttk.Label(
            master=top_frame,
            text='秒'
        ).pack(side=tk.LEFT, padx=(5, 2))
        ttk.Button(
            master=top_frame,
            text='保存',
            bootstyle='outline',
            command=self.save_interval_notify).pack(
            side=tk.LEFT, padx=9)

        ttk.Label(
            master=middle_frame,
            text='标题：'
        ).pack(side=tk.LEFT, padx=(5, 2))
        ttk.Entry(middle_frame, textvariable=self.interval_notify_title).pack(side=tk.LEFT, fill=tk.X, padx=(5, 2),
                                                                              expand=tk.YES)

        ttk.Label(
            master=bottom_frame,
            text='内容：'
        ).pack(side=tk.LEFT, padx=(5, 2))
        ttk.Entry(bottom_frame, textvariable=self.interval_notify_content).pack(side=tk.LEFT, fill=tk.X, padx=(5, 2),
                                                                                expand=tk.YES)

        ttk.Label(
            master=tab,
            anchor="w",
            text='注意：修改时间之后需要重新开启提醒才可生效。'
        ).pack(side=tk.TOP, fill=X, padx=(5, 2))
        return tab

    '''-----------------------------------控制页面-----------------------------------------------'''

    @property
    def create_control_tab(self):
        """控制页面布局"""
        tab = ttk.Frame(self.nb, padding=10)

        bottomframe = ttk.Frame(tab, padding=5)
        bottomframe.pack(side=tk.TOP, fill=tk.X, anchor="nw")

        topframe = ttk.Frame(tab)
        topframe.pack(side=tk.TOP, fill=tk.X, expand=tk.YES, anchor="nw")

        top_lframe = ttk.Frame(topframe, padding=5)
        top_lframe.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.YES, anchor="w")

        top_rframe = ttk.Frame(topframe, padding=5)
        top_rframe.pack(side=tk.RIGHT, fill=tk.BOTH, expand=tk.YES, anchor="w")

        # 布局1
        widget_frame = ttk.LabelFrame(
            master=bottomframe,
            text='位置大小',
            padding=10,
        )
        widget_frame.pack(fill=tk.X, pady=8)

        self.task_width_scale = ScaleFrame(widget_frame, "日程宽度", 150, 150, 400, self.control_task_width)
        self.task_height_scale = ScaleFrame(widget_frame, "日程高度", 40, 40, 150, self.control_task_height)
        self.task_margin_x_scale = ScaleFrame(widget_frame, "左右边距", 0, 0, 20, self.control_task_margin_x)
        self.task_margin_y_scale = ScaleFrame(widget_frame, "上下边距", 0, 0, 20, self.control_task_margin_y)

        self.task_height_scale.pack(side=tk.TOP, fill=tk.X, expand=tk.YES, pady=5)
        self.task_width_scale.pack(side=tk.TOP, fill=tk.X, expand=tk.YES, pady=5)
        self.task_margin_x_scale.pack(side=tk.TOP, fill=tk.X, expand=tk.YES, pady=5)
        self.task_margin_y_scale.pack(side=tk.TOP, fill=tk.X, expand=tk.YES, pady=5)

        # 布局2
        widget_frame2 = ttk.LabelFrame(
            master=top_lframe,
            text='字号设置',
            padding=10
        )
        widget_frame2.pack(fill=tk.X, pady=8)

        self.title_scale = ScaleFrame(widget_frame2, "标题", 8, 8, 30, self.control_title)
        self.time_scale = ScaleFrame(widget_frame2, "时间", 8, 8, 30, self.control_time)
        self.count_scale = ScaleFrame(widget_frame2, "计数", 14, 14, 40, self.control_count)

        self.title_scale.pack(side=tk.TOP, fill=tk.X, expand=tk.YES, pady=5)
        self.time_scale.pack(side=tk.TOP, fill=tk.X, expand=tk.YES, pady=5)
        self.count_scale.pack(side=tk.TOP, fill=tk.X, expand=tk.YES, pady=5)

        # 布局3
        widget_frame3 = ttk.LabelFrame(
            master=top_rframe,
            text='边框设置',
            padding=10
        )
        widget_frame3.pack(fill=tk.X, pady=8)

        self.tasks_border = ScaleFrame(widget_frame3, "日程边框", 0, 0, 15, self.control_tasks_border)
        self.windows_border = ScaleFrame(widget_frame3, "窗体边框", 0, 0, 15, self.control_windows_border)

        self.tasks_border.pack(side=tk.TOP, fill=tk.X, expand=tk.YES, pady=5)
        self.windows_border.pack(side=tk.TOP, fill=tk.X, expand=tk.YES, pady=5)

        return tab

    def control_tasks_border(self, event):
        """控制任务的字号"""
        self.mysetting_dict["tasks_border"] = [self.tasks_border.get_value()]
        self.tile_queue.put("refresh_tasks")

    def control_windows_border(self, event):
        """控制任务的字号"""
        self.mysetting_dict["windows_border"] = [self.windows_border.get_value()]
        self.tile_queue.put("refresh_tasks")

    def control_title(self, event):
        """控制任务的字号"""
        self.mysetting_dict["title_scale"] = [self.title_scale.get_value()]
        self.tile_queue.put("refresh_tasks")

    def control_time(self, event):
        """控制任务的字号"""
        self.mysetting_dict["time_scale"] = [self.time_scale.get_value()]
        self.tile_queue.put("refresh_tasks")

    def control_count(self, event):
        """控制任务的字号"""
        self.mysetting_dict["count_scale"] = [self.count_scale.get_value()]
        self.tile_queue.put("refresh_tasks")

    def control_task_width(self, event):
        """控制任务的宽度"""
        self.mysetting_dict["task_geometry"] = \
            [(self.task_width_scale.get_value(), self.mysetting_dict["task_geometry"][0][1],
              self.mysetting_dict["task_geometry"][0][2], self.mysetting_dict["task_geometry"][0][3])]

        self.tile_queue.put("refresh_tasks")

    def control_task_height(self, event):
        """控制任务的高度"""
        self.mysetting_dict["task_geometry"] = \
            [(self.mysetting_dict["task_geometry"][0][0], self.task_height_scale.get_value(),
              self.mysetting_dict["task_geometry"][0][2], self.mysetting_dict["task_geometry"][0][3])]

        self.tile_queue.put("refresh_tasks")

    def control_task_margin_x(self, event):
        """控制任务的左右边距"""
        self.mysetting_dict["task_geometry"] = \
            [(self.mysetting_dict["task_geometry"][0][0], self.mysetting_dict["task_geometry"][0][1],
              self.task_margin_x_scale.get_value(), self.mysetting_dict["task_geometry"][0][3])]

        self.tile_queue.put("refresh_tasks")

    def control_task_margin_y(self, event):
        """控制任务的上下边距"""
        self.mysetting_dict["task_geometry"] = \
            [(self.mysetting_dict["task_geometry"][0][0], self.mysetting_dict["task_geometry"][0][1],
              self.mysetting_dict["task_geometry"][0][2], self.task_margin_y_scale.get_value())]

        self.tile_queue.put("refresh_tasks")


def just_one_instance(func):
    """一个Python实例"""

    @functools.wraps(func)
    def f(*args, **kwargs):
        # 保证只能运行一个Python实例，方法是程序运行时监听一个特定端口，如果失败则说明已经有实例在跑
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


def my_logs(exe_dir_path):
    # 创建logs文件夹
    if not os.path.exists(exe_dir_path + r"/logs/"):
        os.mkdir(exe_dir_path + r"/logs/")

    # 开启日志记录:创建一个logger
    logger = logging.getLogger()
    # Log等级总开关
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")  # 日志格式

    # 创建一个handler，用于写入日志文件
    fh = logging.FileHandler(
        exe_dir_path + '/logs/' + time.strftime('%Y%m%d%H%M', time.localtime(time.time())) + '.log', mode='w',
        encoding="utf8")
    fh.setLevel(logging.INFO)  # 输出到file的log等级的开关
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # 创建一个handler，用于写入控制台
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)  # 输出到console的log等级的开关
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger



@just_one_instance
def main():
    # pathlib可以根据平台自动转换斜杠，不过返回的不是str，还需要转化
    # exe_dir_path=str(Path(sys.argv[0]).parent)

    exe_dir_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    # print(exe_dir_path)

    os.environ['REQUESTS_CA_BUNDLE'] = os.path.join(exe_dir_path, 'cacert.pem')
    # print(os.environ['REQUESTS_CA_BUNDLE'])

    logger = my_logs(exe_dir_path)
    logger.info(exe_dir_path)

    # 获取屏幕信息
    screen_info = win32api.GetMonitorInfo(win32api.MonitorFromPoint((0, 0)))
    logger.info(str(screen_info))

    # 获取时区
    # local_tz = get_localzone()
    # logger.info(local_tz)

    # 需要在创建窗口之前读取的数据
    if not os.path.exists(exe_dir_path + "/first.sqlite"):
        logger.info("第一次运行")
        first_dict = SqliteDict(exe_dir_path + '/first.sqlite', autocommit=True)
        first_dict["scaling_flag"] = [0]
        first_dict["scaling"] = [133]
    else:
        first_dict = SqliteDict(exe_dir_path + '/first.sqlite', autocommit=True)
        logger.info([(x, i) for x, i in first_dict.items()])

    try:
        MainWindow(
            title="CountBoard",
            icon=str(Path(exe_dir_path).joinpath("favicon.ico")),
            topmost=1,
            width=screen_info.get("Monitor")[2] * 1 / 2,
            height=screen_info.get("Monitor")[3] * 4 / 5,
            version="1.3",
            logger=logger,
            exe_dir_path=exe_dir_path,
            show=0,
            first_dict=first_dict)
    except:
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    utility.enable_high_dpi_awareness()
    main()

# -w不带控制行
# 用户名带空格-->用引号 C:\Users\Gao yongxian\PycharmProjects\CountBoard
# pyinstaller -F -i "C:\Users\Gao yongxian\PycharmProjects\CountBoard\favicon.ico" "C:\Users\Gao yongxian\PycharmProjects\CountBoard\CountBoard.py"
# pyinstaller -F -i "C:\Users\Gao yongxian\PycharmProjects\CountBoard\favicon.ico" "C:\Users\Gao yongxian\PycharmProjects\CountBoard\CountBoard.py" -w --additional-hooks-dir=./hooks
