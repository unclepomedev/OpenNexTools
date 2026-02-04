# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
import bpy
from nextools.logic.uv_morph import (
    ensure_uv_morph_node_group,
    toggle_uv_morph_modifier,
    execute_bake_process,
    set_modifier_factor,
    MOD_NAME,
)


class TestUVMorphLogic(unittest.TestCase):
    def setUp(self):
        bpy.ops.wm.read_homefile(use_empty=True)

    def tearDown(self):
        pass

    def test_ensure_uv_morph_node_group_creation(self):
        """
        Verify that ensure_uv_morph_node_group creates a new node group
        if it doesn't exist.
        """
        if "NT_UV_Morph" in bpy.data.node_groups:
            bpy.data.node_groups.remove(bpy.data.node_groups["NT_UV_Morph"])

        ng = ensure_uv_morph_node_group()

        self.assertIsNotNone(ng)
        self.assertEqual(ng.name, "NT_UV_Morph")
        self.assertEqual(ng.bl_idname, "GeometryNodeTree")
        self.assertIn("NT_UV_Morph", bpy.data.node_groups)

    def test_ensure_uv_morph_node_group_idempotency(self):
        """
        Verify that calling the function twice returns the same object
        and doesn't create duplicates.
        """
        ng1 = ensure_uv_morph_node_group()
        ng2 = ensure_uv_morph_node_group()

        self.assertEqual(ng1, ng2)
        self.assertEqual(ng1.name, ng2.name)

        count = sum(1 for g in bpy.data.node_groups if g.name.startswith("NT_UV_Morph"))
        self.assertEqual(count, 1)

    def test_node_group_structure(self):
        """
        Verify the internal structure of the generated node group.
        It must contain specific nodes and interface sockets.
        """
        ng = ensure_uv_morph_node_group()

        inputs = [
            s.name
            for s in ng.interface.items_tree
            if s.item_type == "SOCKET" and s.in_out == "INPUT"
        ]
        outputs = [
            s.name
            for s in ng.interface.items_tree
            if s.item_type == "SOCKET" and s.in_out == "OUTPUT"
        ]

        self.assertIn("Geometry", inputs)
        self.assertIn("Factor", inputs)
        self.assertIn("UV Map", inputs)
        self.assertIn("Geometry", outputs)

        node_types = [node.bl_idname for node in ng.nodes]
        required_nodes = [
            "NodeGroupInput",
            "NodeGroupOutput",
            "GeometryNodeSplitEdges",
            "GeometryNodeInputNamedAttribute",
            "GeometryNodeInputPosition",
            "ShaderNodeMix",
            "GeometryNodeSetPosition",
        ]

        for node_type in required_nodes:
            self.assertIn(node_type, node_types, f"Node type {node_type} missing in graph")

    def test_node_connections(self):
        """
        Verify critical links exist in the node graph.
        """
        ng = ensure_uv_morph_node_group()
        links = ng.links

        def link_exists(from_node_type, to_node_type):
            for link in links:
                if (
                    link.from_node.bl_idname == from_node_type
                    and link.to_node.bl_idname == to_node_type
                ):
                    return True
            return False

        self.assertTrue(link_exists("NodeGroupInput", "GeometryNodeSplitEdges"))
        self.assertTrue(link_exists("GeometryNodeSplitEdges", "GeometryNodeSetPosition"))
        self.assertTrue(link_exists("GeometryNodeSetPosition", "NodeGroupOutput"))
        self.assertTrue(link_exists("ShaderNodeMix", "GeometryNodeSetPosition"))


class TestUVMorphBake(unittest.TestCase):
    def setUp(self):
        bpy.ops.wm.read_homefile(use_empty=True)
        bpy.ops.mesh.primitive_plane_add(size=2, enter_editmode=False)
        self.obj = bpy.context.active_object
        # Add UV Map
        if not self.obj.data.uv_layers:
            self.obj.data.uv_layers.new(name="UVMap")
        toggle_uv_morph_modifier(self.obj)

    def tearDown(self):
        pass

    def test_set_modifier_factor(self):
        """
        Verify that set_modifier_factor updates the modifier input without error.
        """
        mod = self.obj.modifiers[MOD_NAME]
        set_modifier_factor(mod, 0.5)

        # Verification: check if any property in the modifier corresponds to 0.5
        found = False
        for k, v in mod.items():
            if isinstance(v, float) and abs(v - 0.5) < 1e-6:
                found = True
                break
        self.assertTrue(found, "Factor value 0.5 not found in modifier properties")

    def test_bake_process_execution(self):
        """
        Verify that execute_bake_process creates a new object with Shape Keys.
        """
        if bpy.context.object and bpy.context.object.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

        baked_obj = execute_bake_process(bpy.context, self.obj)

        self.assertIsNotNone(baked_obj)
        self.assertTrue(baked_obj.name.startswith("Plane_Baked"))

        self.assertIsNotNone(baked_obj.data.shape_keys)
        key_blocks = baked_obj.data.shape_keys.key_blocks
        self.assertIn("Basis", key_blocks)
        self.assertIn("UV_Morph", key_blocks)

        self.assertIn(self.obj.name, bpy.data.objects)


if __name__ == "__main__":
    unittest.main()
