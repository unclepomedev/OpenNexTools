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
    uv.UV_OT_nextools_lite_rectify,
    uv.UV_OT_nextools_straight,
    color_id.UV_OT_nextools_bake_color_id,
    panel.UV_PT_nextools_panel,
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.nextools_settings = bpy.props.PointerProperty(type=NextoolsSettings)


def unregister():
    if hasattr(bpy.types.Scene, "nextools_settings"):
        del bpy.types.Scene.nextools_settings
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
