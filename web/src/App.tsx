import { useEffect, useState } from 'react'
import Viewer from './Viewer'
import Sidebar from './Sidebar'
import InfoPanel from './InfoPanel'
import { FEEDBACK_FORM_URL, MODEL_DIR, TISSUE_LABEL } from './config'
import { useAtlas } from './store'
import type { Bundle, Structure } from './types'

function Tooltip() {
  const hovered = useAtlas((s) => (s.hovered ? s.byId[s.hovered] : null))
  const [pos, setPos] = useState<[number, number]>([0, 0])
  useEffect(() => {
    const f = (e: PointerEvent) => setPos([e.clientX, e.clientY])
    window.addEventListener('pointermove', f)
    return () => window.removeEventListener('pointermove', f)
  }, [])
  if (!hovered) return null
  return (
    <div className="tooltip" style={{ left: pos[0] + 14, top: pos[1] + 14 }}>
      {hovered.name}
      <span>{TISSUE_LABEL[hovered.tissue]}</span>
    </div>
  )
}

function ReportModal({ id, onClose }: { id: string; onClose: () => void }) {
  const s = useAtlas((st) => st.byId[id])
  const [note, setNote] = useState('')
  const [copied, setCopied] = useState(false)
  const report = `Structure: ${s.name} (${s.id})\nLayer: ${s.depth}\nWhat is wrong:\n${note}`
  return (
    <div className="modal-back" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>Report an error</h2>
        <p className="muted">{s.name}</p>
        <textarea
          autoFocus
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="What looks wrong? Name, position, layer, description..."
          rows={5}
        />
        <div className="modal-actions">
          {FEEDBACK_FORM_URL ? (
            <a className="btn primary" href={`${FEEDBACK_FORM_URL}`} target="_blank" rel="noreferrer">
              Open feedback form
            </a>
          ) : null}
          <button
            className="primary"
            onClick={() => {
              navigator.clipboard?.writeText(report).then(() => setCopied(true), () => setCopied(false))
            }}
          >
            {copied ? 'Copied' : 'Copy report'}
          </button>
          <button onClick={onClose}>Close</button>
        </div>
        {!FEEDBACK_FORM_URL && (
          <p className="hint">Paste the copied report into the feedback sheet your coordinator shared.</p>
        )}
      </div>
    </div>
  )
}

function About({ onClose }: { onClose: () => void }) {
  return (
    <div className="modal-back" onClick={onClose}>
      <div className="modal about" onClick={(e) => e.stopPropagation()}>
        <h2>About this atlas</h2>
        <p>
          A study tool for first-year medical students covering the whole body. Built by Nalla Perumal Aayush C.
          This is a test build: the content has not been reviewed yet, so check anything important against your
          textbook.
        </p>
        <h3>Credits</h3>
        <ul>
          <li>
            Models: “Z-Anatomy, the libre 3D atlas of anatomy”, CC BY-SA 4.0, based on “BodyParts3D, The Database
            Center for Life Science”, CC BY-SA 2.1 Japan.
          </li>
          <li>Descriptions: Z-Anatomy definitions based on Wikipedia, CC BY-SA 3.0.</li>
          <li>Latin names: Terminologia Anatomica 2 table shipped with Z-Anatomy.</li>
        </ul>
        <p className="muted">The converted models in this app are shared under CC BY-SA 4.0.</p>
        <div className="modal-actions">
          <button onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  )
}

export default function App() {
  const setData = useAtlas((s) => s.setData)
  const selected = useAtlas((s) => s.selected)
  const [error, setError] = useState<string | null>(null)
  const [reportId, setReportId] = useState<string | null>(null)
  const [about, setAbout] = useState(false)

  useEffect(() => {
    Promise.all([
      fetch(MODEL_DIR + 'manifest.json').then((r) => r.json()),
      fetch(MODEL_DIR + 'metadata.json').then((r) => r.json()),
    ])
      .then(([man, meta]: [{ bundles: Bundle[] }, { structures: Structure[] }]) =>
        setData(man.bundles, meta.structures),
      )
      .catch((e) => setError(String(e)))
  }, [setData])

  useEffect(() => {
    const f = (e: KeyboardEvent) => {
      if ((e.target as HTMLElement).tagName === 'INPUT' || (e.target as HTMLElement).tagName === 'TEXTAREA') return
      const st = useAtlas.getState()
      if (e.key === 'Escape') st.select(null)
      if ((e.key === 'h' || e.key === 'H') && st.selected) st.hide(st.selected)
    }
    window.addEventListener('keydown', f)
    return () => window.removeEventListener('keydown', f)
  }, [])

  return (
    <div className="app">
      <Sidebar onAbout={() => setAbout(true)} />
      <main className="stage">
        {error ? <div className="error">Could not load data: {error}</div> : <Viewer />}
        <div className="stage-hint">Drag to rotate · right-drag to pan · scroll to zoom · click a structure</div>
      </main>
      {selected && <InfoPanel key={selected} onReport={setReportId} />}
      <Tooltip />
      {reportId && <ReportModal id={reportId} onClose={() => setReportId(null)} />}
      {about && <About onClose={() => setAbout(false)} />}
    </div>
  )
}
