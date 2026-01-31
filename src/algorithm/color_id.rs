// SPDX-License-Identifier: GPL-3.0-or-later

use crate::algorithm::dsu::Dsu;
use std::collections::{HashMap, HashSet};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
struct EdgeKey {
    min: usize,
    max: usize,
}

impl EdgeKey {
    fn new(v1: usize, v2: usize) -> Self {
        if v1 < v2 {
            Self { min: v1, max: v2 }
        } else {
            Self { min: v2, max: v1 }
        }
    }
}

/// Information of a face sharing an edge
#[derive(Debug, Clone, Copy)]
struct FaceEdgeRef {
    face_idx: usize,
    loop_curr: usize,
    loop_next: usize,
}

/// Key: EdgeKey (v_min, v_max)
/// Value: List of faces sharing that edge
type EdgeMap = HashMap<EdgeKey, Vec<FaceEdgeRef>>;

/// Calculates Color ID based on mesh data passed from Blender
///
/// Arguments:
/// - num_faces: Number of polygons
/// - poly_loop_starts: Loop start index for each polygon (foreach_get("loop_start"))
/// - poly_loop_totals: Number of loops for each polygon (foreach_get("loop_total"))
/// - loop_vert_indices: Vertex indices per loop (foreach_get("vertex_index"))
/// - uv_coords: Flat array of UV coordinates [u, v, u, v, ...]
///
/// Returns:
/// - Vec<f32>: Flat array of [r, g, b, a, r, g, b, a, ...] (for Vertex Color)
pub fn bake_color_id_all(
    num_faces: usize,
    poly_loop_starts: Vec<usize>,
    poly_loop_totals: Vec<usize>,
    loop_vert_indices: Vec<usize>,
    uv_coords: Vec<f32>,
) -> Vec<f32> {
    let edge_map: EdgeMap = build_edge_map(
        num_faces,
        &poly_loop_starts,
        &poly_loop_totals,
        &loop_vert_indices,
    );

    let (mut dsu, island_connections) =
        detect_uv_islands(num_faces, &edge_map, &loop_vert_indices, &uv_coords);

    let (adjacency, all_islands) = build_adjacency_graph(num_faces, &mut dsu, island_connections);

    let island_color_indices = color_graph(&adjacency, all_islands);

    generate_result_colors(
        num_faces,
        loop_vert_indices.len(),
        &poly_loop_starts,
        &poly_loop_totals,
        &mut dsu,
        &island_color_indices,
    )
}

#[inline]
fn is_uv_equal(u1: f32, v1: f32, u2: f32, v2: f32) -> bool {
    const EPSILON: f32 = 1e-4;
    (u1 - u2).abs() < EPSILON && (v1 - v2).abs() < EPSILON
}

/// h: 0.0 - 1.0, s: 0.0 - 1.0, v: 0.0 - 1.0
fn hsv_to_rgb(h: f32, s: f32, v: f32) -> (f32, f32, f32) {
    let h_i = (h * 6.0) as i32;
    let f = h * 6.0 - h_i as f32;
    let p = v * (1.0 - s);
    let q = v * (1.0 - f * s);
    let t = v * (1.0 - (1.0 - f) * s);

    match h_i % 6 {
        0 => (v, t, p),
        1 => (q, v, p),
        2 => (p, v, t),
        3 => (p, q, v),
        4 => (t, p, v),
        _ => (v, p, q),
    }
}

/// Generates a highly visible color from an index using the Golden Angle
/// Inverse Golden Ratio Conjugate ≒ 0.618034
fn get_golden_ratio_color(index: usize) -> (f32, f32, f32, f32) {
    let h = (index as f32 * 0.618_034) % 1.0;
    let (r, g, b) = hsv_to_rgb(h, 0.85, 0.95);
    (r, g, b, 1.0) // Alpha = 1.0
}

/// Topology Analysis (Build Edge Map)
/// (min_vert_idx, max_vert_idx) -> List of (FaceIndex, LoopIndexA, LoopIndexB)
/// Collects information of faces sharing edges
fn build_edge_map(
    num_faces: usize,
    poly_loop_starts: &[usize],
    poly_loop_totals: &[usize],
    loop_vert_indices: &[usize],
) -> EdgeMap {
    let mut edge_map: EdgeMap = HashMap::with_capacity(num_faces * 3);

    for f_idx in 0..num_faces {
        let start = poly_loop_starts[f_idx];
        let total = poly_loop_totals[f_idx];

        for i in 0..total {
            let loop_curr = start + i;
            let loop_next = start + (i + 1) % total;

            let v1 = loop_vert_indices[loop_curr];
            let v2 = loop_vert_indices[loop_next];

            let key = EdgeKey::new(v1, v2);

            edge_map.entry(key).or_default().push(FaceEdgeRef {
                face_idx: f_idx,
                loop_curr,
                loop_next,
            });
        }
    }
    edge_map
}

