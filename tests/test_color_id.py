import unittest
import bpy
import bmesh
from nextools.logic.color_id import apply_color_id_to_mesh


class TestColorIDLogic(unittest.TestCase):
    def setUp(self):
        bpy.ops.wm.read_homefile(use_empty=True)

    def tearDown(self):
        if bpy.context.active_object and bpy.context.active_object.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

    def _setup_mesh(self, mesh_type="CUBE"):
        if mesh_type == "CUBE":
            bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False)
        elif mesh_type == "PLANE":
            bpy.ops.mesh.primitive_plane_add(size=2, enter_editmode=False)

        obj = bpy.context.active_object
        obj.name = "TestObj"
        return obj

    def test_apply_color_id_basic_cube(self):
        """Test basic Color ID application on a Cube."""
        obj = self._setup_mesh("CUBE")
        mesh = obj.data

        count = apply_color_id_to_mesh(obj)

        self.assertEqual(count, 6)
        self.assertIn("Color_ID", mesh.color_attributes)

        # Verify attribute settings
        color_layer = mesh.color_attributes["Color_ID"]
        self.assertEqual(color_layer.domain, "CORNER")
        self.assertEqual(color_layer.data_type, "BYTE_COLOR")

        # Verify data integrity
        sample_color = color_layer.data[0].color
        self.assertEqual(len(sample_color), 4)
        self.assertAlmostEqual(sample_color[3], 1.0)

    def test_error_non_mesh_object(self):
        """Ensure ValueError is raised for non-mesh objects."""
        bpy.ops.object.camera_add()
        cam = bpy.context.active_object

        with self.assertRaises(ValueError) as cm:
            apply_color_id_to_mesh(cam)

        self.assertIn("must be a MESH", str(cm.exception))

    def test_error_no_uv_layer(self):
        """Ensure ValueError is raised for meshes without UV layers."""
        obj = self._setup_mesh("PLANE")

        while obj.data.uv_layers:
            obj.data.uv_layers.remove(obj.data.uv_layers[0])

        with self.assertRaises(ValueError) as cm:
            apply_color_id_to_mesh(obj)

        self.assertIn("Active UV layer is required", str(cm.exception))

    def test_complex_uv_islands(self):
        """Verify execution with split UV islands (seams)."""
        obj = self._setup_mesh("CUBE")

        # Force split UVs using Smart UV Project
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.0)
        bpy.ops.object.mode_set(mode="OBJECT")

        count = apply_color_id_to_mesh(obj)

        self.assertEqual(count, 6)
        self.assertEqual(len(obj.data.color_attributes["Color_ID"].data), len(obj.data.loops))


if __name__ == "__main__":
    unittest.main()
