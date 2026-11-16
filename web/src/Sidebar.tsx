import { useMemo, useState } from 'react'
import { APP_LABEL, FEEDBACK_FORM_URL, LAYERS, SYSTEMS, TISSUE_LABEL, feedbackUrl } from './config'
import { useAtlas, type ViewPreset } from './store'
import type { Structure } from './types'

function score(s: Structure, q: string): number {
  const name = s.name.toLowerCase()
  const latin = (s.latin ?? '').toLowerCase()
  if (name === q) return 100
  if (name.startsWith(q)) return 80
  if (name.split(/\s+/).some((w) => w.startsWith(q))) return 60
  if (name.includes(q)) return 40
  if (latin.includes(q)) return 30
  const words = q.split(/\s+/).filter(Boolean)
  if (words.length > 1 && words.every((w) => name.includes(w) || latin.includes(w))) return 20
  return 0
}

function Search() {
  const structures = useAtlas((s) => s.structures)
  const bundles = useAtlas((s) => s.bundles)
  const focus = useAtlas((s) => s.focus)
  const [q, setQ] = useState('')
  const isolateGroup = useAtlas((s) => s.isolateGroup)
  const byId = useAtlas((s) => s.byId)
  const regionLabel = useMemo(() => Object.fromEntries(bundles.map((b) => [b.id, b.label])), [bundles])
  // every Z-Anatomy group that holds at least two structures, e.g. Heart, Brachial plexus, Rotator cuff muscles
  const groups = useMemo(() => {
    const g: Record<string, string[]> = {}
    for (const s of structures) for (const name of s.groups) (g[name] ??= []).push(s.id)
    return Object.entries(g).filter(([, ids]) => ids.length >= 2)
  }, [structures])
  const groupResults = useMemo(() => {
    const t = q.trim().toLowerCase()
    if (t.length < 3) return []
    return groups
      .map(([name, ids]) => {
        const n = name.toLowerCase()
        const sc = n === t ? 100 : n.startsWith(t) ? 70 : n.split(/\s+/).some((w) => w.startsWith(t)) ? 50 : 0
        // Z-Anatomy files muscles under the nerve that supplies them: say so, so it isn't read as the nerve
        const supplied = /nerve/i.test(name) && ids.filter((id) => byId[id]?.tissue === 'muscle').length >= 0.6 * ids.length
        return { name, ids, sc, supplied }
      })
      .filter((g) => g.sc > 0)
      .sort((a, b) => b.sc - a.sc || a.name.length - b.name.length)
      .slice(0, 3)
  }, [q, groups, byId])
  const scored = useMemo(() => {
    const t = q.trim().toLowerCase()
    if (t.length < 2) return []
    return structures
      .map((s) => ({ s, sc: score(s, t) }))
      .filter((r) => r.sc > 0)
      .sort((a, b) => b.sc - a.sc || a.s.name.length - b.s.name.length)
      .slice(0, 14)
  }, [q, structures])
  const results = scored.map((r) => r.s)
  const topScore = scored[0]?.sc ?? 0

  return (
    <div className="search">
      <input
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder="Search, e.g. median nerve or biceps"
        aria-label="Search structures"
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            const g = groupResults[0]
            // a structure that matches at least as well wins; groups are for names no single structure has
            if (g && g.sc > topScore) isolateGroup(g.supplied ? `muscles supplied by ${g.name}` : g.name, g.ids)
            else if (results[0]) focus(results[0].id)
            else return
            setQ('')
          }
          if (e.key === 'Escape') setQ('')
        }}
      />
      {(results.length > 0 || groupResults.length > 0) && (
        <ul className="results">
          {groupResults.map((g) => (
            <li key={'g:' + g.name}>
              <button
                onClick={() => {
                  isolateGroup(g.supplied ? `muscles supplied by ${g.name}` : g.name, g.ids)
                  setQ('')
                }}
              >
                <span className="dot group-dot" />
                <span className="r-name">{g.supplied ? `Muscles supplied by ${g.name}` : g.name}</span>
                <span className="r-meta">group · {g.ids.length}</span>
              </button>
            </li>
          ))}
          {results.map((s) => (
            <li key={s.id}>
              <button
                onClick={() => {
                  focus(s.id)
                  setQ('')
                }}
              >
                <span className={`dot sys-${s.system}`} />
                <span className="r-name">{s.name}</span>
                <span className="r-meta">
                  {s.side !== 'midline' ? (s.side === 'right' ? 'R · ' : 'L · ') : ''}
                  {regionLabel[s.region] ?? TISSUE_LABEL[s.tissue]}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
      {q.trim().length >= 2 && results.length === 0 && groupResults.length === 0 && <div className="empty">No match</div>}
    </div>
  )
}

export default function Sidebar({ onAbout }: { onAbout: () => void }) {
  const st = useAtlas()
  const counts = useMemo(() => {
    const c: Record<number, number> = {}
    for (const s of st.structures) c[s.depth] = (c[s.depth] ?? 0) + 1
    return c
  }, [st.structures])
  const views: ViewPreset[] = ['anterior', 'posterior', 'lateral', 'medial']

  return (
    <aside className="sidebar">
      <header className="brand">
        <h1>Anatomy Atlas</h1>
        <p>{APP_LABEL} · {st.structures.length || ''} structures</p>
      </header>

      <Search />

      <section>
        <div className="sec-head">
          <h2>Peel layers</h2>
          <label className="check small">
            <input type="checkbox" checked={st.ghostPeeled} onChange={st.toggleGhostPeeled} />
            Ghost peeled
          </label>
        </div>
        <ol className="layers">
          {LAYERS.map((l) => {
            const state = l.depth < st.peel ? 'peeled' : l.depth === st.peel ? 'current' : 'below'
            return (
              <li key={l.depth}>
                <button className={`layer ${state}`} onClick={() => st.setPeel(l.depth)} title={l.hint}>
                  <span className="l-num">{l.depth}</span>
                  <span className="l-label">{l.label}</span>
                  <span className="l-count">{counts[l.depth] ?? 0}</span>
                </button>
              </li>
            )
          })}
        </ol>
        <input
          className="peel-range"
          type="range"
          min={1}
          max={7}
          step={1}
          value={st.peel}
          onChange={(e) => st.setPeel(Number(e.target.value))}
          aria-label="Outermost visible layer"
        />
        <p className="hint">Click a layer to make it the outermost one shown. Everything above it is peeled away. In the trunk, turn off Bones and joints to see the organs.</p>
      </section>

      <section>
        <div className="sec-head">
          <h2>Regions</h2>
          <button className="link" onClick={st.allRegions}>
            Whole body
          </button>
        </div>
        <div className="regions">
          {st.bundles.map((b) => (
            <div key={b.id} className="region-row">
              <label className="check">
                <input type="checkbox" checked={!!st.regions[b.id]} onChange={() => st.toggleRegion(b.id)} />
                {b.label}
              </label>
              <span className={`r-status ${st.status[b.id]}`}>
                {st.status[b.id] === 'ready' ? (
                  <button className="link" onClick={() => st.onlyRegion(b.id)} title={`Show only ${b.label}`}>
                    Only
                  </button>
                ) : st.status[b.id] === 'error' ? (
                  'failed'
                ) : (
                  '…'
                )}
              </span>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2>Systems</h2>
        <div className="systems">
          {SYSTEMS.map((s) => (
            <label key={s.key} className="check">
              <input type="checkbox" checked={st.systems[s.key]} onChange={() => st.toggleSystem(s.key)} />
              <span className="swatch" style={{ background: s.swatch }} />
              {s.label}
            </label>
          ))}
        </div>
      </section>

      <section>
        <h2>View</h2>
        <div className="views">
          {views.map((v) => (
            <button key={v} onClick={() => st.view(v)}>
              {v[0].toUpperCase() + v.slice(1)}
            </button>
          ))}
        </div>
      </section>

      {(st.hidden.length > 0 || st.isolated) && (
        <section>
          <div className="sec-head">
            <h2>{st.isolated ? (st.isolatedLabel ? `Showing ${st.isolatedLabel}` : 'Isolated') : `Hidden (${st.hidden.length})`}</h2>
            <button className="link" onClick={st.showAll}>
              Show all
            </button>
          </div>
          {!st.isolated && (
            <ul className="hidden-list">
              {st.hidden.map((id) => (
                <li key={id}>
                  <span>{st.byId[id]?.name}</span>
                  <button className="link" onClick={() => st.unhide(id)}>
                    Show
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}

      <footer className="side-foot">
        <button onClick={st.reset}>Reset everything</button>
        <span className="foot-links">
          {FEEDBACK_FORM_URL && (
            <a className="link" href={feedbackUrl()} target="_blank" rel="noreferrer">
              Send feedback
            </a>
          )}
          <button className="link" onClick={onAbout}>
            About and credits
          </button>
        </span>
      </footer>
    </aside>
  )
}
