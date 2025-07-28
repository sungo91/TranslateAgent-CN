
"""
@File    : print_structure.py.py
@Project : TranslateAgent-CN
@Author  : SunGo
@Date    : 2025/7/28 21:43
"""

import os
from pathlib import Path

def print_directory_tree(root_dir, prefix="", is_last=True):
    root_path = Path(root_dir)
    print(prefix + ("└── " if is_last else "├── ") + root_path.name)

    if root_path.is_dir():
        children = sorted(root_path.iterdir(), key=lambda x: (x.is_file(), x.name))
        children = [c for c in children if not c.name.startswith('.')]  # 忽略隐藏文件/目录

        for i, child in enumerate(children):
            is_last_child = (i == len(children) - 1)
            extension = "    " if is_last else "│   "
            print_directory_tree(child, prefix + extension, is_last_child)

if __name__ == "__main__":
    project_root = "."  # 当前目录作为根
    print_directory_tree(project_root)