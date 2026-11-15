import { useState } from 'react'
import { LAYERS, TISSUE_LABEL } from './config'
import { useAtlas } from './store'

export default function InfoPanel({ onReport }: { onReport: (id: string) => void }) {
  const st = useAtlas()
  const [expanded, setExpanded] = useState(false)
  const s = st.selected ? st.byId[st.selected] : null
  if (!s) return null
  const c = s.content_ref ? st.content[s.content_ref] : null
  const layer = LAYERS.find((l) => l.depth === s.depth)
  const regionLabel = st.bundles.find((b) => b.id === s.region)?.label ?? s.region
  const loadingText = !c && s.content_ref && st.status[s.region] !== 'ready'
  const paras = c?.paragraphs ?? []
  const shown = expanded ? paras : paras.slice(0, 3)
  const ghosted = st.ghosted.includes(s.id)
  const partOf = s.groups.filter(
    (g) =>
      g !== s.name &&
      !s.innervation.includes(g) &&
      !/^(Muscles|Nerves|Bonus collection|Superficial muscles|Central nervous system|Sense organs)$/.test(g),
  )

  return (
    <aside className="info" key={s.id}>
      <div className="info-head">
        <div>
          <h2>{s.name}</h2>
          {s.latin && <p className="latin">{s.latin}</p>}
        </div>
        <button className="close" onClick={() => st.select(null)} aria-label="Close">
          ×
        </button>
      </div>

      <div className="badges">
        <span className={`badge sys-${s.system}`}>{TISSUE_LABEL[s.tissue]}</span>
        <span className="badge">Layer {s.depth}: {layer?.label}</span>
        <span className="badge">
          {regionLabel}
          {s.side !== 'midline' ? ` · ${s.side}` : ''}
        </span>
        <span className={`badge ${c?.reviewed_by ? 'ok' : 'warn'}`}>{c?.reviewed_by ? 'Reviewed' : 'Not yet reviewed'}</span>
      </div>

      <div className="actions">
        <button onClick={() => st.hide(s.id)}>Hide</button>
        <button onClick={() => (st.isolated ? st.clearIsolate() : st.isolate(s.id))}>
          {st.isolated ? 'Show rest' : 'Isolate'}
        </button>
        <button onClick={() => st.toggleGhost(s.id)}>{ghosted ? 'Unghost' : 'Ghost'}</button>
        <button onClick={() => st.focus(s.id)}>Zoom to</button>
      </div>

      {s.tissue === 'muscle' && (
        <dl className="facts">
          <dt>Nerve supply</dt>
          <dd>{s.innervation.length ? s.innervation.join(', ') : <em>Not filled yet</em>}</dd>
        </dl>
      )}
      {partOf.length > 0 && (
        <dl className="facts">
          <dt>Part of</dt>
          <dd>{partOf.join(' · ')}</dd>
        </dl>
      )}
      {s.depth_note && (
        <dl className="facts">
          <dt>Layer note</dt>
          <dd>{s.depth_note}</dd>
        </dl>
      )}

      <div className="desc">
        {c ? (
          <>
            {s.content_shared_from && (
              <p className="shared">Text below is for {s.content_shared_from}, the larger structure this belongs to.</p>
            )}
            {shown.map((p, i) =>
              p.startsWith('## ') ? <h3 key={i}>{p.slice(3)}</h3> : <p key={i}>{p}</p>,
            )}
            {paras.length > 3 && (
              <button className="link" onClick={() => setExpanded(!expanded)}>
                {expanded ? 'Show less' : `Read more (${paras.length - 3} more paragraphs)`}
              </button>
            )}
            {expanded && c.truncated && (
              <p className="muted">The article continues at the source link below.</p>
            )}
            <p className="source">
              Source: {c.source}
              {c.source_url && (
                <>
                  {' · '}
                  <a href={c.source_url} target="_blank" rel="noreferrer">
                    original article
                  </a>
                </>
              )}
            </p>
          </>
        ) : (
          <p className="muted">{loadingText ? 'Loading description…' : 'No description yet for this structure.'}</p>
        )}
      </div>

      <button className="report" onClick={() => onReport(s.id)}>
        Report an error in this structure
      </button>
    </aside>
  )
}
