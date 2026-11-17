import { useEffect } from 'react'
import { useAtlas } from './store'

/**
 * Lets another page that embeds the atlas in an iframe drive it, and hear what the user picks.
 *
 * In:  { type: 'atlas:show', ids: string[], label?: string }   one id focuses it in context, several isolate them
 *      { type: 'atlas:reset' }
 * Out: { type: 'atlas:ready' } once structures are known
 *      { type: 'atlas:select', id, name, ref }   when the user selects a structure
 *
 * Messages only change the view, so any origin may send them.
 */
export function useEmbedBridge() {
  const loaded = useAtlas((s) => s.loaded)
  const selected = useAtlas((s) => s.selected)

  useEffect(() => {
    if (window.parent === window) return
    const f = (e: MessageEvent) => {
      const m = e.data
      if (!m || typeof m !== 'object') return
      const st = useAtlas.getState()
      if (m.type === 'atlas:reset') st.reset()
      if (m.type === 'atlas:show' && Array.isArray(m.ids)) {
        const ids = m.ids.filter((id: unknown) => typeof id === 'string' && st.byId[id as string]) as string[]
        if (ids.length === 1) {
          st.clearIsolate()
          st.focus(ids[0])
        } else if (ids.length > 1) {
          st.isolateGroup(typeof m.label === 'string' ? m.label : 'Selection', ids)
        }
      }
    }
    window.addEventListener('message', f)
    return () => window.removeEventListener('message', f)
  }, [])

  useEffect(() => {
    if (window.parent !== window && loaded) window.parent.postMessage({ type: 'atlas:ready' }, '*')
  }, [loaded])

  useEffect(() => {
    if (window.parent === window || !selected) return
    const s = useAtlas.getState().byId[selected]
    if (s) window.parent.postMessage({ type: 'atlas:select', id: s.id, name: s.name, ref: s.content_ref }, '*')
  }, [selected])
}
