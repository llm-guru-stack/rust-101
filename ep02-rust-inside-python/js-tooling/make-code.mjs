// Generates src/ with 1,200 small JavaScript modules, so every tool has the same codebase to chew on.
import { mkdirSync, writeFileSync, rmSync } from "node:fs";

const N = Number(process.argv[2] ?? 1200);
rmSync("src", { recursive: true, force: true });
mkdirSync("src", { recursive: true });
for (let i = 0; i < N; i++) {
  const body = `import { helper${(i + 1) % N} } from "./mod${(i + 1) % N}.js";

export function helper${i}(items, limit = ${10 + (i % 7)}) {
  const out = [];
  for (const item of items) {
    if (item.score > limit) {
      out.push({ id: item.id, score: item.score * ${(i % 5) + 1}, tags: item.tags.filter((t) => t !== "skip") });
    }
  }
  return out.sort((a, b) => b.score - a.score);
}

export async function load${i}(fetcher, url) {
  const res = await fetcher(url + "/items/${i}");
  if (!res.ok) throw new Error("request failed: " + res.status);
  const data = await res.json();
  return helper${i}(data.items).map((x) => ({ ...x, next: typeof helper${(i + 1) % N} }));
}
`;
  writeFileSync(`src/mod${i}.js`, body);
}
console.log(`wrote ${N} files to src/`);
