import random
import tkinter as tk
from datetime import datetime
from threading import Thread
from tkinter import *
from tkinter import ttk, colorchooser
from tkinter.filedialog import askopenfilename
from PIL import Image, ImageTk
from markdown2 import Markdown
from sqlitedict import SqliteDict
from SysTrayIcon import SysTrayIcon
from TkHtmlView import TkHtmlView
from TkCalendar import Calendar
import sys,os


class Main_window(object):
    """主窗体"""
    root_x, root_y, abs_x, abs_y = 0, 0, 0, 0

    def __init__(self, title, icon, alpha, topmost, bg, width, height, width_adjust, higth_adjust):
        self.root = tk.Tk()
        self.title = title
        self.icon = icon
        self.root.title(title)
        self.root.wm_attributes('-alpha', alpha)
        self.root.wm_attributes('-topmost', topmost)
        self.root.configure(bg=bg)

        self.root.iconbitmap(icon)
        self.width = width
        self.height = height
        self.width_adjust = width_adjust
        self.higth_adjust = higth_adjust

        self.exe_dir_path=os.path.dirname(sys.argv[0])

        self.width, self.height = width, height
        self.root.geometry("%dx%d-%d+%d" % (width, height, width_adjust, higth_adjust))

        self.root.maxsize(width, 2000)
        self.root.minsize(width, 120)

        self.frame_bottom = Frame(self.root, bg=bg)
        self.frame_bottom.pack(side=BOTTOM)
        self.frame_top = Frame(self.root)
        self.frame_top.pack(side=TOP, fill="both", expand=True)

        # 画布
        self.canvas = Canvas(self.frame_top, bg=bg)
        self.canvas.config(highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill="both", expand=True)

        # 切换置顶按钮
        self.top_photo_image = ImageTk.PhotoImage(Image.open(self.exe_dir_path+"/img/"+"置顶展示.png").resize((18, 18)))
        self.cancel_top_photo_image = ImageTk.PhotoImage(Image.open(self.exe_dir_path+"/img/"+"取消置顶.png").resize((18, 18)))
        self.top_button = tk.Button(self.frame_bottom,
                                    command=self.top,
                                    text="始终置顶",
                                    bg=bg,
                                    image=self.top_photo_image,
                                    relief="flat",
                                    overrelief="groove")
        self.top_button.pack(side=tk.LEFT, padx=5, pady=2)

        # 切换模式按钮
        self.mode_photo_image = ImageTk.PhotoImage(Image.open(self.exe_dir_path+"/img/"+"快递.png").resize((18, 18)))
        self.normal_mode_photo_image = ImageTk.PhotoImage(Image.open(self.exe_dir_path+"/img/"+"普通.png").resize((18, 18)))
        self.mode_button = tk.Button(self.frame_bottom,
                                     command=self.mode,
                                     bg=bg,
                                     text="普通模式",
                                     image=self.mode_photo_image,
                                     relief="flat",
                                     overrelief="groove")
        self.mode_button.pack(side=tk.LEFT, padx=5, pady=2)

        # 新建按钮
        self.create_task_image = Image.open(self.exe_dir_path+"/img/"+"新建.png").resize((18, 18))
        self.create_task__photo_image = ImageTk.PhotoImage(self.create_task_image)
        self.create_task__button = tk.Button(self.frame_bottom, command=self.create_task,
                                             bg=bg,
                                             text="普通模式", image=self.create_task__photo_image,
                                             relief="flat",
                                             overrelief="groove")

        self.create_task__button.pack(side=tk.LEFT, padx=5, pady=2)

        # 设置按钮
        self.setting_photo_image = ImageTk.PhotoImage(Image.open(self.exe_dir_path+"/img/"+"settings.png").resize((19, 19)))
        self.setting_button = tk.Button(self.frame_bottom,
                                        command=self.setting,
                                        bg=bg,
                                        image=self.setting_photo_image,
                                        relief="flat",
                                        overrelief="groove")
        self.setting_button.pack(side=tk.LEFT, padx=5, pady=2)

        # 透明度按钮
        self.alpha_photo_image = ImageTk.PhotoImage(Image.open(self.exe_dir_path+"/img/"+"透明度.png").resize((18, 18)))
        self.alpha_button = tk.Button(self.frame_bottom,
                                      command=self.alpha,
                                      bg=bg,
                                      image=self.alpha_photo_image,
                                      relief="flat",
                                      overrelief="groove")
        self.alpha_button.pack(side=tk.LEFT, padx=5, pady=2)

        # 删除按钮
        self.del_all_photo_image = ImageTk.PhotoImage(Image.open(self.exe_dir_path+"/img/"+"删除全部.png").resize((18, 18)))
        self.del_all_button = tk.Button(self.frame_bottom,
                                        command=self.del_all,
                                        bg=bg,
                                        image=self.del_all_photo_image,
                                        relief="flat",
                                        overrelief="groove")
        self.del_all_button.pack(side=tk.LEFT, padx=5, pady=2)

        # 帮助按钮
        self.help_photo_image = ImageTk.PhotoImage(Image.open(self.exe_dir_path+"/img/"+"帮助中心.png").resize((18, 18)))
        self.help_button = tk.Button(self.frame_bottom,
                                     command=self.help,
                                     bg=bg,
                                     image=self.help_photo_image,
                                     relief="flat",
                                     overrelief="groove")
        self.help_button.pack(side=tk.LEFT, padx=5, pady=2)

        # 退出按钮
        self.exit_photo_image = ImageTk.PhotoImage(Image.open(self.exe_dir_path+"/img/"+"退出.png").resize((18, 18)))
        self.exit_button = tk.Button(self.frame_bottom,
                                     command=self.exit,
                                     bg=bg,
                                     image=self.exit_photo_image,
                                     relief="flat",
                                     overrelief="groove")
        self.exit_button.pack(side=tk.LEFT, padx=5, pady=2)

        # 任务列表
        self.tasks = Tasks(pre_window=self)
        self.tasks.show_all()

        # 最小化
        self.SysTrayIcon = None
        self.root.bind("<Unmap>",
                       lambda event: self.Hidden_window() if self.root.state() == 'iconic' else False)
        self.root.protocol('WM_DELETE_WINDOW', self.exit)

        self.root.mainloop()

    def set_theme(self, bg):
        self.root.configure(bg=bg)
        self.frame_top.configure(bg=bg)
        self.frame_bottom.configure(bg=bg)
        self.canvas.configure(bg=bg)

        self.top_button.configure(bg=bg)
        self.alpha_button.configure(bg=bg)
        self.mode_button.configure(bg=bg)
        self.setting_button.configure(bg=bg)
        self.help_button.configure(bg=bg)
        self.exit_button.configure(bg=bg)
        self.del_all_button.configure(bg=bg)
        self.create_task__button.configure(bg=bg)

        self.tasks.refresh_tasks()

    def alpha(self):
        Alpha_window(
            height=40,
            pre_window=self)

    def del_all(self):
        Ask_del_window(
            height=80,
            pre_window=self)

    def help(self,**kwargs):
        Help_window(width=1000,
                    height=600,
                    path=self.exe_dir_path+"/README.md")

    def setting(self):
        Setting_window(
            height=110,
            pre_window=self)

    def create_task(self):
        Newtask_window(
            height=180,
            pre_window=self)

    def top(self):
        if self.top_button.cget("text") == "始终置顶":
            self.root.wm_attributes('-topmost', 1)
            self.top_button.config(text="取消置顶", image=self.cancel_top_photo_image)
        else:
            self.root.wm_attributes('-topmost', 0)
            self.top_button.config(text="始终置顶", image=self.top_photo_image)

    def mode(self):
        if self.mode_button.cget("text") == "普通模式":
            self.root.overrideredirect(1)
            self.mode_button.config(text="简洁模式", image=self.normal_mode_photo_image)

            # 自动置顶
            self.root.wm_attributes('-topmost', 1)
            self.top_button.config(text="取消置顶", image=self.cancel_top_photo_image)

            self.root.bind('<B1-Motion>', self._on_move)
            self.root.bind('<ButtonPress-1>', self._on_tap)
        else:
            self.root.overrideredirect(0)
            self.mode_button.config(text="普通模式", image=self.mode_photo_image)

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
        self.width = self.root.winfo_width()
        self.height = self.root.winfo_height()
        self.root_x, self.root_y = event.x_root, event.y_root
        self.abs_x, self.abs_y = self.root.winfo_x(), self.root.winfo_y()

    def show_msg(s, title='标题', msg='内容', time=500):
        s.SysTrayIcon.refresh(title=title, msg=msg, time=time)

    def Hidden_window(s, icon='favicon.ico', hover_text="CountBoard"):
        icon = s.icon
        hover_text = s.title
        menu_options = ()

        s.root.withdraw()  # 隐藏tk窗口
        if not s.SysTrayIcon: s.SysTrayIcon = SysTrayIcon(
            icon,  # 图标
            hover_text,  # 光标停留显示文字
            menu_options,  # 右键菜单
            on_quit=s.exit,  # 退出调用
            tk_window=s.root,  # Tk窗口
        )
        s.SysTrayIcon.activation()

    def exit(s, _sysTrayIcon=None):
        s.root.destroy()


