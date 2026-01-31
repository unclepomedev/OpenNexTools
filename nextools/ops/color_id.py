# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from ..logic import color_id as logic_color_id


class UV_OT_NextoolsBakeColorID(bpy.types.Operator):
    """Bake Color ID Map using Rust (High Performance)"""

    bl_idname = "uv.nextools_bake_color_id"
    bl_label = "Bake Color ID"
    bl_options = {"REGISTER", "UNDO"}

    auto_switch_view: bpy.props.BoolProperty(
        name="Auto Switch View",
        description="Automatically switch 3D viewport to show Color ID attribute",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == "MESH" and obj.data.uv_layers.active

    def execute(self, context):
        obj = context.active_object
        original_mode = obj.mode

        if original_mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

        try:
            processed_count = logic_color_id.apply_color_id_to_mesh(obj)

            if self.auto_switch_view:
                self._switch_viewport_shading(context, "Color_ID")

            self.report({"INFO"}, f"Color ID Baked: {processed_count} faces processed.")
            return {"FINISHED"}

        except ValueError as e:
            self.report({"WARNING"}, str(e))
            return {"CANCELLED"}

        except RuntimeError as e:
            self.report({"ERROR"}, str(e))
            return {"CANCELLED"}

        finally:
            if original_mode != "OBJECT" and obj:
                try:
                    bpy.ops.object.mode_set(mode=original_mode)
                except Exception:
                    pass

    def _switch_viewport_shading(self, context, attr_name):
        if not context.screen:
            return
        for area in context.screen.areas:
            if area.type == "VIEW_3D":
                for space in area.spaces:
                    if space.type == "VIEW_3D":
                        shading = space.shading
                        shading.type = "SOLID"
                        shading.color_type = "VERTEX"
                        area.tag_redraw()
