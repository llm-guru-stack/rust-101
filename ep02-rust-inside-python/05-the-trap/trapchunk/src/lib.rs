use pyo3::prelude::*;

fn chunk_all(docs: &[String], size: usize, overlap: usize, rounds: usize) -> Vec<Vec<String>> {
    let mut out = Vec::new();
    for _ in 0..rounds.max(1) {
        out = docs.iter().map(|doc| {
            let sents: Vec<&str> = doc.split_inclusive(&['.', '!', '?'][..]).collect();
            let step = size.saturating_sub(overlap).max(1);
            (0..sents.len()).step_by(step)
                .map(|i| sents[i..(i + size).min(sents.len())].concat())
                .collect()
        }).collect();
    }
    out
}

/// Good: releases the GIL while the Rust work runs, so other Python threads keep going.
#[pyfunction]
#[pyo3(signature = (docs, size, overlap, rounds=1))]
fn chunk_docs(py: Python<'_>, docs: Vec<String>, size: usize, overlap: usize, rounds: usize) -> Vec<Vec<String>> {
    py.allow_threads(|| chunk_all(&docs, size, overlap, rounds))
}

/// Trap 1: same work, but it holds the GIL the whole time. Every other Python thread freezes.
#[pyfunction]
#[pyo3(signature = (docs, size, overlap, rounds=1))]
fn chunk_docs_holding_gil(docs: Vec<String>, size: usize, overlap: usize, rounds: usize) -> Vec<Vec<String>> {
    chunk_all(&docs, size, overlap, rounds)
}

/// Trap 2, version 1: Rust does one tiny job per call (is this word long?).
#[pyfunction]
fn is_long_word(word: &str) -> bool {
    word.chars().count() > 6
}

/// Trap 2, version 2: Rust gets whole documents and does the loop itself.
#[pyfunction]
fn count_long_words(py: Python<'_>, docs: Vec<String>) -> usize {
    py.allow_threads(|| {
        docs.iter()
            .map(|d| d.split_whitespace().filter(|w| w.chars().count() > 6).count())
            .sum()
    })
}

#[pymodule]
fn trapchunk(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(chunk_docs, m)?)?;
    m.add_function(wrap_pyfunction!(chunk_docs_holding_gil, m)?)?;
    m.add_function(wrap_pyfunction!(is_long_word, m)?)?;
    m.add_function(wrap_pyfunction!(count_long_words, m)?)
}
