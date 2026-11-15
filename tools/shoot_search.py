"""Quick check: search for structures from the skin layer and screenshot how they are shown.
Usage: python shoot_search.py <dist> <out> <port> <term> [<term> ...]"""
import functools, http.server, sys, threading, time
from playwright.sync_api import sync_playwright
dist, out, port, terms = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4:]
H = functools.partial(http.server.SimpleHTTPRequestHandler, directory=dist); H.log_message = lambda *a, **k: None
srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
with sync_playwright() as p:
    b = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
    pg = b.new_page(viewport={"width": 1440, "height": 900}); pg.set_default_timeout(180000); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(f"http://127.0.0.1:{port}/index.html")
    pg.wait_for_selector(".layer"); pg.wait_for_function("() => !document.querySelector('.loading-chip, .loader')", timeout=600000)
    for t in terms:
        pg.click(".side-foot button:has-text('Reset')"); time.sleep(2)
        pg.fill(".search input", t); time.sleep(1); pg.keyboard.press("Enter"); time.sleep(6)
        pg.screenshot(path=f"{out}/s_{t.replace(' ', '_')}.png")
    print("errors:", errs); b.close()
srv.shutdown()
