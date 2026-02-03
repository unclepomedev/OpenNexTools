# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from nextools.ops.uv import UV_OT_nextools_lite_rectify, UV_OT_nextools_straight
from nextools.ops.color_id import UV_OT_nextools_bake_color_id


class UV_PT_nextools_panel(bpy.types.Panel):
    bl_label = "NexTools"
    bl_idname = "UV_PT_nextools"
    bl_space_type = "IMAGE_EDITOR"
    bl_region_type = "UI"
    bl_category = "NexTools"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        row = col.row(align=True)
        row.operator(UV_OT_nextools_straight.bl_idname, text="Straight", icon="IPO_LINEAR")
        row.operator(UV_OT_nextools_lite_rectify.bl_idname, text="Rectify", icon="GRID")
        row.prop(
            context.scene.nextools_settings, "rectify_keep_bounds", text="", icon="PIVOT_BOUNDBOX"
        )

        col.separator()
        col.label(text="Baking")
        col.operator(UV_OT_nextools_bake_color_id.bl_idname, text="Color ID", icon="GROUP_VCOL")
