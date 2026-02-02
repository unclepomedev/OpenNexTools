# SPDX-License-Identifier: GPL-3.0-or-later

import bmesh
import bpy
from nextools.logic.uv.rectify import align_uv_rectify
from nextools.logic.uv.straight import align_uv_straight


class UV_OT_NextoolsLiteRectify(bpy.types.Operator):
    """Rectify: Unwraps selected faces into a grid"""

    bl_idname = "uv.nextools_rectify"
    bl_label = "Rectify"
    bl_options = {"REGISTER", "UNDO"}

    keep_bounds: bpy.props.BoolProperty(
        name="Keep Bounds",
        description="Scale the rectified UV island to match its original bounding box",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == "MESH" and obj.mode == "EDIT"

    def execute(self, context):
        obj = context.active_object
        me = obj.data
        bm = bmesh.from_edit_mesh(me)

        uv_layer_name = me.uv_layers.active.name if me.uv_layers.active else None
        if not uv_layer_name:
            self.report({"ERROR"}, "No UV Map found")
            return {"CANCELLED"}

        # Use settings if the operator is called from UI (no property set)
        if not self.properties.is_property_set("keep_bounds"):
            self.keep_bounds = context.scene.nextools_settings.rectify_keep_bounds

        try:
            success = align_uv_rectify(obj, bm, uv_layer_name, keep_bounds=self.keep_bounds)
            if not success:
                self.report({"WARNING"}, "Select connected Quad faces.")
                return {"CANCELLED"}
        except Exception as e:
            self.report({"ERROR"}, f"Rectify Error: {str(e)}")
            import traceback

            traceback.print_exc()
            return {"CANCELLED"}

        return {"FINISHED"}


class UV_OT_NextoolsStraight(bpy.types.Operator):
    """Straight: Straighten selected edges, or rectify if faces are selected"""

    bl_idname = "uv.nextools_straight"
    bl_label = "Straight"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == "MESH" and obj.mode == "EDIT"

    def execute(self, context):
        obj = context.active_object
        me = obj.data
        bm = bmesh.from_edit_mesh(me)

        uv_layer_name = me.uv_layers.active.name if me.uv_layers.active else None
        if not uv_layer_name:
            self.report({"ERROR"}, "No UV Map found")
            return {"CANCELLED"}

        selected_faces = [f for f in bm.faces if f.select]

        if selected_faces:
            keep_bounds = context.scene.nextools_settings.rectify_keep_bounds
            success = align_uv_rectify(obj, bm, uv_layer_name, keep_bounds=keep_bounds)
            if not success:
                self.report({"WARNING"}, "Rectify failed. Select connected Quad faces.")
                return {"CANCELLED"}
        else:
            success = align_uv_straight(bm, uv_layer_name)
            if not success:
                self.report({"WARNING"}, "Straighten failed. Select UV edges.")
                return {"CANCELLED"}

        bmesh.update_edit_mesh(me)
        return {"FINISHED"}
