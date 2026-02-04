# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from nextools.logic import uv_morph as logic_uv_morph


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
        mod_name = logic_uv_morph.MOD_NAME

        if mod_name in obj.modifiers:
            obj.modifiers.remove(obj.modifiers[mod_name])
            self.report({"INFO"}, "UV Morph: OFF")
            return {"FINISHED"}

        ng = logic_uv_morph.ensure_uv_morph_node_group()

        mod = obj.modifiers.new(name=mod_name, type="NODES")
        mod.node_group = ng
        mod.show_on_cage = True
        mod.show_in_editmode = True

        active_uv = obj.data.uv_layers.active
        if active_uv:
            mod["UV Map"] = active_uv.name

        self.report({"INFO"}, "UV Morph: ON")
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
        return obj and obj.type == "MESH" and "NT_UV_Morph" in obj.modifiers

    def execute(self, context):
        original_obj = context.active_object
        mod_name = "NT_UV_Morph"

        target_area = next((a for a in context.screen.areas if a.type == "VIEW_3D"), None)
        if not target_area:
            self.report({"ERROR"}, "3D Viewport not found")
            return {"CANCELLED"}

        try:
            with context.temp_override(area=target_area):
                if context.mode != "OBJECT":
                    bpy.ops.object.mode_set(mode="OBJECT")

                # A. Create Basis object
                bpy.ops.object.select_all(action="DESELECT")
                original_obj.select_set(True)
                context.view_layer.objects.active = original_obj

                bpy.ops.object.duplicate()
                basis_obj = context.active_object
                basis_obj.name = f"{original_obj.name}_Baked"

                mod = basis_obj.modifiers[mod_name]
                logic_uv_morph.set_modifier_factor(mod, 0.0)
                bpy.ops.object.modifier_apply(modifier=mod_name)

                # B. Create Target object (Key 1)
                bpy.ops.object.select_all(action="DESELECT")
                original_obj.select_set(True)
                context.view_layer.objects.active = original_obj

                bpy.ops.object.duplicate()
                target_obj = context.active_object

                mod = target_obj.modifiers[mod_name]
                logic_uv_morph.set_modifier_factor(mod, 1.0)
                bpy.ops.object.modifier_apply(modifier=mod_name)

                # C. Join as Shape Keys
                bpy.ops.object.select_all(action="DESELECT")
                target_obj.select_set(True)
                basis_obj.select_set(True)
                context.view_layer.objects.active = basis_obj

                bpy.ops.object.join_shapes()

                if basis_obj.data.shape_keys:
                    keys = basis_obj.data.shape_keys.key_blocks
                    keys[-1].name = "UV_Morph"
                    keys[-1].value = 0.0

                # D. Cleanup
                bpy.ops.object.select_all(action="DESELECT")
                target_obj.select_set(True)
                bpy.ops.object.delete()

                bpy.ops.object.select_all(action="DESELECT")
                basis_obj.select_set(True)
                context.view_layer.objects.active = basis_obj

            self.report({"INFO"}, f"Baked to '{basis_obj.name}'")
            return {"FINISHED"}

        except Exception as e:
            import traceback

            traceback.print_exc()
            self.report({"ERROR"}, f"Bake failed: {str(e)}")
            return {"CANCELLED"}
