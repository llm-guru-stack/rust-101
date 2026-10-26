//! Plain Rust chunking logic, shared by the Python (PyO3) and Node (napi-rs) wrappers.
use rayon::prelude::*;

/// Split one document into sentences (ending in . ! or ?) and group them into
/// chunks of `size` sentences that overlap by `overlap` sentences.
pub fn chunk(doc: &str, size: usize, overlap: usize) -> Vec<String> {
    let sents: Vec<&str> = doc.split_inclusive(&['.', '!', '?'][..]).collect();
    let step = size.saturating_sub(overlap).max(1);
    (0..sents.len())
        .step_by(step)
        .map(|i| sents[i..(i + size).min(sents.len())].concat())
        .collect()
}

/// Chunk every document on all CPU cores (rayon). Set RAYON_NUM_THREADS to limit the cores.
pub fn chunk_all(docs: &[String], size: usize, overlap: usize) -> Vec<Vec<String>> {
    docs.par_iter().map(|doc| chunk(doc, size, overlap)).collect()
}

/// The same work on one core, for comparison.
pub fn chunk_all_seq(docs: &[String], size: usize, overlap: usize) -> Vec<Vec<String>> {
    docs.iter().map(|doc| chunk(doc, size, overlap)).collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn overlapping_chunks() {
        assert_eq!(chunk("A. B. C.", 2, 1), vec!["A. B.", " B. C.", " C."]);
    }

    #[test]
    fn parallel_matches_sequential() {
        let docs: Vec<String> = (0..500).map(|i| format!("One {i}. Two! Three? Four. Five.")).collect();
        assert_eq!(chunk_all(&docs, 3, 1), chunk_all_seq(&docs, 3, 1));
    }
}
