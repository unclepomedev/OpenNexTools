// SPDX-License-Identifier: GPL-3.0-or-later

mod algorithm;

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

#[pyfunction]
fn bake_color_id_all(
    num_faces: usize,
    poly_loop_starts: Vec<usize>,
    poly_loop_totals: Vec<usize>,
    loop_vert_indices: Vec<usize>,
    uv_coords: Vec<f32>,
) -> PyResult<Vec<f32>> {
    if poly_loop_starts.len() != num_faces {
        return Err(PyValueError::new_err(format!(
            "Data mismatch: poly_loop_starts length {} != num_faces {}",
            poly_loop_starts.len(),
            num_faces
        )));
    }
    if poly_loop_totals.len() != num_faces {
        return Err(PyValueError::new_err(format!(
            "Data mismatch: poly_loop_totals length {} != num_faces {}",
            poly_loop_totals.len(),
            num_faces
        )));
    }

    let total_loops = loop_vert_indices.len();

    for (i, (&start, &total)) in poly_loop_starts
        .iter()
        .zip(poly_loop_totals.iter())
        .enumerate()
    {
        if total == 0 {
            return Err(PyValueError::new_err(format!(
                "Face {} has 0 loops. This causes division by zero.",
                i
            )));
        }
        if start + total > total_loops {
            return Err(PyValueError::new_err(format!(
                "Face {} loops out of bounds: start {} + total {} > total loops {}",
                i, start, total, total_loops
            )));
        }
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
    m.add_function(wrap_pyfunction!(bake_color_id_all, m)?)?;
    Ok(())
}
