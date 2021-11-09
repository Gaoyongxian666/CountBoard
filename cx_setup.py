# Based on https://github.com/marcelotduarte/cx_Freeze/blob/main/cx_Freeze/samples/Tkinter/setup.py
#
# A simple setup script to create an executable using Tkinter. This also
# demonstrates the method for creating a Windows executable that does not have
# an associated console.

import sys
from cx_Freeze import setup, Executable

from pathlib import Path
icon_path = Path('favicon.ico')

base = None
if sys.platform == "win32":
    base = "Win32GUI"

executables = [Executable("Main_window.py", base=base)]

options = {
    'build_exe': {
        'include_files': [
            icon_path
        ],  # additional plugins needed by qt at runtime
        'zip_include_packages': [
            'encodings',
            'markdown2',
            'PIL',
            'sqlitedict',
            'tkhtmlview'
        ],  # reduce size of packages that are used
        'excludes': [
            'unittest',
            'pydoc',
            'pdb'
        ]
    }
}

setup(
    name="CountBoard",
    version="1.1.0.2",
    description="CountBoard 是一个基于 Tkinter 简单的，开源的桌面日程倒计时应用。",
    executables=executables,
    options=options
)