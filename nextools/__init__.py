# SPDX-License-Identifier: GPL-3.0-or-later

from . import operators
from .ops import uv
from .ui import panel
import bpy

_classes = [
    uv.UV_OT_NextoolsLiteRectify,
    panel.UV_PT_NextoolsPanel
]

_modules = [
    operators,
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    for mod in _modules:
        mod.register()


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
    for mod in reversed(_modules):
        mod.unregister()
