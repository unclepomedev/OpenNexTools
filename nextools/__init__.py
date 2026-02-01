# SPDX-License-Identifier: GPL-3.0-or-later

from .ops import uv
from .ops import color_id
from .ui import panel
import bpy

_classes = [
    uv.UV_OT_NextoolsLiteRectify,
    color_id.UV_OT_NextoolsBakeColorID,
    panel.UV_PT_NextoolsPanel,
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
