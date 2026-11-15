import { create } from 'zustand'
import type { Bundle, BundleStatus, Content, Structure, SystemKey } from './types'

export type ViewPreset = 'anterior' | 'posterior' | 'lateral' | 'medial'

interface AtlasState {
  bundles: Bundle[]
  status: Record<string, BundleStatus>
  structures: Structure[]
  byId: Record<string, Structure>
  content: Record<string, Content>
  loaded: boolean
  partsVersion: number // bumps when a bundle's meshes are ready

  peel: number
  ghostPeeled: boolean
  systems: Record<SystemKey, boolean>
  regions: Record<string, boolean>
  hidden: string[]
  ghosted: string[]
  isolated: string[] | null

  selected: string | null
  hovered: string | null
  focusRequest: { id: string | null; ids?: string[]; region: string | null; preset: ViewPreset | null; n: number }
  isolatedLabel: string | null

  setData: (b: Bundle[], s: Structure[]) => void
  setStatus: (id: string, s: BundleStatus) => void
  addContent: (c: Record<string, Content>) => void
  bumpParts: () => void
  setPeel: (d: number) => void
  toggleGhostPeeled: () => void
  toggleSystem: (k: SystemKey) => void
  toggleRegion: (id: string) => void
  onlyRegion: (id: string) => void
  allRegions: () => void
  select: (id: string | null) => void
  hover: (id: string | null) => void
  hide: (id: string) => void
  unhide: (id: string) => void
  showAll: () => void
  toggleGhost: (id: string) => void
  isolate: (id: string) => void
  isolateGroup: (name: string, ids: string[]) => void
  clearIsolate: () => void
  focus: (id: string) => void
  view: (p: ViewPreset) => void
  reset: () => void
}

const allSystems: Record<SystemKey, boolean> = {
  skin: true, muscular: true, nervous: true, vascular: true, organs: true, skeletal: true,
}

export const useAtlas = create<AtlasState>((set) => ({
  bundles: [],
  status: {},
  structures: [],
  byId: {},
  content: {},
  loaded: false,
  partsVersion: 0,
  peel: 1,
  ghostPeeled: false,
  systems: { ...allSystems },
  regions: {},
  hidden: [],
  ghosted: [],
  isolated: null,
  isolatedLabel: null,
  selected: null,
  hovered: null,
  focusRequest: { id: null, region: null, preset: 'anterior', n: 0 },

  setData: (bundles, structures) =>
    set({
      bundles,
      structures,
      loaded: true,
      byId: Object.fromEntries(structures.map((s) => [s.id, s])),
      regions: Object.fromEntries(bundles.map((b) => [b.id, true])),
      status: Object.fromEntries(bundles.map((b) => [b.id, 'waiting' as BundleStatus])),
    }),
  setStatus: (id, s) => set((st) => ({ status: { ...st.status, [id]: s } })),
  addContent: (c) => set((st) => ({ content: { ...st.content, ...c } })),
  bumpParts: () => set((st) => ({ partsVersion: st.partsVersion + 1 })),
  setPeel: (peel) => set({ peel }),
  toggleGhostPeeled: () => set((s) => ({ ghostPeeled: !s.ghostPeeled })),
  toggleSystem: (k) => set((s) => ({ systems: { ...s.systems, [k]: !s.systems[k] } })),
  toggleRegion: (id) => set((s) => ({ regions: { ...s.regions, [id]: !s.regions[id] } })),
  onlyRegion: (id) =>
    set((s) => ({
      regions: Object.fromEntries(s.bundles.map((b) => [b.id, b.id === id])),
      focusRequest: { id: null, region: id, preset: null, n: s.focusRequest.n + 1 },
    })),
  allRegions: () =>
    set((s) => ({
      regions: Object.fromEntries(s.bundles.map((b) => [b.id, true])),
      focusRequest: { id: null, region: null, preset: 'anterior', n: s.focusRequest.n + 1 },
    })),
  select: (selected) => set({ selected }),
  hover: (hovered) => set({ hovered }),
  hide: (id) =>
    set((s) => ({
      hidden: s.hidden.includes(id) ? s.hidden : [...s.hidden, id],
      selected: s.selected === id ? null : s.selected,
    })),
  unhide: (id) => set((s) => ({ hidden: s.hidden.filter((h) => h !== id) })),
  showAll: () => set({ hidden: [], ghosted: [], isolated: null, isolatedLabel: null }),
  toggleGhost: (id) =>
    set((s) => ({
      ghosted: s.ghosted.includes(id) ? s.ghosted.filter((g) => g !== id) : [...s.ghosted, id],
    })),
  isolate: (id) =>
    set((s) => ({
      isolated: [id],
      isolatedLabel: null,
      selected: id,
      focusRequest: { id, region: null, preset: null, n: s.focusRequest.n + 1 },
    })),
  isolateGroup: (name, ids) =>
    set((s) => ({
      isolated: ids,
      isolatedLabel: name,
      selected: null,
      focusRequest: { id: null, ids, region: null, preset: null, n: s.focusRequest.n + 1 },
    })),
  clearIsolate: () => set({ isolated: null, isolatedLabel: null }),
  focus: (id) =>
    set((s) => {
      const st = s.byId[id]
      // show it in context: its region and system on, peeled to its layer, layers above it ghosted
      const regions = st && !s.regions[st.region] ? { ...s.regions, [st.region]: true } : s.regions
      const systems = st && !s.systems[st.system] ? { ...s.systems, [st.system]: true } : s.systems
      const peel = st ? st.depth : s.peel
      const ghostPeeled = st && st.depth !== s.peel ? st.depth > 1 : s.ghostPeeled
      return {
        selected: id,
        regions,
        systems,
        peel,
        ghostPeeled,
        hidden: s.hidden.filter((h) => h !== id),
        focusRequest: { id, region: null, preset: null, n: s.focusRequest.n + 1 },
      }
    }),
  view: (preset) => set((s) => ({ focusRequest: { id: null, region: null, preset, n: s.focusRequest.n + 1 } })),
  reset: () =>
    set((s) => ({
      peel: 1,
      ghostPeeled: false,
      systems: { ...allSystems },
      regions: Object.fromEntries(s.bundles.map((b) => [b.id, true])),
      hidden: [],
      ghosted: [],
      isolated: null,
      isolatedLabel: null,
      selected: null,
      focusRequest: { id: null, region: null, preset: 'anterior', n: s.focusRequest.n + 1 },
    })),
}))

export type DrawMode = 'solid' | 'ghost' | 'off'

export function drawMode(s: Structure, st: AtlasState): DrawMode {
  if (st.isolated) return st.isolated.includes(s.id) ? 'solid' : 'off'
  if (!st.regions[s.region] || !st.systems[s.system] || st.hidden.includes(s.id)) return 'off'
  if (s.depth < st.peel) return st.ghostPeeled ? 'ghost' : 'off'
  if (st.ghosted.includes(s.id)) return 'ghost'
  return 'solid'
}
