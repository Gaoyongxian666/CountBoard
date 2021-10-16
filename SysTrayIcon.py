import win32api, win32con, win32gui_struct, win32gui
import os

class SysTrayIcon(object):
    '''SysTrayIcon类用于显示任务栏图标'''
    QUIT = 'QUIT'
    SPECIAL_ACTIONS = [QUIT]
    FIRST_ID = 5320

    def __init__(s, icon, hover_text, menu_options, on_quit, tk_window=None, default_menu_index=None,
                 window_class_name=None):
        '''
        icon         需要显示的图标文件路径
        hover_text   鼠标停留在图标上方时显示的文字
        menu_options 右键菜单，格式: (('a', None, callback), ('b', None, (('b1', None, callback),)))
        on_quit      传递退出函数，在执行退出时一并运行
        tk_window    传递Tk窗口，s.root，用于单击图标显示窗口
        default_menu_index 不显示的右键菜单序号
        window_class_name  窗口类名
        '''
        s.icon = icon
        s.hover_text = hover_text
        s.on_quit = on_quit
        s.root = tk_window

        menu_options = menu_options + (('退出', None, s.QUIT),)
        s._next_action_id = s.FIRST_ID
        s.menu_actions_by_id = set()
        s.menu_options = s._add_ids_to_menu_options(list(menu_options))
        s.menu_actions_by_id = dict(s.menu_actions_by_id)
        del s._next_action_id

        s.default_menu_index = (default_menu_index or 0)
        s.window_class_name = window_class_name or "SysTrayIconPy"

        message_map = {win32gui.RegisterWindowMessage("TaskbarCreated"): s.restart,
                       win32con.WM_DESTROY: s.destroy,
                       win32con.WM_COMMAND: s.command,
                       win32con.WM_USER + 20: s.notify, }
        # 注册窗口类。
        wc = win32gui.WNDCLASS()
        wc.hInstance = win32gui.GetModuleHandle(None)
        wc.lpszClassName = s.window_class_name
        wc.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW;
        wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        wc.hbrBackground = win32con.COLOR_WINDOW
        wc.lpfnWndProc = message_map  # 也可以指定wndproc.
        s.classAtom = win32gui.RegisterClass(wc)

    def activation(s):
        '''激活任务栏图标，不用每次都重新创建新的托盘图标'''
        hinst = win32gui.GetModuleHandle(None)  # 创建窗口。
        style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
        s.hwnd = win32gui.CreateWindow(s.classAtom,
                                       s.window_class_name,
                                       style,
                                       0, 0,
                                       win32con.CW_USEDEFAULT,
                                       win32con.CW_USEDEFAULT,
                                       0, 0, hinst, None)
        win32gui.UpdateWindow(s.hwnd)
        s.notify_id = None
        s.refresh(title='软件已后台！', msg='点击重新打开', time=500)

        win32gui.PumpMessages()

    def refresh(s, title='', msg='', time=500):
        '''刷新托盘图标
           title 标题
           msg   内容，为空的话就不显示提示
           time  提示显示时间'''
        hinst = win32gui.GetModuleHandle(None)
        if os.path.isfile(s.icon):
            icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
            hicon = win32gui.LoadImage(hinst, s.icon, win32con.IMAGE_ICON,
                                       0, 0, icon_flags)
        else:  # 找不到图标文件 - 使用默认值
            hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)

        if s.notify_id:
            message = win32gui.NIM_MODIFY
        else:
            message = win32gui.NIM_ADD

        s.notify_id = (s.hwnd, 0,  # 句柄、托盘图标ID
                       win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP | win32gui.NIF_INFO,
                       # 托盘图标可以使用的功能的标识
                       win32con.WM_USER + 20, hicon, s.hover_text,  # 回调消息ID、托盘图标句柄、图标字符串
                       msg, time, title,  # 提示内容、提示显示时间、提示标题
                       win32gui.NIIF_INFO  # 提示用到的图标
                       )
        win32gui.Shell_NotifyIcon(message, s.notify_id)

    def show_menu(s):
        '''显示右键菜单'''
        menu = win32gui.CreatePopupMenu()
        s.create_menu(menu, s.menu_options)

        pos = win32gui.GetCursorPos()
        win32gui.SetForegroundWindow(s.hwnd)
        win32gui.TrackPopupMenu(menu,
                                win32con.TPM_LEFTALIGN,
                                pos[0],
                                pos[1],
                                0,
                                s.hwnd,
                                None)
        win32gui.PostMessage(s.hwnd, win32con.WM_NULL, 0, 0)

    def _add_ids_to_menu_options(s, menu_options):
        result = []
        for menu_option in menu_options:
            option_text, option_icon, option_action = menu_option
            if callable(option_action) or option_action in s.SPECIAL_ACTIONS:
                s.menu_actions_by_id.add((s._next_action_id, option_action))
                result.append(menu_option + (s._next_action_id,))
            else:
                result.append((option_text,
                               option_icon,
                               s._add_ids_to_menu_options(option_action),
                               s._next_action_id))
            s._next_action_id += 1
        return result

    def restart(s, hwnd, msg, wparam, lparam):
        s.refresh()

    def destroy(s, hwnd=None, msg=None, wparam=None, lparam=None, exit=1):
        nid = (s.hwnd, 0)
        win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
        win32gui.PostQuitMessage(0)  # 终止应用程序。
        if exit and s.on_quit:
            s.on_quit()  # 需要传递自身过去时用 s.on_quit(s)
        else:
            s.root.deiconify()  # 显示tk窗口

    def notify(s, hwnd, msg, wparam, lparam):
        '''鼠标事件'''
        if lparam == win32con.WM_LBUTTONDBLCLK:  # 双击左键
            pass
        elif lparam == win32con.WM_RBUTTONUP:  # 右键弹起
            s.show_menu()
        elif lparam == win32con.WM_LBUTTONUP:  # 左键弹起
            s.destroy(exit=0)
        return True
        """
        可能的鼠标事件：
          WM_MOUSEMOVE      #光标经过图标
          WM_LBUTTONDOWN    #左键按下
          WM_LBUTTONUP      #左键弹起
          WM_LBUTTONDBLCLK  #双击左键
          WM_RBUTTONDOWN    #右键按下
          WM_RBUTTONUP      #右键弹起
          WM_RBUTTONDBLCLK  #双击右键
          WM_MBUTTONDOWN    #滚轮按下
          WM_MBUTTONUP      #滚轮弹起
          WM_MBUTTONDBLCLK  #双击滚轮
        """

    def create_menu(s, menu, menu_options):
        for option_text, option_icon, option_action, option_id in menu_options[::-1]:
            if option_icon:
                option_icon = s.prep_menu_icon(option_icon)

            if option_id in s.menu_actions_by_id:
                item, extras = win32gui_struct.PackMENUITEMINFO(text=option_text,
                                                                hbmpItem=option_icon,
                                                                wID=option_id)
                win32gui.InsertMenuItem(menu, 0, 1, item)
            else:
                submenu = win32gui.CreatePopupMenu()
                s.create_menu(submenu, option_action)
                item, extras = win32gui_struct.PackMENUITEMINFO(text=option_text,
                                                                hbmpItem=option_icon,
                                                                hSubMenu=submenu)
                win32gui.InsertMenuItem(menu, 0, 1, item)

    def prep_menu_icon(s, icon):
        # 加载图标。
        ico_x = win32api.GetSystemMetrics(win32con.SM_CXSMICON)
        ico_y = win32api.GetSystemMetrics(win32con.SM_CYSMICON)
        hicon = win32gui.LoadImage(0, icon, win32con.IMAGE_ICON, ico_x, ico_y, win32con.LR_LOADFROMFILE)

        hdcBitmap = win32gui.CreateCompatibleDC(0)
        hdcScreen = win32gui.GetDC(0)
        hbm = win32gui.CreateCompatibleBitmap(hdcScreen, ico_x, ico_y)
        hbmOld = win32gui.SelectObject(hdcBitmap, hbm)
        brush = win32gui.GetSysColorBrush(win32con.COLOR_MENU)
        win32gui.FillRect(hdcBitmap, (0, 0, 16, 16), brush)
        win32gui.DrawIconEx(hdcBitmap, 0, 0, hicon, ico_x, ico_y, 0, 0, win32con.DI_NORMAL)
        win32gui.SelectObject(hdcBitmap, hbmOld)
        win32gui.DeleteDC(hdcBitmap)

        return hbm

    def command(s, hwnd, msg, wparam, lparam):
        id = win32gui.LOWORD(wparam)
        s.execute_menu_option(id)

    def execute_menu_option(s, id):
        menu_action = s.menu_actions_by_id[id]
        if menu_action == s.QUIT:
            win32gui.DestroyWindow(s.hwnd)
        else:
            menu_action(s)




