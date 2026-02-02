# SPDX-License-Identifier: GPL-3.0-or-later

from .ops import uv
from .ops import color_id
from .ui import panel
import bpy


class NextoolsSettings(bpy.types.PropertyGroup):
    rectify_keep_bounds: bpy.props.BoolProperty(
        name="Keep Bounds",
        description="Scale the rectified UV island to match its original bounding box",
        default=True,
    )


_classes = [
    NextoolsSettings,
    uv.UV_OT_NextoolsLiteRectify,
    color_id.UV_OT_NextoolsBakeColorID,
    panel.UV_PT_NextoolsPanel,
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.nextools_settings = bpy.props.PointerProperty(type=NextoolsSettings)


def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.nextools_settings
