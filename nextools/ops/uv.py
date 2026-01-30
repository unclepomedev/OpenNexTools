# SPDX-License-Identifier: GPL-3.0-or-later

import bmesh
import bpy
from nextools.logic.uv.rectify import align_uv_rectify


class UV_OT_NextoolsLiteRectify(bpy.types.Operator):
    """Rectify: Unwraps selected faces into a grid"""
    bl_idname = "uv.nextools_rectify"
    bl_label = "Rectify"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and obj.mode == 'EDIT'

    def execute(self, context):
        obj = context.active_object
        me = obj.data
        bm = bmesh.from_edit_mesh(me)

        uv_layer_name = me.uv_layers.active.name if me.uv_layers.active else None
        if not uv_layer_name:
            self.report({'ERROR'}, "No UV Map found")
            return {'CANCELLED'}

        try:
            success = align_uv_rectify(obj, bm, uv_layer_name)
            if not success:
                self.report({'WARNING'}, "Select connected Quad faces.")
                return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"Rectify Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}

        return {'FINISHED'}