fn get_sorted_uvs(
    loop_curr: usize,
    loop_next: usize,
    loop_vert_indices: &[usize],
    uv_coords: &[f32],
) -> ((f32, f32), (f32, f32)) {
    if loop_vert_indices[loop_curr] < loop_vert_indices[loop_next] {
        (
            (uv_coords[loop_curr * 2], uv_coords[loop_curr * 2 + 1]),
            (uv_coords[loop_next * 2], uv_coords[loop_next * 2 + 1]),
        )
    } else {
        (
            (uv_coords[loop_next * 2], uv_coords[loop_next * 2 + 1]),
            (uv_coords[loop_curr * 2], uv_coords[loop_curr * 2 + 1]),
        )
    }
}

/// Detect UV Islands (Union-Find)
/// Initially assume all faces are separate islands
/// Returns: (Dsu, island_connections)
fn detect_uv_islands(
    num_faces: usize,
    edge_map: &EdgeMap,
    loop_vert_indices: &[usize],
    uv_coords: &[f32],
) -> (Dsu, Vec<(usize, usize)>) {
    let mut dsu = Dsu::new(num_faces);
    // Connections between islands (Geometrically connected but UVs are split)
    let mut island_connections: Vec<(usize, usize)> = Vec::new();

    for (_, entries) in edge_map.iter() {
        // If Manifold, entries.len() == 2
        // Non-manifold cases might have 3 or more, but checking all pairs here
        for i in 0..entries.len() {
            for j in (i + 1)..entries.len() {
                let ref1 = &entries[i];
                let ref2 = &entries[j];

                let (uv1_min, uv1_max) =
                    get_sorted_uvs(ref1.loop_curr, ref1.loop_next, loop_vert_indices, uv_coords);

                let (uv2_min, uv2_max) =
                    get_sorted_uvs(ref2.loop_curr, ref2.loop_next, loop_vert_indices, uv_coords);

                let connected_uv = is_uv_equal(uv1_min.0, uv1_min.1, uv2_min.0, uv2_min.1)
                    && is_uv_equal(uv1_max.0, uv1_max.1, uv2_max.0, uv2_max.1);

                if connected_uv {
                    dsu.merge(ref1.face_idx, ref2.face_idx);
                } else {
                    island_connections.push((ref1.face_idx, ref2.face_idx));
                }
            }
        }
    }
    (dsu, island_connections)
}

/// Build Island Adjacency Graph
/// IslandID (Representative Face ID) -> Set of Neighbor IslandIDs
fn build_adjacency_graph(
    num_faces: usize,
    dsu: &mut Dsu,
    island_connections: Vec<(usize, usize)>,
) -> (HashMap<usize, HashSet<usize>>, HashSet<usize>) {
    let mut adjacency: HashMap<usize, HashSet<usize>> = HashMap::new();
    let mut all_islands: HashSet<usize> = HashSet::new();

    for f in 0..num_faces {
        all_islands.insert(dsu.leader(f));
    }

    for (f1, f2) in island_connections {
        let root1 = dsu.leader(f1);
        let root2 = dsu.leader(f2);

        if root1 != root2 {
            adjacency.entry(root1).or_default().insert(root2);
            adjacency.entry(root2).or_default().insert(root1);
        }
    }
    (adjacency, all_islands)
}

/// Graph Coloring (Greedy Coloring / Welsh-Powell)
fn color_graph(
    adjacency: &HashMap<usize, HashSet<usize>>,
    all_islands: HashSet<usize>,
) -> HashMap<usize, i32> {
    let mut island_color_indices: HashMap<usize, i32> = HashMap::new();

    let mut islands_by_degree: Vec<(usize, usize)> = all_islands
        .into_iter()
        .map(|island| {
            let deg = adjacency.get(&island).map(|s| s.len()).unwrap_or(0);
            (deg, island)
        })
        .collect();

    islands_by_degree.sort_unstable_by(|a, b| b.0.cmp(&a.0));

    for (_, island) in islands_by_degree {
        let mut neighbor_colors = HashSet::new();
        if let Some(neighbors) = adjacency.get(&island) {
            for &n in neighbors {
                if let Some(&c) = island_color_indices.get(&n) {
                    neighbor_colors.insert(c);
                }
            }
        }

        let mut color_idx = 0;
        while neighbor_colors.contains(&color_idx) {
            color_idx += 1;
        }
        island_color_indices.insert(island, color_idx);
    }
    island_color_indices
}

