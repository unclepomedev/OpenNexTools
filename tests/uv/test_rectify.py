import unittest

import bmesh
import bpy
from mathutils import Vector
from nextools.logic.uv.rectify import align_uv_rectify


class TestRectifyLogic(unittest.TestCase):
    def setUp(self):
        bpy.ops.wm.read_homefile(use_empty=True)

        bpy.ops.mesh.primitive_plane_add(size=2, enter_editmode=False, align="WORLD")
        self.obj = bpy.context.active_object
        self.obj.name = "TestQuad"
        bpy.ops.object.mode_set(mode="EDIT")

        self.me = self.obj.data
        self.bm = bmesh.from_edit_mesh(self.me)

        self.bm.faces.ensure_lookup_table()
        self.bm.verts.ensure_lookup_table()

        self.uv_layer = self.bm.loops.layers.uv.verify()

    def tearDown(self):
        if self.bm:
            self.bm.free()

    def test_rectify_distorted_quad(self):
        """
        Verify that a distorted quad UV is rectified into a normalized (0-1) square.
        """
        bm = self.bm
        uv_layer = self.uv_layer

        face = bm.faces[0]
        face.select = True

        distorted_uvs = [(0.2, 0.1), (0.9, 0.3), (0.8, 0.8), (0.1, 0.9)]

        for loop, uv_coord in zip(face.loops, distorted_uvs):
            loop[uv_layer].uv = uv_coord

        bmesh.update_edit_mesh(self.me)
        success = align_uv_rectify(self.obj, bm, uv_layer.name)
        self.assertTrue(success, "Rectify function should return True")
        bpy.ops.object.mode_set(mode="OBJECT")

        uv_coords = []
        for loop in self.me.polygons[0].loop_indices:
            uv = self.me.uv_layers.active.data[loop].uv
            uv_coords.append(Vector(uv))

        for uv in uv_coords:
            self.assertTrue(0.0 <= uv.x <= 1.0)
            self.assertTrue(0.0 <= uv.y <= 1.0)

        xs = [uv.x for uv in uv_coords]
        ys = [uv.y for uv in uv_coords]

        width = max(xs) - min(xs)
        height = max(ys) - min(ys)

        self.assertAlmostEqual(width, 1.0, places=4, msg="Width should be 1.0")
        self.assertAlmostEqual(height, 1.0, places=4, msg="Height should be 1.0")


if __name__ == "__main__":
    unittest.main()
