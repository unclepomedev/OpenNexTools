use pyo3::prelude::*;

#[pyfunction]
fn solve_heavy_math(a: usize, b: usize) -> PyResult<usize> {
    Ok(a + b)
}

#[pymodule]
fn nt_rust_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(solve_heavy_math, m)?)?;
    Ok(())
}
