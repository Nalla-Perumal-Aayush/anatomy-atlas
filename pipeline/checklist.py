"""Check the atlas against a first-year anatomy checklist.

Each entry is matched against exported structure names and the Z-Anatomy groups that have exported parts.
A name matches if an atlas name equals it, or contains it (so "Biceps brachii" matches its two heads).

Usage: python checklist.py <metadata.json> <col_members.json> <out.csv>
"""
import csv
import json
import re
import sys

CHECKLIST = {
    "Bones": [
        "Frontal bone", "Parietal bone", "Occipital bone", "Temporal bone", "Sphenoid", "Ethmoid", "Nasal bone",
        "Lacrimal bone", "Zygomatic bone", "Maxilla", "Palatine bone", "Vomer", "Inferior nasal concha", "Mandible",
        "Hyoid bone", "Malleus", "Incus", "Stapes", "Atlas", "Axis", "Sacrum", "Coccyx", "Sternum", "Rib",
        "Clavicle", "Scapula", "Humerus", "Radius", "Ulna", "Scaphoid", "Lunate", "Triquetrum", "Pisiform",
        "Trapezium", "Trapezoid", "Capitate", "Hamate", "Metacarpal", "Phalanx", "Hip bone", "Femur", "Patella",
        "Tibia", "Fibula", "Talus", "Calcaneus", "Navicular", "Cuboid", "Cuneiform", "Metatarsal",
    ],
    "Joints and ligaments": [
        "Articular disc of temporomandibular joint", "Anterior longitudinal ligament", "Posterior longitudinal ligament",
        "Ligamenta flava", "Supraspinous ligament", "Interspinous ligament", "Ligamentum nuchae",
        "Intervertebral disc", "Transverse ligament of atlas", "Alar ligament", "Coracoclavicular ligament",
        "Coraco-acromial ligament", "Glenohumeral ligament", "Glenoid labrum", "Ulnar collateral ligament of elbow",
        "Radial collateral ligament of elbow", "Anular ligament of radius", "Iliofemoral ligament",
        "Pubofemoral ligament", "Ischiofemoral ligament", "Ligament of head of femur", "Acetabular labrum",
        "Anterior cruciate ligament", "Posterior cruciate ligament", "Medial meniscus", "Lateral meniscus",
        "Tibial collateral ligament", "Fibular collateral ligament", "Patellar ligament", "Deltoid ligament",
        "Anterior talofibular ligament", "Calcaneofibular ligament", "Plantar calcaneonavicular ligament",
        "Long plantar ligament", "Sacrospinous ligament", "Sacrotuberous ligament", "Inguinal ligament",
        "Pubic symphysis", "Flexor retinaculum", "Extensor retinaculum",
    ],
    "Muscles of head and neck": [
        "Occipitofrontalis", "Orbicularis oculi", "Orbicularis oris", "Buccinator", "Zygomaticus major",
        "Levator labii superioris", "Depressor anguli oris", "Mentalis", "Platysma", "Masseter", "Temporalis",
        "Medial pterygoid", "Lateral pterygoid", "Superior rectus", "Inferior rectus", "Medial rectus",
        "Lateral rectus", "Superior oblique", "Inferior oblique", "Levator palpebrae superioris",
        "Sternocleidomastoid", "Digastric", "Mylohyoid", "Geniohyoid", "Stylohyoid", "Sternohyoid", "Omohyoid",
        "Sternothyroid", "Thyrohyoid", "Genioglossus", "Hyoglossus", "Styloglossus", "Palatoglossus",
        "Superior pharyngeal constrictor", "Middle pharyngeal constrictor", "Inferior pharyngeal constrictor",
        "Stylopharyngeus", "Cricothyroid", "Posterior crico-arytenoid", "Lateral crico-arytenoid", "Vocalis",
        "Anterior scalene", "Middle scalene", "Posterior scalene", "Longus colli", "Longus capitis",
        "Tensor veli palatini", "Levator veli palatini", "Stapedius", "Tensor tympani",
    ],
    "Muscles of trunk and back": [
        "Trapezius", "Latissimus dorsi", "Rhomboid major", "Rhomboid minor", "Levator scapulae",
        "Serratus posterior superior", "Serratus posterior inferior", "Splenius capitis", "Iliocostalis",
        "Longissimus", "Spinalis", "Semispinalis", "Multifidus", "Rotatores", "Quadratus lumborum",
        "Pectoralis major", "Pectoralis minor", "Subclavius", "Serratus anterior", "External intercostal",
        "Internal intercostal", "Innermost intercostal", "Transversus thoracis", "Diaphragm",
        "External abdominal oblique", "Internal abdominal oblique", "Transversus abdominis", "Rectus abdominis",
        "Pyramidalis", "Cremaster", "Psoas major", "Iliacus", "Levator ani", "Coccygeus",
        "External anal sphincter", "Bulbospongiosus", "Ischiocavernosus", "Superficial transverse perineal",
    ],
    "Muscles of upper limb": [
        "Deltoid", "Supraspinatus", "Infraspinatus", "Teres minor", "Teres major", "Subscapularis",
        "Biceps brachii", "Coracobrachialis", "Brachialis", "Triceps brachii", "Anconeus", "Pronator teres",
        "Flexor carpi radialis", "Palmaris longus", "Flexor carpi ulnaris", "Flexor digitorum superficialis",
        "Flexor digitorum profundus", "Flexor pollicis longus", "Pronator quadratus", "Brachioradialis",
        "Extensor carpi radialis longus", "Extensor carpi radialis brevis", "Extensor digitorum",
        "Extensor digiti minimi", "Extensor carpi ulnaris", "Supinator", "Abductor pollicis longus",
        "Extensor pollicis brevis", "Extensor pollicis longus", "Extensor indicis", "Abductor pollicis brevis",
        "Flexor pollicis brevis", "Opponens pollicis", "Adductor pollicis", "Abductor digiti minimi",
        "Flexor digiti minimi", "Opponens digiti minimi", "Lumbrical", "Dorsal interossei", "Palmar interossei",
        "Palmaris brevis",
    ],
    "Muscles of lower limb": [
        "Gluteus maximus", "Gluteus medius", "Gluteus minimus", "Tensor fasciae latae", "Piriformis",
        "Superior gemellus", "Inferior gemellus", "Obturator internus", "Obturator externus", "Quadratus femoris",
        "Sartorius", "Rectus femoris", "Vastus lateralis", "Vastus medialis", "Vastus intermedius", "Articularis genus",
        "Pectineus", "Adductor longus", "Adductor brevis", "Adductor magnus", "Gracilis", "Biceps femoris",
        "Semitendinosus", "Semimembranosus", "Tibialis anterior", "Extensor hallucis longus",
        "Extensor digitorum longus", "Fibularis tertius", "Fibularis longus", "Fibularis brevis", "Gastrocnemius",
        "Soleus", "Plantaris", "Popliteus", "Flexor digitorum longus", "Flexor hallucis longus", "Tibialis posterior",
        "Extensor digitorum brevis", "Extensor hallucis brevis", "Abductor hallucis", "Flexor digitorum brevis",
        "Quadratus plantae", "Flexor hallucis brevis", "Adductor hallucis",
    ],
    "Heart and great vessels": [
        "Right atrium", "Left atrium", "Right ventricle", "Left ventricle", "Interventricular septum",
        "Tricuspid valve", "Mitral valve", "Pulmonary valve", "Aortic valve", "Papillary muscle",
        "Chordae tendineae", "Pericardium", "Ascending aorta", "Arch of aorta", "Thoracic aorta", "Abdominal aorta",
        "Pulmonary trunk", "Right pulmonary artery", "Left pulmonary artery", "Pulmonary veins",
        "Superior vena cava", "Inferior vena cava", "Coronary sinus", "Right coronary artery",
        "Left coronary artery", "Anterior interventricular artery", "Circumflex artery", "Great cardiac vein",
        "Middle cardiac vein", "Small cardiac vein",
    ],
    "Arteries": [
        "Brachiocephalic trunk", "Common carotid artery", "Internal carotid artery", "External carotid artery",
        "Superior thyroid artery", "Lingual artery", "Facial artery", "Occipital artery", "Posterior auricular artery",
        "Maxillary artery", "Superficial temporal artery", "Middle meningeal artery", "Ophthalmic artery",
        "Vertebral artery", "Basilar artery", "Anterior cerebral artery", "Middle cerebral artery",
        "Posterior cerebral artery", "Subclavian artery", "Internal thoracic artery", "Thyrocervical trunk",
        "Inferior thyroid artery", "Axillary artery", "Brachial artery", "Profunda brachii", "Radial artery",
        "Ulnar artery", "Superficial palmar arch", "Deep palmar arch", "Posterior intercostal artery",
        "Coeliac trunk", "Left gastric artery", "Splenic artery", "Common hepatic artery", "Gastroduodenal artery",
        "Right gastric artery", "Cystic artery", "Superior mesenteric artery", "Jejunal arteries", "Ileal arteries",
        "Ileocolic artery", "Right colic artery", "Middle colic artery", "Inferior mesenteric artery",
        "Left colic artery", "Sigmoid arteries", "Superior rectal artery", "Renal artery", "Testicular artery",
        "Ovarian artery", "Common iliac artery", "Internal iliac artery", "External iliac artery",
        "Uterine artery", "Internal pudendal artery", "Superior gluteal artery", "Inferior gluteal artery",
        "Obturator artery", "Femoral artery", "Deep artery of thigh", "Popliteal artery", "Anterior tibial artery",
        "Posterior tibial artery", "Fibular artery", "Dorsalis pedis artery", "Plantar arch",
    ],
    "Veins": [
        "Internal jugular vein", "External jugular vein", "Anterior jugular vein", "Facial vein",
        "Retromandibular vein", "Superior sagittal sinus", "Inferior sagittal sinus", "Straight sinus",
        "Transverse sinus", "Sigmoid sinus", "Cavernous sinus", "Subclavian vein", "Brachiocephalic vein",
        "Azygos vein", "Hemi-azygos vein", "Axillary vein", "Cephalic vein", "Basilic vein", "Median cubital vein",
        "Hepatic portal vein", "Splenic vein", "Superior mesenteric vein", "Inferior mesenteric vein",
        "Hepatic veins", "Renal vein", "Common iliac vein", "Internal iliac vein", "External iliac vein",
        "Femoral vein", "Great saphenous vein", "Small saphenous vein", "Popliteal vein",
    ],
    "Nerves": [
        "Olfactory nerve", "Optic nerve", "Oculomotor nerve", "Trochlear nerve", "Trigeminal nerve",
        "Ophthalmic nerve", "Maxillary nerve", "Mandibular nerve", "Abducent nerve", "Facial nerve",
        "Vestibulocochlear nerve", "Glossopharyngeal nerve", "Vagus nerve", "Accessory nerve", "Hypoglossal nerve",
        "Lingual nerve", "Inferior alveolar nerve", "Infra-orbital nerve", "Chorda tympani", "Recurrent laryngeal nerve",
        "Superior laryngeal nerve", "Phrenic nerve", "Ansa cervicalis", "Great auricular nerve",
        "Lesser occipital nerve", "Greater occipital nerve", "Suprascapular nerve", "Long thoracic nerve",
        "Dorsal scapular nerve", "Thoracodorsal nerve", "Lateral cord of brachial plexus",
        "Medial cord of brachial plexus", "Posterior cord of brachial plexus", "Musculocutaneous nerve",
        "Median nerve", "Ulnar nerve", "Radial nerve", "Axillary nerve", "Intercostal nerve", "Sympathetic trunk",
        "Greater splanchnic nerve", "Iliohypogastric nerve", "Ilio-inguinal nerve", "Genitofemoral nerve",
        "Lateral cutaneous nerve of thigh", "Femoral nerve", "Saphenous nerve", "Obturator nerve",
        "Superior gluteal nerve", "Inferior gluteal nerve", "Sciatic nerve", "Tibial nerve",
        "Common fibular nerve", "Superficial fibular nerve", "Deep fibular nerve", "Sural nerve",
        "Medial plantar nerve", "Lateral plantar nerve", "Pudendal nerve",
    ],
    "Brain and spinal cord": [
        "Frontal lobe", "Parietal lobe", "Temporal lobe", "Occipital lobe", "Insula", "Precentral gyrus",
        "Postcentral gyrus", "Corpus callosum", "Fornix", "Thalamus", "Hypothalamus", "Caudate nucleus", "Putamen",
        "Globus pallidus", "Internal capsule", "Hippocampus", "Amygdala", "Lateral ventricle", "Third ventricle",
        "Fourth ventricle", "Cerebral aqueduct", "Midbrain", "Pons", "Medulla oblongata", "Cerebellum",
        "Spinal cord", "Cauda equina", "Dura mater", "Arachnoid mater", "Pia mater", "Pituitary gland",
        "Pineal gland", "Optic chiasm", "Mammillary body", "Substantia nigra", "Red nucleus",
    ],
    "Organs: thorax, abdomen, pelvis": [
        "Trachea", "Main bronchus", "Right lung", "Left lung", "Pleura", "Thymus", "Oesophagus", "Stomach",
        "Duodenum", "Jejunum", "Ileum", "Caecum", "Appendix", "Ascending colon", "Transverse colon",
        "Descending colon", "Sigmoid colon", "Rectum", "Anal canal", "Liver", "Gallbladder", "Bile duct",
        "Pancreas", "Spleen", "Greater omentum", "Lesser omentum", "Mesentery", "Peritoneum", "Kidney",
        "Ureter", "Suprarenal gland", "Urinary bladder", "Urethra", "Prostate", "Seminal gland", "Ductus deferens",
        "Testis", "Epididymis", "Penis", "Uterus", "Uterine tube", "Ovary", "Vagina", "Thyroid gland",
        "Parathyroid gland",
    ],
    "Organs: head and neck": [
        "Parotid gland", "Submandibular gland", "Sublingual gland", "Tongue", "Tooth", "Palatine tonsil",
        "Pharyngeal tonsil", "Soft palate", "Pharynx", "Larynx", "Epiglottis", "Thyroid cartilage",
        "Cricoid cartilage", "Arytenoid cartilage", "Vocal fold", "Nasal septum", "Nasal concha",
        "Maxillary sinus", "Frontal sinus", "Eyeball", "Cornea", "Lens", "Retina", "Iris", "Lacrimal gland",
        "Auricle", "External acoustic meatus", "Tympanic membrane", "Cochlea", "Semicircular canals",
    ],
}

