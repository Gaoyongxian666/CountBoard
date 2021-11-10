# -*- coding: UTF-8 -*-
"""
@Project ：CountBoard
@File ：CustomWindow.py
@Author ：Gao yongxian
@Date ：2021/11/8 11:00
@contact: g1695698547@163.com
"""
import os
import sys
import traceback
from pathlib import Path
from win32api import GetMonitorInfo, MonitorFromPoint


class CustomWindow(object):
    """
    自定义模板(用来窗口初始化): self.root要在继承之前使用，tk.Toplevel() 或 tk.TK()
    """

    def __init__(self, *args, **kwargs):
        """
        初始化
        """
        super().__init__()

        # 传参
        try:
            self.overrideredirect = kwargs["overrideredirect"]
        except:
            self.overrideredirect = 0
        try:
            self.width = kwargs["width"]
        except:
            self.width = 300
        try:
            self.height = kwargs["height"]
        except:
            self.height = 300
        try:
            self.title = kwargs["title"]
        except:
            self.title = "无标题"
        try:
            self.position = kwargs["position"]
        except:
            self.position = "center"
        try:
            self.icon = kwargs["icon"]
        except:
            exe_dir_path = os.path.dirname(sys.argv[0])
            self.icon = str(Path(exe_dir_path).joinpath("favicon.ico"))
        try:
            self.topmost = kwargs["topmost"]
        except:
            self.topmost = 1
        try:
            self.alpha = kwargs["alpha"]
        except:
            self.alpha = 1
        try:
            self.pre_window = kwargs["pre_window"]
        except:
            self.pre_window = None
        try:
            self._geometry = kwargs["_geometry"]
        except:
            self._geometry = "(300x300+300+300)"

        try:
            self._auto_margin = kwargs["_auto_margin"]
        except:
            self._auto_margin = False

        try:
            self.offset = kwargs["offset"]
        except:
            self.offset = 0

        # 窗体初始化
        self.root.title(self.title)
        self.root.iconbitmap(self.icon)
        self.root.wm_attributes('-alpha', self.alpha)
        self.root.wm_attributes('-topmost', self.topmost)
        # 此项只有最后设置才可以，否则无法起效
        self.root.overrideredirect(self.overrideredirect)

        # 使用win32获取屏幕宽高和工作宽高
        monitor_info = GetMonitorInfo(MonitorFromPoint((0, 0)))
        # print('monitor info:{}'.format(monitor_info))
        work = monitor_info.get('Work')
        # print('工作区间:{}'.format(work))
        self.work_width = work[2]
        self.work_heigh = work[3]

        # 屏幕宽高
        self.win_width = self.root.winfo_screenwidth()
        self.win_heigth = self.root.winfo_screenheight()

        if self.position == "custom":
            self.width = self._geometry[0]
            self.height = self._geometry[1]

        # 设置位置
        self.set_position(self.position, self.pre_window, self._geometry)
        self.set_auto_margin(self._auto_margin)

    def modify_offset(self, offset):
        """修改贴边距离"""
        self.offset = offset

    def modify_auto_margin(self, _auto_margin):
        """修改是否贴边"""
        self._auto_margin = _auto_margin

    def set_position(self, position="center", pre_window=None, _geometry: str = ""):
        """
        设置窗体的位置,可以在外部调用

        Args:
            position: 窗体位置
            pre_window: 上一个窗体对象
            _geometry: 自定义位置
        """
        if position == "center":
            # 中心位置,要传入宽高
            width_adjust = (self.win_width - self.width) / 2
            higth_adjust = (self.win_heigth - self.height) / 2
            self.root.geometry("%dx%d+%d+%d" % (self.width, self.height, width_adjust, higth_adjust))
        elif position == "follow":
            # 跟随位置,要传入高
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
        elif position == "custom":
            # 自定义位置，要传入_geometry
            self.root.geometry("%dx%d+%d+%d" % _geometry)

    def close(self):
        """
        关闭窗体
        """
        self.root.destroy()

    def set_auto_margin(self, flag):
        """
        设置自动贴边：注意无边的窗口才可以
        """
        self.root_x, self.root_y, self.abs_x, self.abs_y = 0, 0, 0, 0

        if flag == True:
            self.root.bind('<B1-Motion>', self._on_move)
            self.root.bind('<ButtonPress-1>', self._on_tap)
            self.root.bind('<ButtonRelease-1>', self._on_release)
        else:
            self.root.unbind('<B1-Motion>')
            self.root.unbind('<ButtonPress-1>')
            self.root.unbind('<ButtonRelease-1>')

    def _on_move(self, event):
        """
        移动
        """
        offset_x = event.x_root - self.root_x
        offset_y = event.y_root - self.root_y

        x_adjust = self.abs_x + offset_x
        y_adjust = self.abs_y + offset_y

        geo_str = "%dx%d+%d+%d" % (self.width, self.height,
                                   x_adjust, y_adjust)
        self.root.geometry(geo_str)

    def _on_tap(self, event):
        """
        鼠标左键按下，获取当前窗口信息以及鼠标信息
        """
        self.root_x, self.root_y = event.x_root, event.y_root
        self.abs_x, self.abs_y = self.root.winfo_x(), self.root.winfo_y()
        self.width = self.root.winfo_width()
        self.height = self.root.winfo_height()

    def _on_release(self, event, **kwargs):
        """
        鼠标左键弹起
        """
        offset_x = event.x_root - self.root_x
        offset_y = event.y_root - self.root_y

        if self._auto_margin:
            if self.width + self.abs_x + offset_x > self.work_width:
                x_adjust = self.work_width - self.width - self.offset
            elif self.abs_x + offset_x < 0:
                x_adjust = 0 + self.offset
            else:
                x_adjust = self.abs_x + offset_x

            if self.height + self.abs_y + offset_y > self.work_heigh:
                y_adjust = self.work_heigh - self.height - self.offset
            elif self.abs_y + offset_y < 0:
                y_adjust = 0 + self.offset
            else:
                y_adjust = self.abs_y + offset_y
        else:
            y_adjust = self.abs_y + offset_y
            x_adjust = self.abs_x + offset_x

        geo_str = "%dx%d+%d+%d" % (self.width, self.height, x_adjust, y_adjust)

        try:
            mysetting_dict = kwargs["mysetting_dict"]
            mysetting_dict["tile_geometry"] = [(self.width, self.height, x_adjust, y_adjust)]
            print("写入数据库成功")

        except:
            print("写入数据库失败")
            print(traceback.format_exc())

        self.root.geometry(geo_str)