/// Generate Result Data
/// Blender's Vertex Color (Byte Color / Attribute) holds data per loop
/// Flat List: [r, g, b, a, r, g, b, a, ...]
fn generate_result_colors(
    num_faces: usize,
    total_loop_count: usize,
    poly_loop_starts: &[usize],
    poly_loop_totals: &[usize],
    dsu: &mut Dsu,
    island_color_indices: &HashMap<usize, i32>,
) -> Vec<f32> {
    let mut result_colors = vec![0.0f32; total_loop_count * 4];

    for f_idx in 0..num_faces {
        let island_id = dsu.leader(f_idx);
        let c_idx = *island_color_indices.get(&island_id).unwrap_or(&0);

        let (r, g, b, a) = get_golden_ratio_color(c_idx as usize);

        let start = poly_loop_starts[f_idx];
        let total = poly_loop_totals[f_idx];

        for i in 0..total {
            let loop_idx = start + i;
            let offset = loop_idx * 4;

            result_colors[offset] = r;
            result_colors[offset + 1] = g;
            result_colors[offset + 2] = b;
            result_colors[offset + 3] = a;
        }
    }
    result_colors
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Test Helper: Get color of the first loop of the specified Face from result color array (RGBA)
    fn get_face_color(
        colors: &[f32],
        face_idx: usize,
        poly_loop_starts: &[usize],
    ) -> (f32, f32, f32) {
        let start = poly_loop_starts[face_idx];
        let offset = start * 4;
        (colors[offset], colors[offset + 1], colors[offset + 2])
    }

    #[test]
    fn test_single_triangle() {
        // Face 0: Vertices [0, 1, 2]
        let num_faces = 1;
        let poly_loop_starts = vec![0];
        let poly_loop_totals = vec![3];
        let loop_vert_indices = vec![0, 1, 2];
        // UV: Arbitrary values
        let uv_coords = vec![0.0, 0.0, 1.0, 0.0, 0.0, 1.0];

        let colors = bake_color_id_all(
            num_faces,
            poly_loop_starts,
            poly_loop_totals,
            loop_vert_indices,
            uv_coords,
        );

        // Verify: Data length is Loop count (3) * 4 (RGBA) = 12
        assert_eq!(colors.len(), 12);
        // Alpha is always 1.0
        assert_eq!(colors[3], 1.0);
    }

    #[test]
    fn test_connected_faces_same_island() {
        // Case where 2 triangles share edge (1, 2) and UVs are also connected
        // Face 0: [0, 1, 2]
        // Face 1: [2, 1, 3] (Note order: Share 1-2 edge in reverse direction for Manifold)

        let num_faces = 2;
        let poly_loop_starts = vec![0, 3];
        let poly_loop_totals = vec![3, 3];
        let loop_vert_indices = vec![
            0, 1, 2, // Face 0
            2, 1, 3, // Face 1
        ];

        // UV coordinates
        // Match v1=(1.0, 0.0), v2=(0.0, 1.0)
        let uv_coords = vec![
            0.0, 0.0, 1.0, 0.0, 0.0, 1.0, // Face 0 (v0, v1, v2)
            0.0, 1.0, 1.0, 0.0, 1.0, 1.0, // Face 1 (v2, v1, v3) -> v2, v1 match Face0
        ];

        let colors = bake_color_id_all(
            num_faces,
            poly_loop_starts.clone(),
            poly_loop_totals,
            loop_vert_indices,
            uv_coords,
        );

        // Verify: UVs are connected, so same island = same color
        let color0 = get_face_color(&colors, 0, &poly_loop_starts);
        let color1 = get_face_color(&colors, 1, &poly_loop_starts);

        assert_eq!(
            color0, color1,
            "Connected UVs should result in the same color ID"
        );
    }

    #[test]
    fn test_disconnected_faces_diff_color() {
        // Case where 2 triangles share edge (1, 2) but UVs are split (Seam)
        // Face 0: [0, 1, 2]
        // Face 1: [2, 1, 3]

        let num_faces = 2;
        let poly_loop_starts = vec![0, 3];
        let poly_loop_totals = vec![3, 3];
        let loop_vert_indices = vec![0, 1, 2, 2, 1, 3];

        // UV coordinates: Placed in completely different locations -> UV Seam
        let uv_coords = vec![
            0.0, 0.0, 0.1, 0.0, 0.0, 0.1, // Face 0 Area
            0.8, 0.8, 0.9, 0.8, 0.8, 0.9, // Face 1 Area (Far away)
        ];

        let colors = bake_color_id_all(
            num_faces,
            poly_loop_starts.clone(),
            poly_loop_totals,
            loop_vert_indices,
            uv_coords,
        );

        // Verify:
        // 1. Should be judged as different islands
        // 2. Adjacent on the adjacency graph, so should be "different colors" by graph coloring
        let color0 = get_face_color(&colors, 0, &poly_loop_starts);
        let color1 = get_face_color(&colors, 1, &poly_loop_starts);

        assert_ne!(
            color0, color1,
            "Adjacent islands must have different colors"
        );
    }

    #[test]
    fn test_edge_key_order() {
        // Confirm internal structure logic
        let k1 = EdgeKey::new(10, 20);
        let k2 = EdgeKey::new(20, 10);
        assert_eq!(k1, k2, "EdgeKey should be order-independent");
        assert_eq!(k1.min, 10);
        assert_eq!(k1.max, 20);
    }
}
