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
