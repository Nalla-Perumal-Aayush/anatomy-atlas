"""Headless smoke test: serve a build, load the whole body, exercise features, save screenshots.

Usage: python shoot.py <dist dir> <out dir> [port]
"""
import functools
import http.server
import sys
import threading
import time

from playwright.sync_api import sync_playwright

dist, out = sys.argv[1], sys.argv[2]
port = int(sys.argv[3]) if len(sys.argv) > 3 else 8765
Handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=dist)
Handler.log_message = lambda *a, **k: None
srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()


def snap(pg, name, wait=3):
    time.sleep(wait)
    pg.screenshot(path=f"{out}/{name}.png")


with sync_playwright() as p:
    b = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = b.new_page(viewport={"width": 1440, "height": 900}); pg.set_default_timeout(180000)
    logs = []
    pg.on("console", lambda m: m.type in ("error", "warning") and logs.append(f"{m.type}: {m.text[:300]}"))
    pg.on("pageerror", lambda e: logs.append(f"PAGEERROR: {e}"))
    t0 = time.time()
    pg.goto(f"http://127.0.0.1:{port}/index.html")
    pg.wait_for_selector(".layer", timeout=60000)
    snap(pg, "b0_first_region", 6)
    pg.wait_for_function("() => !document.querySelector('.loading-chip, .loader')", timeout=600000)
    print(f"all regions loaded in {time.time() - t0:.0f}s")
    pg.click(".views button:has-text('Anterior')")
    snap(pg, "b1_body_skin", 6)
    pg.click("text=Superficial muscles")
    snap(pg, "b2_superficial_muscles", 5)
    pg.click("text=Bones, organs and brain")
    snap(pg, "b3_bones_organs", 5)
    pg.click("label:has-text('Bones and joints') input")
    snap(pg, "b4_organs_no_bones", 5)
    pg.click("label:has-text('Bones and joints') input")
    pg.click(".region-row:has-text('Brain and spinal cord') button:has-text('Only')")
    pg.click(".views button:has-text('Lateral')")
    snap(pg, "b5_brain_lateral", 6)
    pg.click(".sec-head button:has-text('Whole body')")
    pg.click("text=Skin")
    pg.fill(".search input", "liver")
    time.sleep(1)
    snap(pg, "b6_search", 1)
    pg.keyboard.press("Enter")
    snap(pg, "b7_liver", 6)
    pg.fill(".search input", "sciatic")
    time.sleep(1)
    pg.keyboard.press("Enter")
    snap(pg, "b8_sciatic", 6)
    print("\n".join(logs[-25:]) or "no console errors")
    b.close()
srv.shutdown()
