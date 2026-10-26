use pyo3::prelude::*;
use rayon::prelude::*;
use std::time::Instant;

/// Chunk every document on all CPU cores. Same signature as episode 2, so Python code doesn't change.
#[pyfunction]
fn chunk_docs(py: Python<'_>, docs: Vec<String>, size: usize, overlap: usize) -> Vec<Vec<String>> {
    py.allow_threads(|| {
        docs.par_iter()
            .map(|doc| fastchunk_core::chunk(doc, size, overlap))
            .collect()
    })
}

/// Episode 2's version: one core.
#[pyfunction]
fn chunk_docs_seq(py: Python<'_>, docs: Vec<String>, size: usize, overlap: usize) -> Vec<Vec<String>> {
    py.allow_threads(|| fastchunk_core::chunk_all_seq(&docs, size, overlap))
}

/// Same as chunk_docs, but also returns how long the Rust part alone took (seconds).
/// The difference to the total call time is the part that can't run in parallel.
#[pyfunction]
fn chunk_docs_timed(py: Python<'_>, docs: Vec<String>, size: usize, overlap: usize) -> (Vec<Vec<String>>, f64) {
    py.allow_threads(|| {
        let t = Instant::now();
        let out = fastchunk_core::chunk_all(&docs, size, overlap);
        (out, t.elapsed().as_secs_f64())
    })
}

/// How many worker threads rayon is using (follows RAYON_NUM_THREADS).
#[pyfunction]
fn num_threads() -> usize {
    rayon::current_num_threads()
}

#[pymodule]
fn fastchunk(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(chunk_docs, m)?)?;
    m.add_function(wrap_pyfunction!(chunk_docs_seq, m)?)?;
    m.add_function(wrap_pyfunction!(chunk_docs_timed, m)?)?;
    m.add_function(wrap_pyfunction!(num_threads, m)?)
}
