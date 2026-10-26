use napi::bindgen_prelude::*;
use napi_derive::napi;

pub struct ChunkTask { docs: Vec<String>, size: u32, overlap: u32 }

impl Task for ChunkTask {
    type Output = Vec<Vec<String>>;
    type JsValue = Vec<Vec<String>>;
    // runs on a libuv worker thread, so Node's event loop keeps serving requests;
    // inside, rayon spreads the documents across every core
    fn compute(&mut self) -> Result<Self::Output> {
        Ok(fastchunk_core::chunk_all(&self.docs, self.size as usize, self.overlap as usize))
    }
    fn resolve(&mut self, _env: Env, out: Self::Output) -> Result<Self::JsValue> { Ok(out) }
}

/// The right way: returns a Promise and never blocks the event loop.
#[napi]
pub fn chunk_docs(docs: Vec<String>, size: u32, overlap: u32) -> AsyncTask<ChunkTask> {
    AsyncTask::new(ChunkTask { docs, size, overlap })
}

/// The trap: same work, but on the main thread. The event loop freezes until it's done.
#[napi]
pub fn chunk_docs_sync(docs: Vec<String>, size: u32, overlap: u32) -> Vec<Vec<String>> {
    fastchunk_core::chunk_all(&docs, size as usize, overlap as usize)
}
