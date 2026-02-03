import unittest

import bmesh
import bpy
from nextools.logic.uv.straight import align_uv_straight


class TestStraightLogic(unittest.TestCase):
    def setUp(self):
        bpy.ops.wm.read_homefile(use_empty=True)
        self.bm = None

    def tearDown(self):
        if self.bm and self.bm.is_valid:
            self.bm.free()
        if bpy.context.active_object and bpy.context.active_object.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

    def _setup_mesh(self):
        # 2x2 grid
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=2, y_subdivisions=2, size=2)
        self.obj = bpy.context.active_object
        bpy.ops.object.mode_set(mode="EDIT")

        self.me = self.obj.data
        self.bm = bmesh.from_edit_mesh(self.me)
        self.bm.faces.ensure_lookup_table()
        self.bm.verts.ensure_lookup_table()
        self.bm.edges.ensure_lookup_table()
        self.uv_layer = self.bm.loops.layers.uv.verify()

    def test_straight_horizontal_edges(self):
        """
        Select nearly horizontal edges and run Straight, then verify they become perfectly horizontal (V coordinates match).
        """
        self._setup_mesh()
        bm = self.bm
        uv_layer = self.uv_layer

        # Select the center horizontal edges (Vertices 3, 4, 5)
        # Grid (x,y=2) has 9 vertices
        # 0 1 2
        # 3 4 5
        # 6 7 8

        # Get loops around vertex 4 and shift UVs
        target_verts = [bm.verts[3], bm.verts[4], bm.verts[5]]
        for v in target_verts:
            for loop in v.link_loops:
                loop.uv_select_vert = True
                # Shift UVs slightly up and down
                loop[uv_layer].uv.y += 0.1 if v.index == 4 else -0.05

        # Select edges
        for e in bm.edges:
            if all(v in target_verts for v in e.verts):
                for loop in e.link_loops:
                    loop.uv_select_edge = True

        bmesh.update_edit_mesh(self.me)

        success = align_uv_straight(bm, uv_layer.name)
        self.assertTrue(success)

        # Verify that V coordinates of all selected vertices match
        y_coords = []
        for face in bm.faces:
            for loop in face.loops:
                if loop.uv_select_vert:
                    y_coords.append(loop[uv_layer].uv.y)

        for y in y_coords:
            self.assertAlmostEqual(y, y_coords[0], places=5)

    def test_straight_vertical_edges(self):
        """
        Select nearly vertical edges and run Straight, then verify they become perfectly vertical (U coordinates match).
        """
        self._setup_mesh()
        bm = self.bm
        uv_layer = self.uv_layer

        # Select the center vertical edges (Vertices 1, 4, 7)
        target_verts = [bm.verts[1], bm.verts[4], bm.verts[7]]
        for v in target_verts:
            for loop in v.link_loops:
                loop.uv_select_vert = True
                # Shift UVs slightly left and right
                loop[uv_layer].uv.x += 0.1 if v.index == 4 else -0.05

        # Select edges
        for e in bm.edges:
            if all(v in target_verts for v in e.verts):
                for loop in e.link_loops:
                    loop.uv_select_edge = True

        bmesh.update_edit_mesh(self.me)

        success = align_uv_straight(bm, uv_layer.name)
        self.assertTrue(success)

        # Verify that U coordinates of all selected vertices match
        x_coords = []
        for face in bm.faces:
            for loop in face.loops:
                if loop.uv_select_vert:
                    x_coords.append(loop[uv_layer].uv.x)

        for x in x_coords:
            self.assertAlmostEqual(x, x_coords[0], places=5)


if __name__ == "__main__":
    unittest.main(argv=["ignored", "-v"])