class Tasks:
    def __init__(self, pre_window, **kwargs, ):
        # 接收数据
        self.pre_window = pre_window
        self.root = pre_window.root
        self.width = pre_window.width

        # key=main_text,value[0]=main_text,value[1]=time_text,value[2]=countdown_time,value[3]=color,value[4]=tag_name.
        self.mydict = SqliteDict(exe_dir_path+'/my_db.sqlite', autocommit=True)
        self.canvas = pre_window.canvas

        self.task_init_x = 15
        self.task_init_y = 15

        self.task_width = 300
        self.task_height = 60
        self.task_radius = 20

        self.__int_update_time()

    def __int_update_time(self):
        # 初始化更新时间
        from datetime import datetime
        for key, value in self.mydict.iteritems():
            startdate = datetime.today()
            enddate = datetime.strptime(value[1], '%Y-%m-%d')
            days = str((enddate - startdate).days)
            self.mydict[key] = [value[0], value[1], days, value[3], value[4],value[5]]

    def del_all(self):
        # 删除所有数据
        self.canvas.delete("all")
        for key in self.mydict.iterkeys():
            self.mydict.__delitem__(key)

    def show_all(self):
        # 展示当前数据库的所以元素
        self.canvas.delete("all")
        for value in sorted(self.mydict.itervalues(), key=self.get_int_day):
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
        self.canvas.create_polygon(points, **kwargs, smooth=True, outline="white")

    def add_task(self, value):
        self.task_main_text = value[0]
        self.task_time_text = value[1]
        mode = SqliteDict(exe_dir_path+'/setting.sqlite').__getitem__("mode")[0]
        if mode=="普通模式":
            self.task_countdown_text = str(int(value[2])+1)
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
        self.canvas.create_text(self.task_init_x + 280,
                                self.task_init_y + 30,
                                text=self.task_countdown_text + "天",
                                width=220,
                                font=('microsoft yahei', 25, 'bold'),
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
        self.mydict[value[0]] = value

    def handler_adaptor(self, fun, **kwds):
        return lambda event, fun=fun, kwds=kwds: fun(event, **kwds)

    def task_DoubleClick(self, event, task_tag_name):
        for value in self.mydict.itervalues():
            if value[4] == task_tag_name:
                Newtask_window(
                    height=180,
                    pre_window=self.pre_window,
                    value=value)
                return 1
        print("no!" + task_tag_name)

    def del_one(self, value):
        self.mydict.__delitem__(value)

    def refresh_tasks(self):
        # 画布删除,重新画
        self.canvas.delete("all")
        self.task_init_y = 15
        self.show_all()


class Newtask_window(object):
    def __init__(self, height, pre_window, **kwargs):
        self.root = tk.Toplevel()
        self.root.title('新建日程')
        self.root.iconbitmap("favicon.ico")
        self.tasks = pre_window.tasks
        self.pre_window = pre_window
        self.pre_window_root = pre_window.root
        self.width, self.height = pre_window.width, height
        self.exe_dir_path=pre_window.exe_dir_path

        self.pre_window_root_x, self.pre_window_root_y, self.pre_window_root_w, self.pre_window_root_h = \
            self.pre_window_root.winfo_x(), \
            self.pre_window_root.winfo_y(), \
            self.pre_window_root.winfo_width(), \
            self.pre_window_root.winfo_height()
        self.width_adjust = self.pre_window_root_x
        self.height_adjust = self.pre_window_root_y + self.pre_window_root_h + 40

        self.root.geometry("%dx%d+%d+%d" % (self.width, self.height, self.width_adjust, self.height_adjust))

        # 布局
        self.frame_top = Frame(self.root)
        self.frame_top.pack(side=TOP, padx=20, pady=10)
        self.frame_middle = Frame(self.root)
        self.frame_middle.pack(side=TOP, padx=20, pady=1)
        self.frame_middle2 = Frame(self.root)
        self.frame_middle2.pack(side=TOP, padx=20, pady=10)
        self.frame_bottom2 = Frame(self.root)
        self.frame_bottom2.pack(side=BOTTOM, padx=20, expand=True, fill=X)
        self.frame_bottom = Frame(self.root)
        self.frame_bottom.pack(side=BOTTOM, padx=20)

        # 日程名称
        ttk.Label(self.frame_top, text="日程名称").pack(side=tk.LEFT, padx=5, pady=2)
        self.task_name_str = tk.StringVar()
        self.task_name = ttk.Entry(self.frame_top,
                                   validate="focus",  # 获取焦点调用test函数
                                   validatecommand=self.clear,
                                   textvariable=self.task_name_str)
        self.task_name.pack(side=tk.LEFT, fill="x", expand=True)
        tk.Label(self.frame_top, state="disable", width=1000).pack(side=tk.LEFT, expand=True, fill=X)

        # 选择时间
        ttk.Label(self.frame_middle, text="选择时间").pack(side=tk.LEFT, padx=5, pady=2)
        self.date_str = tk.StringVar()
        self.date = tk.Entry(self.frame_middle, textvariable=self.date_str, width=10)
        self.date.pack(side=tk.LEFT)
        date_str_gain = lambda: [self.date_str.set(date) for date in
                                 [Calendar((self.width_adjust, self.height_adjust), 'ul').selection()] if date]
        self.data_photo_image = ImageTk.PhotoImage(Image.open(self.exe_dir_path+"/img/"+"234日历.png").resize((15, 15)))
        self.data_button = tk.Button(self.frame_middle, command=date_str_gain,
                                     text="日期",
                                     image=self.data_photo_image,
                                     relief="flat",
                                     overrelief="groove").pack(side=tk.LEFT)
        tk.Label(self.frame_middle, state="disable", width=1000).pack(side=tk.LEFT, expand=True, fill=X)

        # 背景颜色
        ttk.Label(self.frame_middle2, text="背景颜色").pack(side=tk.LEFT, padx=5, pady=2)
        self.color_str = tk.StringVar()
        self.color_frame = tk.Entry(self.frame_middle2, width=10, textvariable=self.color_str)
        self.color_frame.pack(side=tk.LEFT)
        self.color_photo_image = ImageTk.PhotoImage(Image.open(self.exe_dir_path+"/img/"+"颜色.png").resize((15, 15)))
        self.color_button = tk.Button(self.frame_middle2,
                                      command=self.onChoose,
                                      text="日期",
                                      image=self.color_photo_image,
                                      relief="flat",
                                      overrelief="groove")
        self.color_button.pack(side=tk.LEFT)
        tk.Label(self.frame_middle2, state="disable", width=1000).pack(side=tk.LEFT, expand=True, fill=X)

        # 字体颜色
        ttk.Label(self.frame_bottom, text="字体颜色").pack(side=tk.LEFT, padx=5, pady=2)
        self.text_color_str = tk.StringVar()
        self.text_color_frame = tk.Entry(self.frame_bottom, width=10, textvariable=self.text_color_str)
        self.text_color_frame.pack(side=tk.LEFT)
        self.text_color_photo_image = ImageTk.PhotoImage(Image.open(self.exe_dir_path+"/img/"+"字体颜色.png").resize((15, 15)))
        self.text_color_button = tk.Button(self.frame_bottom,
                                           command=self.text_onChoose,
                                           text="日期",
                                           image=self.text_color_photo_image,
                                           relief="flat", overrelief="groove")
        self.text_color_button.pack(side=tk.LEFT)
        tk.Label(self.frame_bottom, state="disable", width=1000).pack(side=tk.LEFT, expand=True, fill=X)

        # 完成按钮
        self.save_task_photo_image = ImageTk.PhotoImage(Image.open(self.exe_dir_path+"/img/"+"对勾.png").resize((15, 15)))
        self.save_task_button = tk.Button(self.frame_bottom2, command=self.ok,
                                          text="完成",
                                          image=self.save_task_photo_image,
                                          relief="flat", overrelief="groove")
        self.save_task_button.pack(side=tk.RIGHT)

        # 配置默认数据,初始化
        self.modify_flag = 0
        self.task_name.insert(0, "创建你的日程吧！")
        self.date.insert(0, datetime.today().date())

        self.color_frame.insert(0, "#c0c0c0")
        self.color_frame.config(background="#c0c0c0")

        self.text_color_frame.insert(0, "#ffffff")
        self.text_color_frame.config(background="#ffffff")
        '''***********************************下面区别于new_task**************************************************'''
        for key in kwargs:
            if key == "value":
                self.modify_flag = 1
                self.root.title('修改日程')

                self.value = kwargs["value"]


                # 配置参数,初始化
                self.task_name.delete(0, "end")
                self.task_name.insert(0, self.value[0])

                self.date.delete(0, "end")
                self.date.insert(0, self.value[1])

                self.color_frame.delete(0, "end")
                self.color_frame.insert(0, self.value[3])
                self.color_frame.config(background=self.value[3])

                self.text_color_frame.delete(0, "end")
                self.text_color_frame.insert(0, self.value[5])
                self.text_color_frame.config(background=self.value[5])

                # 删除按钮
                self.del_task_photo_image=ImageTk.PhotoImage(Image.open(self.exe_dir_path+"/img/"+"删除色块.png").resize((15, 15)))
                self.del_task_button = tk.Button(self.frame_bottom2, command=self.del_task,
                                                 text="完成",
                                                 image=self.del_task_photo_image,
                                                 relief="flat", overrelief="groove")
                self.del_task_button.pack(side=tk.RIGHT)

        self.root.mainloop()

    def del_task(self):
        self.tasks.del_one(self.value[0])
        self.tasks.refresh_tasks()
        self.root.destroy()

    def clear(self):
        # 点击输入框的回调,删除提示内容
        if "创建你的日程" in self.task_name.get():
            self.task_name.delete(0, "end")

    def ok(self):
        if self.modify_flag == 1:
            # 先删除一项,然后再添加一项
            self.tasks.del_one(self.value[0])

        # 点击确认按钮,更新数据库
        startdate = datetime.today()
        enddate = datetime.strptime(self.date_str.get(), '%Y-%m-%d')
        days = str((enddate - startdate).days)
        value = [self.task_name_str.get(),
                 self.date_str.get(),
                 days,
                 self.color_str.get(),
                 ''.join(random.sample('zyxwvutsrqponmlkjihgfedcba1234567890', 5)),
                 self.text_color_str.get()]
        self.tasks.add_one(value)
        self.tasks.refresh_tasks()
        self.root.destroy()

    def text_onChoose(self):
        (rgb, hx) = colorchooser.askcolor()
        self.text_color_frame.config(background=hx)
        self.text_color_frame.delete(0, 'end')
        self.text_color_frame.insert(0, hx)

    def onChoose(self):
        (rgb, hx) = colorchooser.askcolor()
        self.color_frame.config(background=hx)
        self.color_frame.delete(0, 'end')
        self.color_frame.insert(0, hx)


class Alpha_window(object):
    def __init__(self, height, pre_window, **kwargs):
        self.root = tk.Toplevel()
        self.root.title('调整透明度')
        self.root.iconbitmap("favicon.ico")

        self.pre_window = pre_window
        self.pre_window_root = pre_window.root
        self.width = pre_window.width
        self.tasks = pre_window.tasks
        self.height = height

        self.pre_window_root_x, self.pre_window_root_y, self.pre_window_root_w, self.pre_window_root_h = \
            self.pre_window_root.winfo_x(), \
            self.pre_window_root.winfo_y(), \
            self.pre_window_root.winfo_width(), \
            self.pre_window_root.winfo_height()
        self.width_adjust = self.pre_window_root_x
        self.height_adjust = self.pre_window_root_y + self.pre_window_root_h + 40

        self.root.geometry("%dx%d+%d+%d" % (self.width, self.height, self.width_adjust, self.height_adjust))

        # 布局
        self.frame_bottom = Frame(self.root)
        self.frame_bottom.pack(side=BOTTOM, fill="x", expand=True, padx=10, pady=5)
        # ttk.Style().configure("TScale",
        #                       # background="#ccc",
        #                       sliderwidth=0.1)
        self.scale = ttk.Scale(self.frame_bottom, from_=30, to=100,
                               # style="TScale",
                               command=self.set_alpha,
                               value=90)
        self.scale.pack(side=tk.LEFT, padx=5, pady=2, expand=True, fill=X)
        self.scale.set(float(self.pre_window_root.wm_attributes("-alpha"))*100)
        self.root.mainloop()

    def set_alpha(self, i):
        self.pre_window_root.attributes('-alpha', float(i)/100)


class Ask_del_window(object):
    def __init__(self, height, pre_window, **kwargs):
        self.root = tk.Toplevel()
        self.root.title('删除全部')
        self.root.iconbitmap("favicon.ico")
        self.pre_window = pre_window
        self.pre_window_root = pre_window.root
        self.width = pre_window.width
        self.tasks = pre_window.tasks
        self.height = height
        self.exe_dir_path =pre_window.exe_dir_path

        self.pre_window_root_x, self.pre_window_root_y, self.pre_window_root_w, self.pre_window_root_h = \
            self.pre_window_root.winfo_x(), \
            self.pre_window_root.winfo_y(), \
            self.pre_window_root.winfo_width(), \
            self.pre_window_root.winfo_height()
        self.width_adjust = self.pre_window_root_x
        self.height_adjust = self.pre_window_root_y + self.pre_window_root_h + 40

        self.root.geometry("%dx%d+%d+%d" % (self.width, self.height, self.width_adjust, self.height_adjust))

        # 布局
        self.frame_top = Frame(self.root)
        self.frame_top.pack(side=TOP, padx=20, pady=5, expand=True, fill=X)
        self.frame_bottom = Frame(self.root)
        self.frame_bottom.pack(side=BOTTOM, padx=20, expand=True, fill=X)
        self.lable = ttk.Label(self.frame_top, text="是否要删除全部?"
                               )
        self.lable.pack(side=tk.LEFT, padx=5, pady=2, expand=True, fill=X)

        self.cancel_image = ImageTk.PhotoImage(Image.open(self.exe_dir_path+"/img/"+"取消.png").resize((18, 18)))
        self.cancel_button = tk.Button(self.frame_bottom,
                                       command=self.cancel,
                                       image=self.cancel_image,
                                       relief="flat",
                                       overrelief="groove")
        self.cancel_button.pack(side=tk.RIGHT, padx=5, pady=2)

        self.ok_image = ImageTk.PhotoImage(Image.open(self.exe_dir_path+"/img/"+"确认.png").resize((18, 18)))
        self.ok_button = tk.Button(self.frame_bottom,
                                   command=self.ok,
                                   image=self.ok_image,
                                   relief="flat",
                                   overrelief="groove")
        self.ok_button.pack(side=tk.RIGHT, padx=5, pady=2)

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
        self.mydict = SqliteDict(self.exe_dir_path+'/setting.sqlite', autocommit=True)
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
        self.theme_color_photo_image = ImageTk.PhotoImage(Image.open(self.exe_dir_path+"/img/"+"颜色.png").resize((15, 15)))
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
        self.cancel_image = ImageTk.PhotoImage(Image.open(self.exe_dir_path+"/img/"+"取消.png").resize((18, 18)))
        self.cancel_button = tk.Button(self.frame_bottom,
                                       command=self.cancel,
                                       image=self.cancel_image,
                                       relief="flat",
                                       overrelief="groove")
        self.cancel_button.pack(side=tk.RIGHT, padx=5, pady=2)

        # 确定按钮
        self.ok_image = ImageTk.PhotoImage(Image.open(self.exe_dir_path+"/img/"+"确认.png").resize((18, 18)))
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
        self.root = tk.Toplevel()
        self.root.title('使用说明')
        self.root.iconbitmap("favicon.ico")
        self.path = path
        # 居中显示
        self.width, self.height = width, height
        win_width = self.root.winfo_screenwidth()
        win_higth = self.root.winfo_screenheight()
        width_adjust = (win_width - width) / 2
        higth_adjust = (win_higth - height) / 2
        self.root.geometry("%dx%d+%d+%d" % (width, height, width_adjust, higth_adjust))

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
    exe_dir_path=os.path.dirname(sys.argv[0])
    print(exe_dir_path)
    if not os.path.exists(exe_dir_path+"/setting.sqlite"):
        print("第一次运行")
        mydict = SqliteDict(exe_dir_path+'/setting.sqlite')
        mydict["theme"] = ["white"]
        mydict["mode"] = ["普通模式"]
        mydict.commit()
        mydict.close()

    bg = SqliteDict(exe_dir_path+'/setting.sqlite').__getitem__("theme")[0]
    main = Main_window(title="CountBoard",
                       icon="favicon.ico",
                       alpha=0.9, topmost=0,
                       bg=bg,
                       width=330,
                       height=190,
                       width_adjust=10,
                       higth_adjust=5)


# -w不带控制行
# 用户名带空格--用引号
# pyinstaller -F -i E:\favicon.ico "C:\Users\Gao yongxian\PycharmProjects\CountBoard\CountBoard.py" -w