meta_p, members_p, out_p = sys.argv[1:4]
meta = json.load(open(meta_p))["structures"]
members = json.load(open(members_p))
exported = {s["source_name"] for s in meta}
names = [s["name"].lower() for s in meta]
groups = {c.lower().strip("()") for c, objs in members.items() if any(o in exported for o in objs)}


def present(term):
    t = term.lower()
    variants = {t, t + " muscle", t + " muscles"}
    if any(v in groups for v in variants) or any(v in names for v in variants):
        return "yes", ""
    hits = [n for n in names if re.search(r"\b" + re.escape(t) + r"\b", n)]
    if hits:
        return "yes", hits[0]
    ghits = [g for g in groups if re.search(r"\b" + re.escape(t) + r"\b", g)]
    if ghits:
        return "yes", ghits[0]
    return "no", ""


rows = []
for system, terms in CHECKLIST.items():
    for t in terms:
        ok, via = present(t)
        rows.append({"system": system, "structure": t, "in_atlas": ok, "matched": via})
with open(out_p, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
for system in CHECKLIST:
    r = [x for x in rows if x["system"] == system]
    miss = [x["structure"] for x in r if x["in_atlas"] == "no"]
    print(f"\n{system}: {len(r) - len(miss)}/{len(r)} present; missing {len(miss)}: {miss}")
