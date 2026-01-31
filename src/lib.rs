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
