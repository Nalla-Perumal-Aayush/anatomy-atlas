import { useEffect, useMemo, useRef, useState } from 'react'
import { Canvas, useFrame, useThree, type ThreeEvent } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import * as THREE from 'three'
import type { OrbitControls as OrbitControlsImpl } from 'three-stdlib'
import { MODEL_DIR } from './config'
import { loadBundle, modelUrl } from './loadModel'
import { drawMode, useAtlas, type ViewPreset } from './store'
import type { Content } from './types'

const BASE_OPACITY: Record<string, number> = {
  atlas_fascia: 0.45,
  atlas_bursa: 0.5,
  atlas_tendon_sheath: 0.6,
  atlas_peritoneum: 0.45,
  atlas_cornea: 0.4,
}
const DOUBLE_SIDED = new Set(['atlas_skin', 'atlas_skin_inner', 'atlas_fascia', 'atlas_peritoneum'])
const SELECT_COLOR = new THREE.Color('#1e8bff')
const HOVER_COLOR = new THREE.Color('#ffffff')
const BLACK = new THREE.Color(0, 0, 0)
const NO_RAYCAST = () => {}
// Whole body framing used before anything is visible (metres, Y up, model faces +Z)
const BODY_BOX = new THREE.Box3(new THREE.Vector3(-0.45, 0, -0.2), new THREE.Vector3(0.45, 1.8, 0.2))

interface Part {
  root: THREE.Object3D
  meshes: THREE.Mesh[]
  key: string // last applied draw state, to skip unchanged parts
}
/** All loaded structures by id, across bundles. */
const registry: Record<string, Part> = {}

function findId(o: THREE.Object3D | null): string | null {
  while (o) {
    if (o.userData.sid) return o.userData.sid as string
    o = o.parent
  }
  return null
}

function Model({ scene }: { scene: THREE.Group }) {
  const invalidate = useThree((s) => s.invalidate)
  const byId = useAtlas((s) => s.byId)
  const st = useAtlas()
  const downAt = useRef<[number, number] | null>(null)

  const ids = useMemo(() => {
    const out: string[] = []
    scene.traverse((o) => {
      if (!byId[o.name] || registry[o.name]) return
      const meshes: THREE.Mesh[] = []
      o.traverse((c) => {
        const m = c as THREE.Mesh
        if (!m.isMesh) return
        const src = m.material as THREE.MeshStandardMaterial
        const mat = src.clone()
        const base = BASE_OPACITY[src.name] ?? 1
        mat.userData.baseOpacity = base
        mat.userData.baseColor = src.color.clone()
        mat.transparent = base < 1
        mat.opacity = base
        mat.depthWrite = base >= 1
        mat.side = DOUBLE_SIDED.has(src.name) ? THREE.DoubleSide : THREE.FrontSide
        mat.roughness = 0.62
        mat.metalness = 0
        m.material = mat
        m.userData.sid = o.name
        meshes.push(m)
      })
      o.userData.sid = o.name
      registry[o.name] = { root: o, meshes, key: '' }
      out.push(o.name)
    })
    return out
  }, [scene, byId])

  useEffect(() => {
    useAtlas.getState().bumpParts()
  }, [ids])

  useEffect(() => {
    for (const id of ids) {
      const part = registry[id]
      const mode = drawMode(byId[id], st)
      const isSel = st.selected === id
      const isHov = st.hovered === id && !isSel
      const key = `${mode}${isSel ? 's' : ''}${isHov ? 'h' : ''}`
      if (part.key === key) continue
      part.key = key
      part.root.visible = mode !== 'off'
      for (const m of part.meshes) m.raycast = mode === 'solid' ? THREE.Mesh.prototype.raycast : NO_RAYCAST
      if (mode === 'off') continue
      for (const m of part.meshes) {
        const mat = m.material as THREE.MeshStandardMaterial
        const base = mat.userData.baseOpacity as number
        const ghost = mode === 'ghost'
        const transparent = ghost || base < 1
        if (mat.transparent !== transparent) mat.needsUpdate = true
        mat.transparent = transparent
        mat.opacity = ghost ? 0.1 : base
        mat.depthWrite = !ghost && base >= 1
        mat.color.copy(isSel ? (mat.userData.baseColor as THREE.Color).clone().lerp(SELECT_COLOR, 0.65) : mat.userData.baseColor)
        mat.emissive.copy(isSel ? SELECT_COLOR : isHov ? HOVER_COLOR : BLACK)
        mat.emissiveIntensity = isSel ? 0.35 : isHov ? 0.25 : 0
        m.renderOrder = ghost ? 2 : base < 1 ? 1 : 0
      }
    }
    invalidate()
  }, [ids, byId, st.peel, st.ghostPeeled, st.systems, st.regions, st.hidden, st.ghosted, st.isolated, st.selected, st.hovered])

  const onMove = (e: ThreeEvent<PointerEvent>) => {
    e.stopPropagation()
    const id = findId(e.object)
    if (id !== useAtlas.getState().hovered) useAtlas.getState().hover(id)
  }
  const onClick = (e: ThreeEvent<MouseEvent>) => {
    e.stopPropagation()
    const d = downAt.current
    if (d && Math.hypot(e.nativeEvent.clientX - d[0], e.nativeEvent.clientY - d[1]) > 5) return
    useAtlas.getState().select(findId(e.object))
  }
  return (
    <primitive
      object={scene}
      onPointerMove={onMove}
      onPointerOut={() => useAtlas.getState().hover(null)}
      onPointerDown={(e: ThreeEvent<PointerEvent>) => (downAt.current = [e.nativeEvent.clientX, e.nativeEvent.clientY])}
      onClick={onClick}
    />
  )
}

