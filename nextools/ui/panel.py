# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from nextools.ops.uv import UV_OT_NextoolsLiteRectify


class UV_PT_NextoolsPanel(bpy.types.Panel):
    bl_label = "NexTools"
    bl_idname = "UV_PT_nextools"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "NexTools"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        col.operator(UV_OT_NextoolsLiteRectify.bl_idname, text="Rectify", icon='GRID')
