import unittest

import bmesh
import bpy
from mathutils import Vector
from nextools.logic.uv.rectify import align_uv_rectify


class TestRectifyLogic(unittest.TestCase):
    def setUp(self):
        bpy.ops.wm.read_homefile(use_empty=True)
        self.bm = None

    def tearDown(self):
        if self.bm and self.bm.is_valid:
            self.bm.free()
        if bpy.context.active_object and bpy.context.active_object.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

    def _setup_mesh(self, mesh_type="QUAD"):
        if mesh_type == "QUAD":
            bpy.ops.mesh.primitive_plane_add(size=2, enter_editmode=False, align="WORLD")
        elif mesh_type == "TRIANGLE":
            bpy.ops.mesh.primitive_circle_add(vertices=3, fill_type="NGON", enter_editmode=False)

        self.obj = bpy.context.active_object
        self.obj.name = "TestObj"
        bpy.ops.object.mode_set(mode="EDIT")

        self.me = self.obj.data
        self.bm = bmesh.from_edit_mesh(self.me)
        self.bm.faces.ensure_lookup_table()
        self.bm.verts.ensure_lookup_table()
        self.uv_layer = self.bm.loops.layers.uv.verify()

    def test_rectify_distorted_quad(self):
        """
        Verify that a distorted quad UV is rectified into a normalized (0-1) square.
        """
        self._setup_mesh("QUAD")
        bm = self.bm
        uv_layer = self.uv_layer

        face = bm.faces[0]
        face.select = True

        distorted_uvs = [(0.2, 0.1), (0.9, 0.3), (0.8, 0.8), (0.1, 0.9)]

        for loop, uv_coord in zip(face.loops, distorted_uvs, strict=True):
            loop[uv_layer].uv = uv_coord

        bmesh.update_edit_mesh(self.me)
        success = align_uv_rectify(self.obj, bm, uv_layer.name)
        self.assertTrue(success)

        bpy.ops.object.mode_set(mode="OBJECT")

        uv_coords = [Vector(d.uv) for d in self.me.uv_layers.active.data]
        xs = [uv.x for uv in uv_coords]
        ys = [uv.y for uv in uv_coords]

        self.assertAlmostEqual(max(xs) - min(xs), 1.0, places=4)
        self.assertAlmostEqual(max(ys) - min(ys), 1.0, places=4)

    def test_rectify_mixed_selection_priority(self):
        """
        Verify that Quads are prioritized as the active face over Triangles in mixed selection.
        """
        bpy.ops.mesh.primitive_plane_add(size=2, enter_editmode=False)  # Quad
        obj = bpy.context.active_object

        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.subdivide()
        bpy.ops.mesh.select_all(action="DESELECT")

        me = obj.data
        bm = bmesh.from_edit_mesh(me)
        bm.faces.ensure_lookup_table()
        self.bm = bm

        bmesh.ops.triangulate(bm, faces=[bm.faces[0]])
        bm.faces.ensure_lookup_table()

        tri_face = [f for f in bm.faces if len(f.verts) == 3][0]
        quad_face = [f for f in bm.faces if len(f.verts) == 4][0]

        tri_face.select = True
        quad_face.select = True

        bm.faces.active = tri_face

        uv_layer = bm.loops.layers.uv.verify()
        bmesh.update_edit_mesh(me)

        success = align_uv_rectify(obj, bm, uv_layer.name)
        self.assertTrue(success)

        bpy.ops.object.mode_set(mode="OBJECT")

        uv_data = [d.uv for d in me.uv_layers.active.data]
        xs = [uv[0] for uv in uv_data]
        ys = [uv[1] for uv in uv_data]

        self.assertAlmostEqual(max(xs) - min(xs), 1.0, places=3)
        self.assertAlmostEqual(max(ys) - min(ys), 1.0, places=3)

    def test_rectify_keep_bounds(self):
        """
        Verify that Rectify with keep_bounds=True maintains the original bounding box.
        """
        self._setup_mesh("QUAD")
        bm = self.bm
        uv_layer = self.uv_layer

        face = bm.faces[0]
        face.select = True

        # Original bounds: (0.2, 0.1) to (0.9, 0.9)
        distorted_uvs = [(0.2, 0.1), (0.9, 0.3), (0.8, 0.9), (0.3, 0.8)]
        orig_min_x, orig_max_x = 0.2, 0.9
        orig_min_y, orig_max_y = 0.1, 0.9

        for loop, uv_coord in zip(face.loops, distorted_uvs, strict=True):
            loop[uv_layer].uv = uv_coord

        bmesh.update_edit_mesh(self.me)
        success = align_uv_rectify(self.obj, bm, uv_layer.name, keep_bounds=True)
        self.assertTrue(success)

        bpy.ops.object.mode_set(mode="OBJECT")

        uv_coords = [Vector(d.uv) for d in self.me.uv_layers.active.data]
        xs = [uv.x for uv in uv_coords]
        ys = [uv.y for uv in uv_coords]

        self.assertAlmostEqual(min(xs), orig_min_x, places=4)
        self.assertAlmostEqual(max(xs), orig_max_x, places=4)
        self.assertAlmostEqual(min(ys), orig_min_y, places=4)
        self.assertAlmostEqual(max(ys), orig_max_y, places=4)


if __name__ == "__main__":
    unittest.main()
