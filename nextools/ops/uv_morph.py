# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from nextools.logic import uv_morph as logic_uv_morph
from nextools.logic.uv_morph import MOD_NAME


class UV_OT_nextools_uv_morph(bpy.types.Operator):
    """Toggle UV Morph Modifier (Real-time UV Visualization)"""

    bl_idname = "uv.nextools_uv_morph"
    bl_label = "UV Morph"
    bl_description = "Toggle real-time transformation from 3D mesh to UV layout"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == "MESH"

    def execute(self, context):
        obj = context.active_object
        is_added = logic_uv_morph.toggle_uv_morph_modifier(obj)
        if is_added:
            self.report({"INFO"}, "UV Morph: ON")
        else:
            self.report({"INFO"}, "UV Morph: OFF")

        return {"FINISHED"}


class UV_OT_nextools_bake_morph(bpy.types.Operator):
    """Bake UV Morph to a new mesh with Shape Keys (for export)"""

    bl_idname = "uv.nextools_bake_morph"
    bl_label = "Bake to Shape Key"
    bl_description = "Create a new mesh object with UV Morph baked as a Shape Key"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == "MESH" and MOD_NAME in obj.modifiers

    def execute(self, context):
        original_obj = context.active_object

        target_area = next((a for a in context.screen.areas if a.type == "VIEW_3D"), None)
        if not target_area:
            self.report({"ERROR"}, "3D Viewport not found")
            return {"CANCELLED"}

        try:
            with context.temp_override(area=target_area):
                if context.mode != "OBJECT":
                    bpy.ops.object.mode_set(mode="OBJECT")

                basis_obj = logic_uv_morph.execute_bake_process(context, original_obj)

            self.report({"INFO"}, f"Baked to '{basis_obj.name}'")
            return {"FINISHED"}

        except Exception as e:
            import traceback

            traceback.print_exc()
            self.report({"ERROR"}, f"Bake failed: {str(e)}")
            return {"CANCELLED"}
