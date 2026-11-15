import type { SystemKey, Tissue } from './types'

export const APP_LABEL = 'Whole body'
export const MODEL_DIR = './models/body/'
export const DRACO_DIR = './draco/'

// Hosts that refuse .glb/.wasm files (e.g. Claude artifacts): `npm run build:artifact`
// ships models as base64 JSON and uses Draco's plain-JavaScript decoder.
export const MODELS_AS_B64: boolean = import.meta.env.VITE_MODELS_B64 === '1'
export const DRACO_JS_ONLY: boolean = import.meta.env.VITE_DRACO_JS === '1'

// Paste a Google Form or Formspree link here to collect error reports.
// Left empty, the report button shows the text for the tester to copy instead.
export const FEEDBACK_FORM_URL = ''

export const LAYERS: { depth: number; label: string; hint: string }[] = [
  { depth: 1, label: 'Skin', hint: 'Surface regions of the body' },
  { depth: 2, label: 'Superficial fascia', hint: 'Cutaneous nerves, superficial veins, superficial nodes' },
  { depth: 3, label: 'Deep fascia', hint: 'Deep fascia, retinacula, aponeuroses' },
  { depth: 4, label: 'Superficial muscles', hint: 'Facial muscles, trapezius, pectoralis major, superficial limb muscles' },
  { depth: 5, label: 'Deep muscles', hint: 'Deep muscle layers, bursae, tendon sheaths' },
  { depth: 6, label: 'Nerves and vessels', hint: 'Named nerves, arteries, veins and lymph nodes' },
  { depth: 7, label: 'Bones, organs and brain', hint: 'Skeleton, joints, viscera, heart, brain. Turn Bones off to see organs' },
]

export const SYSTEMS: { key: SystemKey; label: string; swatch: string }[] = [
  { key: 'skin', label: 'Skin', swatch: '#dda98c' },
  { key: 'muscular', label: 'Muscles and fascia', swatch: '#b8352e' },
  { key: 'nervous', label: 'Nerves, brain, spinal cord', swatch: '#f5d540' },
  { key: 'vascular', label: 'Heart, vessels, lymph nodes', swatch: '#5b6fd8' },
  { key: 'organs', label: 'Organs and sense organs', swatch: '#c47a6a' },
  { key: 'skeletal', label: 'Bones and joints', swatch: '#eee6d0' },
]

export const TISSUE_LABEL: Record<Tissue, string> = {
  skin: 'Skin',
  fascia: 'Fascia',
  muscle: 'Muscle',
  bursa: 'Bursa',
  tendon_sheath: 'Tendon sheath',
  nerve: 'Nerve',
  artery: 'Artery',
  vein: 'Vein',
  lymph_node: 'Lymph nodes',
  bone: 'Bone',
  cartilage: 'Cartilage',
  ligament: 'Ligament',
  capsule: 'Joint capsule',
  organ: 'Organ',
  heart: 'Heart',
  cns: 'Brain / spinal cord',
  sense_organ: 'Sense organ',
}
