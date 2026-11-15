import * as THREE from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader.js'
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js'
import { DRACO_DIR, DRACO_JS_ONLY, MODELS_AS_B64 } from './config'

let loader: GLTFLoader | null = null

async function getLoader(): Promise<GLTFLoader> {
  if (loader) return loader
  const l = new GLTFLoader()
  const draco = new DRACOLoader().setDecoderPath(DRACO_DIR)
  if (DRACO_JS_ONLY) draco.setDecoderConfig({ type: 'js' })
  draco.preload()
  l.setDRACOLoader(draco)
  try {
    await MeshoptDecoder.ready // only needed for meshopt-compressed files
    l.setMeshoptDecoder(MeshoptDecoder)
  } catch {
    /* WebAssembly blocked: Draco (JS) and quantize-only files still load */
  }
  loader = l
  return l
}

async function fetchBytes(url: string, onProgress: (p: number) => void): Promise<ArrayBuffer> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} for ${url}`)
  const total = Number(res.headers.get('content-length')) || 0
  const reader = res.body?.getReader()
  let buf: Uint8Array
  if (reader) {
    const chunks: Uint8Array[] = []
    let got = 0
    for (;;) {
      const { done, value } = await reader.read()
      if (done) break
      chunks.push(value)
      got += value.length
      if (total) onProgress(got / total)
    }
    buf = new Uint8Array(got)
    let o = 0
    for (const c of chunks) {
      buf.set(c, o)
      o += c.length
    }
  } else {
    buf = new Uint8Array(await res.arrayBuffer())
  }
  if (!url.endsWith('.b64.json')) return buf.buffer as ArrayBuffer
  const { glb } = JSON.parse(new TextDecoder().decode(buf)) as { glb: string }
  const bin = atob(glb)
  const out = new Uint8Array(bin.length)
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i)
  return out.buffer
}

/** Model file name as shipped: name.glb normally, name.b64.json on strict hosts. */
export function modelUrl(dir: string, file: string) {
  return dir + (MODELS_AS_B64 ? file.replace(/\.glb$/, '.b64.json') : file)
}

export async function loadBundle(url: string, onProgress: (p: number) => void = () => {}): Promise<THREE.Group> {
  const [bytes, l] = await Promise.all([fetchBytes(url, onProgress), getLoader()])
  return new Promise((resolve, reject) =>
    l.parse(bytes, '', (g) => resolve(g.scene), (e) => reject(new Error(String((e as unknown as { message?: string })?.message ?? e)))),
  )
}
