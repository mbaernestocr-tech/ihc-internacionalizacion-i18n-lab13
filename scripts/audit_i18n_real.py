# -*- coding: utf-8 -*-
# ES: Fuente B (guía v5 §4.6): auditoría REAL de internacionalización de 14 sitios financieros/bursátiles (7 PE + 7 INT).
#     Mide: lang, dir, charset declarado, hreflang, selector de idioma (heurística), idiomas ofrecidos, respuesta a Accept-Language
#     (es-PE frente a ja-JP), formato de fecha/número visible, banderas como idioma, mención de lenguas originarias. Declara fecha/hora.
#     Los fallos de carga se REGISTRAN y no se promedian. Es la PÁGINA DE INICIO de un solo día: no es un veredicto del sitio.
# EN: Source B: real i18n audit of 14 finance sites. Failures are recorded, never hidden.
import csv, datetime, os, re, time
from playwright.sync_api import sync_playwright
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here)
EVID = os.path.join(root, 'evidencias_auditoria'); os.makedirs(EVID, exist_ok=True)
CH = os.environ.get('CHROME_PATH', r'C:\Program Files\Google\Chrome\Application\chrome.exe')   # ajuste la ruta de Chrome o Chromium
SITIOS = [
    ('BVL (Bolsa de Valores de Lima)', 'PE', 'https://www.bvl.com.pe/'),
    ('SMV (Superintendencia del Mercado de Valores)', 'PE', 'https://www.smv.gob.pe/'),
    ('BCRP (Banco Central de Reserva)', 'PE', 'https://www.bcrp.gob.pe/'),
    ('SBS (Superintendencia de Banca)', 'PE', 'https://www.sbs.gob.pe/'),
    ('BCP (Banco de Crédito)', 'PE', 'https://www.viabcp.com/'),
    ('Interbank', 'PE', 'https://interbank.pe/'),
    ('BBVA Perú', 'PE', 'https://www.bbva.pe/'),
    ('Yahoo Finance', 'INT', 'https://finance.yahoo.com/'),
    ('Investing.com', 'INT', 'https://www.investing.com/'),
    ('NYSE', 'INT', 'https://www.nyse.com/'),
    ('JPX (Bolsa de Tokio)', 'INT', 'https://www.jpx.co.jp/'),
    ('Saudi Exchange (Tadawul)', 'INT', 'https://www.saudiexchange.sa/'),
    ('B3 (Bolsa de Brasil)', 'INT', 'https://www.b3.com.br/'),
    ('Interactive Brokers', 'INT', 'https://www.interactivebrokers.com/'),
]
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'
JS = r"""() => {
  const h = document.documentElement, q = s => [...document.querySelectorAll(s)];
  const cs = (document.querySelector('meta[charset]')||{}).getAttribute ? document.querySelector('meta[charset]').getAttribute('charset') :
             ((document.querySelector('meta[http-equiv="Content-Type" i]')||{content:''}).content.match(/charset=([^;]+)/i)||[,''])[1];
  const hl = q('link[rel~="alternate"][hreflang]').map(l => l.getAttribute('hreflang'));
  const sel = q('a,button,select,option,[role=button],[role=menuitem]');
  const rx = /^(es|en|fr|de|pt|ja|ar|zh|ru|it|español|english|français|deutsch|português|日本語|العربية|中文|quechua|runasimi|aimara|idioma|language|lang|语言|言語)\b/i;
  const sw = sel.filter(e => { const t=(e.innerText||e.textContent||'').trim(); return t.length>0 && t.length<22 && rx.test(t) || /language|idioma|lang-?switch|languageselector/i.test(e.className+' '+e.id+' '+(e.getAttribute('aria-label')||'')); });
  const flags = q('img[src*="flag" i],img[alt*="flag" i],img[alt*="bandera" i],[class*="flag" i]').length;
  const body = (document.body.innerText||'').slice(0,20000);
  const dt = (body.match(/\b\d{1,2}[\/.-]\d{1,2}[\/.-]\d{2,4}\b/)||[''])[0] || (body.match(/\b\d{1,2} (de )?(ene|feb|mar|abr|may|jun|jul|ago|set|sep|oct|nov|dic|jan|apr|aug|dec)[a-z]*\.? (de )?\d{4}\b/i)||[''])[0];
  const nm = (body.match(/\b\d{1,3}([.,]\d{3})+([.,]\d{1,4})?\b|\b\d+[.,]\d{2}\b/)||[''])[0];
  const ori = /quechua|runasimi|aimara|aymara|asháninka|shipibo/i.test(body + ' ' + hl.join(' '));
  const langs = [...new Set(sw.map(e => (e.getAttribute('lang')||e.getAttribute('hreflang')||'').toLowerCase()).filter(Boolean).concat(hl.map(x=>x.toLowerCase())))];
  return {lang: h.getAttribute('lang')||'', dir: h.getAttribute('dir')||'', charset: cs||'', hreflang: hl.length, idiomas: langs.slice(0,12).join(' '),
          selector: sw.length>0, flags, fecha: dt, numero: nm, originarias: ori, texto: body.length, title: document.title.slice(0,80)};
}"""
rows = []
ahora = lambda: datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
def visita(b, url, loc):
    ctx = b.new_context(locale=loc, user_agent=UA, viewport={'width': 1366, 'height': 900}, extra_http_headers={'Accept-Language': loc + ',' + loc.split('-')[0] + ';q=0.8'})
    pg = ctx.new_page(); st = 0; d = {}; err = ''
    try:
        r = pg.goto(url, wait_until='domcontentloaded', timeout=40000); st = r.status if r else 0
        try: pg.wait_for_load_state('networkidle', timeout=10000)
        except Exception: pass
        for intento in range(3):                      # las páginas con redirecciones tardías destruyen el contexto: se reintenta
            try:
                time.sleep(2.5 if intento else 1.2); d = pg.evaluate(JS); d['url_final'] = pg.url; d['pg'] = pg; break
            except Exception as e2:
                if intento == 2: raise e2
    except Exception as e:
        err = str(e).splitlines()[0][:120]
    return ctx, pg, st, d, err
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CH, headless=True)
    for nombre, pais, url in SITIOS:
        f = dict(sitio=nombre, pais=pais, url=url, fecha_hora=ahora(), estado='', http='', lang='', dir='', charset='', hreflang=0, idiomas_detectados='',
                 selector_idioma='', banderas_como_idioma=0, fecha_visible='', numero_visible='', lenguas_originarias='', lang_con_es_PE='', lang_con_ja_JP='',
                 url_final_es_PE='', url_final_ja_JP='', responde_accept_language='', puntaje_i18n=0, nota='')
        ctx, pg, st, d, err = visita(b, url, 'es-PE'); f['http'] = st
        cuerpo = ''
        try: cuerpo = (pg.inner_text('body') or '')[:3000].lower()
        except Exception: pass
        if err or st >= 400 or (len(cuerpo) < 800 and any(k in cuerpo for k in ['access denied', 'acceso denegado', 'captcha', 'verify you are human', 'forbidden', 'just a moment', 'blocked'])):
            f['estado'] = 'NO VÁLIDA'; f['nota'] = (err or f'bloqueo o error HTTP {st}; no se promedia')
        else:
            f['estado'] = 'VÁLIDA'; f['lang'] = d['lang'] or '(vacío)'; f['dir'] = d['dir'] or '(vacío)'; f['charset'] = d['charset'] or '(no declarado en meta)'
            f['hreflang'] = d['hreflang']; f['idiomas_detectados'] = d['idiomas']; f['selector_idioma'] = 'sí' if d['selector'] else 'no detectado'
            f['banderas_como_idioma'] = d['flags']; f['fecha_visible'] = d['fecha']; f['numero_visible'] = d['numero']; f['lenguas_originarias'] = 'sí' if d['originarias'] else 'no'
            f['lang_con_es_PE'] = d['lang'] or '(vacío)'; f['url_final_es_PE'] = d['url_final']
            try: pg.screenshot(path=os.path.join(EVID, 'S13_' + re.sub(r'[^a-z0-9]+', '', nombre.split()[0].lower()) + '.png'))
            except Exception: pass
            ctx.close()
            ctx2, pg2, st2, d2, err2 = visita(b, url, 'ja-JP')
            if not err2 and d2:
                f['lang_con_ja_JP'] = d2['lang'] or '(vacío)'; f['url_final_ja_JP'] = d2['url_final']
                cambia = (d2['url_final'] != d['url_final']) or ((d2['lang'] or '') != (d['lang'] or ''))
                f['responde_accept_language'] = 'sí' if cambia else 'no'
            else: f['responde_accept_language'] = 'no medible'
            ctx2.close()
            # Puntaje 0-10 (heurístico y declarado en la guía): lang(2) charset(1) hreflang(2) selector(2) Accept-Language(2) sin banderas como idioma(1)
            pt = (2 if d['lang'] else 0) + (1 if d['charset'] else 0) + (2 if d['hreflang'] > 0 else 0) + (2 if d['selector'] else 0) + \
                 (2 if f['responde_accept_language'] == 'sí' else 0) + (1 if d['flags'] == 0 else 0)
            f['puntaje_i18n'] = pt
            f['nota'] = 'solo página de inicio; heurística'
        try: ctx.close()
        except Exception: pass
        rows.append(f); print(f['estado'], '|', nombre, '|', f['lang'], '|', f['hreflang'], '|', f['puntaje_i18n'], '|', f['nota'], flush=True)
    b.close()
with open(os.path.join(root, 'datos', 'auditoria_i18n_sitios_reales.csv'), 'w', newline='', encoding='utf-8-sig') as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print('VÁLIDAS:', sum(1 for r in rows if r['estado'] == 'VÁLIDA'), 'de', len(rows))
