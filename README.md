# Anatomy Atlas

A web-based 3D anatomy atlas for first-year medical students. You can peel the body layer by layer and click any structure to read about it. It covers the whole body: 3,153 structures in 10 regions and 7 depth layers, built from the open Z-Anatomy dataset.

## What's in here

```
pipeline/   Python scripts that turn the Z-Anatomy .blend into web-ready files
  export.py         main exporter (uses the bpy package, no Blender app needed)
  compress.sh       compresses every region bundle (draco or meshopt)
  inventory.py      counts what the .blend holds, by system and region
  depth_tags.csv    which layer each structure sits in (draft, needs review)
  TA2.csv           Terminologia Anatomica 2 table, used for Latin names
  inspect_*.py      small helpers used to explore the .blend file
build/body/         last pipeline output: manifest, metadata, text per region, report.txt
web/                the viewer: Vite + React + React Three Fiber
tools/              gltf-transform CLI setup and the headless screenshot test
LICENSES.md         credits for the models and text
```

## 1. Get the data

Download Z-Anatomy from https://github.com/Z-Anatomy/Models-of-human-anatomy and unzip `Z-Anatomy.zip`. The file you need is `Z-Anatomy/Startup.blend` (about 290 MB). Keep it outside this repo.

## 2. Run the export (Python 3.11)

The `bpy` package only ships for Python 3.11, so give it its own environment.

```bash
python3.11 -m venv bpyenv
bpyenv/bin/pip install bpy numpy
cd pipeline
../bpyenv/bin/python export.py \
  --blend /path/to/Z-Anatomy/Startup.blend \
  --out ../build/body \
  --tags depth_tags.csv --ta2 TA2.csv
```

This takes under a minute. For each region it writes `<region>.raw.glb` and `<region>.content.json`, plus one `metadata.json`, `manifest.json` and `report.txt` for the whole body. Use `--only head,neck` to redo just some regions.

The regions are thorax, abdomen, pelvis, neck, head, both upper limbs, both lower limbs, and brain with spinal cord. The trunk is split by the height of each structure's centre (thresholds at the top of `export.py`). Nerve and vessel tubes are rebuilt at lower resolution (`--curve-bevel`, `--curve-res`) because the source tubes are far denser than a browser needs.

## 3. Compress the models

```bash
cd tools && npm install && cd ..
pipeline/compress.sh $PWD/build/body $PWD/build/body/draco draco
cp build/body/draco/* web/public/models/body/
```

The whole body comes to about 18 MB of models plus 3.7 MB of text. Draco came out smaller than meshopt here (18 MB against 27 MB), and its decoder also has a plain-JavaScript version for hosts that block WebAssembly. The decoder files live in `web/public/draco/`.

The script keeps `--join false` and `--flatten false`. Without them every structure gets merged into one mesh and nothing can be clicked.

## 4. Run the viewer

```bash
cd web
npm install
npm run dev        # local dev server
npm run build      # static site in web/dist, ready for Netlify or GitHub Pages
```

`web/dist` is plain static files, so any static host works. All paths are relative, so it also works from a sub-folder.

### Deploying on GitHub Pages

The repo includes `.github/workflows/deploy.yml`, which builds `web/` and publishes it on every push to `main`. One-time setup: in the repo go to Settings, then Pages, and under "Build and deployment" set Source to "GitHub Actions". The site appears at `https://<username>.github.io/<repo>/`.

On a free GitHub account Pages needs a public repo. GitHub's soft bandwidth limit is 100 GB a month; one full first visit downloads about 22 MB, and browsers cache it for return visits.

The viewer loads the regions one after another (thorax first, brain last), so the body appears piece by piece. It redraws only when something changes, which keeps laptops and phones cool.

`npm run build:artifact` makes the special build used for the Claude preview link. That host refuses .glb and .wasm files, so models get wrapped as base64 JSON and Draco runs its JavaScript decoder.

## 5. Before testers see it

- Set `FEEDBACK_FORM_URL` in `web/src/config.ts` to a Google Form link. Until then, the report button lets testers copy their report text.
- Have a professor check the layers. Muscles count as superficial (layer 4) if they match the `SUPERFICIAL_MUSCLE` list in `export.py`. Cutaneous nerves and superficial veins go to layer 2 by the `SUPERFICIAL_NV` list. Anything else can be overridden per structure in `pipeline/depth_tags.csv`, which works for both sides.
- Read `build/body/report.txt`. It lists the structures with no description, and the known gaps in the source data.

## How the layers work across the body

Layers 1 to 6 peel the same way everywhere. Layer 7 holds bones, organs and the brain together, because in the trunk the organs sit inside the ribs. To see the organs, peel to layer 7 and turn off "Bones and joints". Searching for any structure peels to its layer and ghosts everything above it, so it's always visible.

Search also finds Z-Anatomy groups ("Heart", "Rotator cuff muscles", "Digestive system"). Picking a group isolates all its parts.

## Known gaps

- The lateral and medial cords of the brachial plexus aren't modelled in Z-Anatomy. Only the posterior cord is.
- The heart has no single "Heart" structure. It's 17 parts (chambers, valves, papillary muscles), so search finds it as a group.
- The trunk is split into thorax, abdomen and pelvis by the height of each structure's centre, so long structures (aorta, oesophagus, erector spinae) sit in one region only.
- 235 of 513 muscles have no nerve supply yet. Nerve supply is taken from how Z-Anatomy groups muscles under nerves, and many trunk and head muscles aren't grouped that way.
- 337 of 3,153 structures have no description text, mostly small ligaments, lymph node groups and skin regions.
- Descriptions come from Wikipedia through Z-Anatomy, trimmed to the first 30 paragraphs, and have not been reviewed. Every panel says so.
