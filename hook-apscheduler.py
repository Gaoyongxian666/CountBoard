# -*- coding: UTF-8 -*-
"""
@Project ：CountBoard
@File ：hooks-apscheduler.py
@Author ：Gao yongxian
@Date ：2021/12/2 13:02
@contact: g1695698547@163.com
"""
"""apscheduler 3.6.3"""
# hooks-a.py 不能被检索到是？

from PyInstaller.utils.hooks import collect_submodules, copy_metadata, collect_all

datas = copy_metadata('apscheduler', recursive=True)
hiddenimports = collect_submodules('apscheduler')



