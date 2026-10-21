use pyo3::prelude::*;

/// Split each document into sentences (ending in . ! or ?) and group them into
/// chunks of `size` sentences that overlap by `overlap` sentences.
#[pyfunction]
fn chunk_docs(py: Python<'_>, docs: Vec<String>, size: usize, overlap: usize) -> Vec<Vec<String>> {
    py.allow_threads(|| {
        docs.iter().map(|doc| {
            let sents: Vec<&str> = doc.split_inclusive(&['.', '!', '?'][..]).collect();
            let step = size.saturating_sub(overlap).max(1);
            (0..sents.len()).step_by(step)
                .map(|i| sents[i..(i + size).min(sents.len())].concat())
                .collect()
        }).collect()
    })
}

#[pymodule]
fn fastchunk(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(chunk_docs, m)?)
}
