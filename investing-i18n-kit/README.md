# investing_i18n_kit — internacionalización del «Sistema Web Integrado Investing AI»

Kit mínimo (JavaScript puro, sin dependencias) para internacionalizar su sitio de la Semana 13.

| Archivo | Para qué sirve |
|---|---|
| `i18n.js` | `I18N.t()`, `num/money/pct/dt/rel`, `sort` (Intl.Collator), plurales (Intl.PluralRules), `dir` RTL, pseudolocalización |
| `locales/es-PE.json`, `en-US.json`, `ar-EG.json`, `ja-JP.json` | Cadenas de ejemplo externalizadas (borrador de traducción) |
| `locales/qu-PE.json` | **Borrador** en quechua con pocas cadenas; las demás caen a `es-PE`. Requiere revisión de hablante nativo |

## Uso en 5 líneas
```html
<script src="i18n.js"></script>
<script>
  Promise.all(['es-PE','en-US','ar-EG','ja-JP','qu-PE'].map(l => fetch('locales/'+l+'.json').then(r => r.json())))
    .then(a => { I18N.load(Object.fromEntries(['es-PE','en-US','ar-EG','ja-JP','qu-PE'].map((l,i)=>[l,a[i]])));
                 I18N.set({locale:'ar-EG', tz:'America/Lima'}); I18N.apply(); });
</script>
<h1 data-i18n="brand"></h1>
```
(Sirva el sitio con `python -m http.server 8000`; `fetch()` no funciona con doble clic.)

## Reglas que el kit NO resuelve por usted
1. Cantidad y divisa se conservan: cambiar de idioma **no** convierte divisas (`I18N.money(125430.5,'USD')`).
2. Los precios del sistema son sintéticos; los formatos sí son reales (`Intl`).
3. Las traducciones al árabe, japonés y quechua son borradores generados con IA: **requieren revisión humana competente**.
4. Use CSS lógico (`margin-inline-start`, `text-align:start`) y nunca ancho fijo en etiquetas.
5. Gráficos (ECharts): pase `locale` y espeje el eje con `inverse` en RTL; no incruste texto en imágenes.
