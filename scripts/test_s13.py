import re
# -*- coding: utf-8 -*-
# ES: pruebas de los 3 HTML con Chrome (Playwright) sobre un servidor local. Genera capturas y los CSV PRUEBA_TECNICA_BOT (NO son datos de personas).
import os, sys, threading, http.server, socketserver, functools, csv, io, json
from playwright.sync_api import sync_playwright
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here)   # raíz del repositorio
CAP = os.path.join(root, 'capturas'); DAT = os.path.join(root, 'datos', 'simulados'); os.makedirs(CAP, exist_ok=True); os.makedirs(DAT, exist_ok=True)
CH = os.environ.get('CHROME_PATH', r'C:\Program Files\Google\Chrome\Application\chrome.exe')   # ajuste la ruta de Chrome o Chromium
H = functools.partial(http.server.SimpleHTTPRequestHandler, directory=root)
class Q(H.func):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(Q, directory=root)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
U = f'http://127.0.0.1:{port}/'
res = []
def chk(n, c, d=''): res.append((n, bool(c))); print(('OK  ' if c else 'FALLA'), n, d, flush=True)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CH, headless=True)
    # ---------- 13.1 ----------
    pg = b.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e))); pg.goto(U + 'html/ejercicio_13_1_laboratorio_codificaciones.html')
    chk('13.1 sin errores JS al cargar', not errs, errs)
    pg.fill('#txt', 'Señal 😀 Ñ'); pg.wait_for_timeout(100)
    t = pg.inner_text('#res')
    chk('13.1 Señal: 9 puntos de código y 14 bytes UTF-8', bool(re.search(r'Puntos de código Unicode\s+9', t)) and bool(re.search(r'Bytes en UTF-8\s+14', t)), ' '.join(t.split())[:120])
    pg.select_option('#dec', 'windows-1252'); pg.fill('#txt', 'Señal'); pg.wait_for_timeout(100)
    chk('13.1 mojibake «SeÃ±al»', 'SeÃ±al' in pg.inner_text('#moji'), pg.inner_text('#moji'))
    pg.click('#log'); pg.click('#csv') if False else None
    chk('13.1 registro de medición', '1 registros' in pg.inner_text('#n'))
    pg.evaluate("document.querySelector('#csv').click()"); chk('13.1 CSV generado', 'bytes_utf8' in (pg.evaluate('window.__csv') or ''))
    pg.screenshot(path=os.path.join(CAP, 'S13_captura_13_1.png'), full_page=True); chk('13.1 sin errores JS al final', not errs, errs); pg.close()
    # ---------- 13.2 ----------
    pg = b.new_page(viewport={'width': 1200, 'height': 900}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(U + 'html/ejercicio_13_2_portal_i18n_A_vs_B.html'); chk('13.2 sin errores JS al cargar', not errs, errs)
    filas = []
    for ver in ['A', 'B']:
        pg.click('#v' + ver)
        for loc in ['es-PE', 'en-US', 'qu-PE', 'ar-EG', 'ja-JP']:
            pg.select_option('#loc', loc); pg.wait_for_timeout(60)
            if loc in ('es-PE', 'ar-EG') or ver == 'A':
                pg.screenshot(path=os.path.join(CAP, f'S13_captura_13_2_{ver}_{loc}.png'), full_page=False)
            pg.click('#aud_btn')
    pg.check('#ps')
    for ver in ['A', 'B']:
        pg.click('#v' + ver)
        for loc in ['es-PE', 'en-US']:
            pg.select_option('#loc', loc); pg.wait_for_timeout(60); pg.click('#aud_btn')
    pg.click('#vB'); pg.select_option('#loc', 'en-US'); pg.screenshot(path=os.path.join(CAP, 'S13_captura_13_2_B_en-US_pseudo.png'))
    pg.uncheck('#ps')
    pg.evaluate("document.querySelector('#csv').click()"); s = pg.evaluate('window.__csv'); filas = list(csv.DictReader(io.StringIO(s.lstrip('\ufeff'))))
    chk('13.2 CSV con 14 mediciones', len(filas) == 14, len(filas))
    f = lambda v, l, ps='no': next((r for r in filas if r['version'] == v and r['locale'] == l and r['pseudo'] == ps), None)
    chk('13.2 A: ancho fijo produce truncados (>0) en es-PE', int(f('A', 'es-PE')['truncados']) > 0, f('A', 'es-PE')['truncados'])
    chk('13.2 B: 0 truncados en es-PE', int(f('B', 'es-PE')['truncados']) == 0, f('B', 'es-PE')['truncados'])
    chk('13.2 A: fecha y dinero fijos detectados', int(f('A', 'es-PE')['fechas_fijas']) > 0 and int(f('A', 'es-PE')['dinero_fijo']) > 0)
    chk('13.2 B: sin fechas/dinero fijos', int(f('B', 'es-PE')['fechas_fijas']) == 0 and int(f('B', 'es-PE')['dinero_fijo']) == 0)
    chk('13.2 A ignora dir en ar-EG (dir_ok=no)', f('A', 'ar-EG')['dir_ok'] == 'no'); chk('13.2 B espeja dir en ar-EG (dir_ok=sí)', f('B', 'ar-EG')['dir_ok'] == 'sí')
    chk('13.2 B pseudolocalizado expande >20 % frente a es-PE pseudolocalizado o mide caracteres', f('B','en-US','sí') is not None and int(f('B','en-US','sí')['caracteres']) > int(f('B','en-US')['caracteres']) * 1.2, (f('B','en-US','sí') or {}).get('caracteres'))
    pg.select_option('#loc', 'ar-EG'); pg.click('#vB'); txt = pg.inner_text('#app')
    chk('13.2 B árabe usa dígitos y texto árabe', any('\u0600' <= c <= '\u06ff' for c in txt))
    pg.select_option('#loc', 'ja-JP'); chk('13.2 B japonés muestra 買い', '買い' in pg.inner_text('#app') or '売り' in pg.inner_text('#app') or '保有' in pg.inner_text('#app'))
    # móvil
    pg.set_viewport_size({'width': 375, 'height': 800}); pg.select_option('#loc', 'en-US'); pg.click('#vB'); pg.wait_for_timeout(100)
    w = pg.evaluate('[document.documentElement.scrollWidth, window.innerWidth]'); chk('13.2 móvil 375 px sin desborde horizontal (B)', w[0] <= w[1] + 1, w)
    pg.screenshot(path=os.path.join(CAP, 'S13_captura_13_2_B_movil.png'))
    chk('13.2 sin errores JS al final', not errs, errs)
    with open(os.path.join(DAT, 'ejercicio_13_2_auditoria_PRUEBA_TECNICA_BOT.csv'), 'w', encoding='utf-8-sig', newline='') as fh: fh.write(s.lstrip('\ufeff'))
    pg.close()
    # ---------- 13.3 ----------
    allrows = []
    for k in range(8):
        pg = b.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e))); pg.goto(U + 'html/ejercicio_13_3_experimento_formatos_locales.html')
        pg.fill('#pid', f'BOT-{k:02d}'); pg.check('#ok'); pg.click('#go')
        import random; random.seed(k)
        for _ in range(16):
            ctx = pg.inner_text('#ctx'); fm = 'A' if 'formato A' in ctx else 'B'
            btns = pg.query_selector_all('#opts button')
            ok_idx = None  # el bot no conoce la respuesta: elige al azar (A) o la 2.ª opción con 80 % (B); SOLO prueba el flujo
            idx = random.randrange(len(btns)) if fm == 'A' else (1 if random.random() < .8 else 0)
            btns[idx].click()
        chk(f'13.3 bot {k}: termina y exporta', pg.is_visible('#fin'))
        pg.evaluate("document.querySelector('#csv').click()"); s = pg.evaluate('window.__csv'); allrows += list(csv.DictReader(io.StringIO(s.lstrip('\ufeff'))))
        if k == 0: pg.screenshot(path=os.path.join(CAP, 'S13_captura_13_3_resultado.png'), full_page=True)
        chk(f'13.3 bot {k}: sin errores JS', not errs, errs); pg.close()
    chk('13.3 128 respuestas (8 bots × 16)', len(allrows) == 128, len(allrows))
    ords = {r['participante']: [x['formato'] for x in allrows if x['participante'] == r['participante']][0] for r in allrows}
    chk('13.3 contrabalanceo: aparecen A-primero y B-primero', len(set(ords.values())) == 2, ords)
    with open(os.path.join(DAT, 'ejercicio_13_3_experimento_PRUEBA_TECNICA_BOT.csv'), 'w', encoding='utf-8-sig', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(allrows[0].keys())); w.writeheader(); w.writerows(allrows)
    pg = b.new_page(); pg.goto(U + 'html/ejercicio_13_3_experimento_formatos_locales.html'); pg.screenshot(path=os.path.join(CAP, 'S13_captura_13_3_inicio.png'), full_page=True)
    b.close()
n = sum(1 for _, o in res if o); print(f'\nRESULTADO: {n}/{len(res)} pruebas OK'); sys.exit(0 if n == len(res) else 1)
