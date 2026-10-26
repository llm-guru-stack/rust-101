// The event-loop trap, measured. A timer ticks every millisecond (think: other requests
// being answered). We count how many ticks get through while Rust is working.
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
const { chunkDocs, chunkDocsSync } = require("./index.js");

const docs = JSON.parse(readFileSync(new URL("../data/docs.json", import.meta.url)));
// repeat the work so the call lasts long enough to see the difference
const big = Array.from({ length: 10 }, () => docs).flat();

let ticks = 0;
const timer = setInterval(() => { ticks++; }, 1);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

await sleep(50);
let t0 = performance.now(), before = ticks;
const a = chunkDocsSync(big, 5, 1);
await sleep(0);
console.log(`sync  (blocks the event loop): ${((performance.now() - t0) / 1000).toFixed(2)}s, timer ticked ${ticks - before} times`);

await sleep(50);
t0 = performance.now(); before = ticks;
const b = await chunkDocs(big, 5, 1);
console.log(`async (AsyncTask + rayon):     ${((performance.now() - t0) / 1000).toFixed(2)}s, timer ticked ${ticks - before} times`);

clearInterval(timer);
console.log(`same output: ${JSON.stringify(a) === JSON.stringify(b) ? "yes" : "NO"} · ${a.length.toLocaleString()} documents`);
