// SPDX-License-Identifier: GPL-3.0-or-later

mod algorithm;

use pyo3::prelude::*;

#[pyfunction]
fn solve_heavy_math(a: usize, b: usize) -> PyResult<usize> {
    Ok(a + b)
}

#[pyfunction]
fn bake_color_id_all(
    num_faces: usize,
    poly_loop_starts: Vec<usize>,
    poly_loop_totals: Vec<usize>,
    loop_vert_indices: Vec<usize>,
    uv_coords: Vec<f32>,
) -> PyResult<Vec<f32>> {
    if poly_loop_starts.len() != num_faces {
        return Err(pyo3::exceptions::PyValueError::new_err(format!(
            "poly_loop_starts length mismatch: expected {}, got {}", num_faces, poly_loop_starts.len()
        )));
    }
    if poly_loop_totals.len() != num_faces {
        return Err(pyo3::exceptions::PyValueError::new_err(format!(
            "poly_loop_totals length mismatch: expected {}, got {}", num_faces, poly_loop_totals.len()
        )));
    }
    if uv_coords.len() != loop_vert_indices.len() * 2 {
        return Err(pyo3::exceptions::PyValueError::new_err(format!(
            "uv_coords length mismatch: expected {} (loops*2), got {}", loop_vert_indices.len() * 2, uv_coords.len()
        )));
    }
    let result = algorithm::color_id::bake_color_id_all(
        num_faces,
        poly_loop_starts,
        poly_loop_totals,
        loop_vert_indices,
        uv_coords,
    );
    Ok(result)
}

#[pymodule]
fn nt_rust_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(solve_heavy_math, m)?)?;
    m.add_function(wrap_pyfunction!(bake_color_id_all, m)?)?;
    Ok(())
}