const PRESET_DIR: Record<ViewPreset, THREE.Vector3> = {
  anterior: new THREE.Vector3(0, 0, 1),
  posterior: new THREE.Vector3(0, 0, -1),
  lateral: new THREE.Vector3(-1, 0, 0),
  medial: new THREE.Vector3(1, 0, 0),
}

function boxOf(filter: (id: string) => boolean): THREE.Box3 | null {
  const box = new THREE.Box3()
  let any = false
  for (const [id, p] of Object.entries(registry)) {
    if (!filter(id) || !p.root.visible) continue
    box.expandByObject(p.root)
    any = true
  }
  return any ? box : null
}

function CameraRig() {
  const camera = useThree((s) => s.camera) as THREE.PerspectiveCamera
  const controls = useThree((s) => s.controls) as unknown as OrbitControlsImpl | null
  const req = useAtlas((s) => s.focusRequest)
  const partsVersion = useAtlas((s) => s.partsVersion)
  const goal = useRef<{ pos: THREE.Vector3; target: THREE.Vector3 } | null>(null)
  const done = useRef(-1)
  const invalidate = useThree((s) => s.invalidate)

  useEffect(() => {
    if (!controls || done.current === req.n) return
    const fit = (box: THREE.Box3, dir: THREE.Vector3, pad: number) => {
      const sphere = box.getBoundingSphere(new THREE.Sphere())
      const fov = THREE.MathUtils.degToRad(camera.fov)
      const dist = Math.max((sphere.radius * pad) / Math.sin(fov / 2), 0.08)
      goal.current = { target: sphere.center.clone(), pos: sphere.center.clone().add(dir.clone().normalize().multiplyScalar(dist)) }
    }
    const currentDir = () => {
      const d = camera.position.clone().sub(controls.target)
      return d.lengthSq() > 0 ? d : PRESET_DIR.anterior
    }
    if (req.id) {
      const p = registry[req.id]
      if (!p) return // its bundle is still loading: try again when parts arrive
      p.root.updateWorldMatrix(true, true)
      const box = new THREE.Box3().setFromObject(p.root)
      // look from the side the structure lies on, measured from the middle of its region
      const byId = useAtlas.getState().byId
      const region = byId[req.id]?.region
      const regionBox = boxOf((id) => byId[id]?.region === region)
      let dir = currentDir()
      if (regionBox) {
        const c = box.getCenter(new THREE.Vector3())
        const rc = regionBox.getCenter(new THREE.Vector3())
        const out = new THREE.Vector3(c.x - rc.x, 0, c.z - rc.z)
        const size = regionBox.getSize(new THREE.Vector3())
        if (out.length() > 0.12 * Math.max(size.x, size.z)) dir = out.normalize().add(new THREE.Vector3(0, 0.25, 0))
      }
      fit(box, dir, 1.6)
    } else if (req.ids) {
      const want = new Set(req.ids)
      const box = boxOf((id) => want.has(id))
      if (!box) return
      fit(box, currentDir(), 1.15)
    } else if (req.region) {
      const byId = useAtlas.getState().byId
      const box = boxOf((id) => byId[id]?.region === req.region)
      if (!box) return
      fit(box, currentDir(), 1.05)
    } else if (req.preset) {
      // first view frames the whole body even while regions are still arriving
      fit(req.n === 0 ? BODY_BOX : boxOf(() => true) ?? BODY_BOX, PRESET_DIR[req.preset], 1.0)
    }
    done.current = req.n
    invalidate()
  }, [req, partsVersion, camera, controls, invalidate])

  useFrame((_, dt) => {
    if (!goal.current || !controls) return
    const k = 1 - Math.pow(0.0005, dt)
    camera.position.lerp(goal.current.pos, k)
    controls.target.lerp(goal.current.target, k)
    controls.update()
    if (camera.position.distanceTo(goal.current.pos) < 1e-4 && controls.target.distanceTo(goal.current.target) < 1e-4) {
      goal.current = null
    } else {
      invalidate() // keep drawing until the camera move finishes
    }
  })
  return null
}

