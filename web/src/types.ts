export type SystemKey = 'skin' | 'muscular' | 'nervous' | 'vascular' | 'organs' | 'skeletal'

export type Tissue =
  | 'skin' | 'fascia' | 'muscle' | 'bursa' | 'tendon_sheath' | 'nerve' | 'artery' | 'vein'
  | 'lymph_node' | 'bone' | 'cartilage' | 'ligament' | 'capsule' | 'organ' | 'heart' | 'cns'
  | 'sense_organ'

export interface Structure {
  id: string
  name: string
  source_name: string
  side: 'right' | 'left' | 'midline'
  region: string
  system: SystemKey
  tissue: Tissue
  depth: number
  depth_note: string
  groups: string[]
  content_ref: string | null
  content_shared_from: string | null
  innervation: string[]
  latin: string | null
  ta2_id: string | null
}

export interface Content {
  title: string | null
  paragraphs: string[]
  source_url: string | null
  truncated?: boolean
  source: string
  reviewed_by: string | null
  reviewed_on: string | null
}

export interface Bundle {
  id: string
  label: string
  count: number
  model: string
  content: string
}

export type BundleStatus = 'waiting' | 'loading' | 'ready' | 'error'
