// Wrap every .glb in a folder as <name>.b64.json ({"glb": "<base64>"}) and remove the .glb.
// Used for hosts that refuse binary model files. Usage: node scripts/b64.mjs <folder>
import { readdirSync, readFileSync, writeFileSync, unlinkSync } from 'node:fs'
import { join } from 'node:path'

const dir = process.argv[2]
for (const f of readdirSync(dir)) {
  if (!f.endsWith('.glb')) continue
  const p = join(dir, f)
  const out = join(dir, f.replace(/\.glb$/, '.b64.json'))
  writeFileSync(out, JSON.stringify({ glb: readFileSync(p).toString('base64') }))
  unlinkSync(p)
  console.log(`wrote ${out}`)
}