/** Loads the bundles one after another, in manifest order. */
function useBundles() {
  const bundles = useAtlas((s) => s.bundles)
  const [scenes, setScenes] = useState<Record<string, THREE.Group>>({})
  const [progress, setProgress] = useState(0)
  useEffect(() => {
    if (!bundles.length) return
    let alive = true
    ;(async () => {
      for (const b of bundles) {
        if (!alive) return
        const st = useAtlas.getState()
        st.setStatus(b.id, 'loading')
        setProgress(0)
        try {
          const [scene, content] = await Promise.all([
            loadBundle(modelUrl(MODEL_DIR, b.model), (p) => alive && setProgress(p)),
            fetch(MODEL_DIR + b.content).then((r) => r.json() as Promise<Record<string, Content>>),
          ])
          if (!alive) return
          st.addContent(content)
          setScenes((s) => ({ ...s, [b.id]: scene }))
          st.setStatus(b.id, 'ready')
        } catch (e) {
          console.error(e)
          st.setStatus(b.id, 'error')
        }
      }
    })()
    return () => {
      alive = false
    }
  }, [bundles])
  return { scenes, progress }
}

export default function Viewer() {
  const { scenes, progress } = useBundles()
  const status = useAtlas((s) => s.status)
  const bundles = useAtlas((s) => s.bundles)
  const loadingB = bundles.find((b) => status[b.id] === 'loading')
  const ready = bundles.filter((b) => status[b.id] === 'ready').length
  const failed = bundles.filter((b) => status[b.id] === 'error').length

  return (
    <>
      {loadingB && (
        <div className={ready ? 'loading-chip' : 'loader'}>
          Loading {loadingB.label.toLowerCase()} ({ready + 1} of {bundles.length}) {Math.round(progress * 100)}%
        </div>
      )}
      {failed > 0 && !loadingB && <div className="loading-chip error-chip">{failed} region(s) failed to load</div>}
      <Canvas
        frameloop="demand"
        camera={{ fov: 35, near: 0.005, far: 30, position: [0, 1, 4] }}
        dpr={[1, 2]}
        gl={{ antialias: true, preserveDrawingBuffer: true }}
        onPointerMissed={(e) => {
          if (e.type === 'click') useAtlas.getState().select(null)
        }}
      >
        <ambientLight intensity={0.45} />
        <hemisphereLight args={['#ffffff', '#3a3530', 0.7]} />
        <directionalLight position={[1.5, 2.5, 3]} intensity={1.4} />
        <directionalLight position={[-2, 1, -2.5]} intensity={0.7} />
        <directionalLight position={[-3, 0.5, 1]} intensity={0.5} />
        {Object.entries(scenes).map(([id, scene]) => (
          <Model key={id} scene={scene} />
        ))}
        <OrbitControls makeDefault enableDamping dampingFactor={0.12} minDistance={0.03} maxDistance={8} />
        <CameraRig />
      </Canvas>
    </>
  )
}
