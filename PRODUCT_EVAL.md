# Product Evaluation — Live Translate

- **Student:** Daragh Moran
- **Date:** 2026-07-13
- **Video demo:** _(pending — paste your 60–90s demo link before submitting)_
- **LLM provider / model:** Anthropic Claude / `claude-sonnet-4-6`
- **Backend target:** `http://localhost:8787` (local) · deployed gateway `https://fde-lt-gw-dm.fly.dev`

## Verdict

> This is shippable. The backend meets every automated criterion (70/70) and every
> SLA with wide margin, and it's deployed on Fly.io as two independent services with
> a working public gateway. The **strongest part is the caching**: a cache hit is
> ~148× faster than a miss (12 ms vs 1762 ms p95) with zero errors, and it fails
> loud on LLM errors rather than silently serving English. The **weakest / open
> item** is the live-website test on a real site (e.g. homedepot.com via the Chrome
> extension), which is still pending and must be completed with screenshots before
> final submission. Two minor production caveats: on Fly the SQLite cache is
> ephemeral (no volume mounted) and the AI service is publicly reachable rather than
> `flycast`-private.

**Rubric score (from `eval/report.json`):** 70 / 70 auto (+ 30 manual — grader)

## 1. Performance & cost (from `benchmark/bench.py`, cold run)

| Metric | Result | SLA | Pass? |
|---|---|---|---|
| Cache hit p95 | 11.9 ms | ≤ 60 ms | ✅ |
| Cache miss p95 | 1762 ms | ≤ 3500 ms | ✅ |
| Cache hit rate | 75.0 % | ≥ 60 % | ✅ |
| Throughput | 1094.6 req/s | ≥ 20 | ✅ |
| Error rate | 0.0 % | ≤ 1 % | ✅ |
| Cost per miss | $0.000158 | — | — |
| Monthly savings from cache | $59.23 | — | — |

Speedup on a cache hit: **~148×** (miss p95 1762 ms → hit p95 12 ms). Cost model at
500,000 translations/mo: **$78.98 no-cache → $19.74 cached** (prices from
`benchmark/sla.json` — Anthropic $3/$15 per Mtok; verify against current published
rates before quoting externally).

## 2. Live-website test

**Permissive-site test — PASSED.** The widget was injected on the provided
Sierra Coffee Roasters demo page (`demo-pages/index.html`) via the console loader,
pointed at the deployed gateway (`https://fde-lt-gw-dm.fly.dev`). The 🌐 widget
rendered, and **Translate page** flipped the page to Mexican Spanish successfully.

**Real-site test — still pending.** The graded test on a real site the student does
not control (default `https://www.homedepot.com`) via the Chrome extension is not yet
run. This is what exercises strict-CSP behavior and is required for final submission.

- **Site tested:** `demo-pages/index.html` (permissive) ✅ · real site (homedepot.com) — _pending_
- **Translated whole page?** Yes, on the demo page (headings, product copy, footer flipped to es-MX)
- **Coverage gaps:** Not fully assessed — requires the real-site test
- **Cache on re-translate:** Backend-proven (2nd identical call `cached:true`, ~0 ms); observe the badge on the real-site test
- **Resilience:** _Pending_ — note if a strict-CSP site blocks injection (that's a real finding, not a backend failure; the extension proxies via its background worker to work around CSP)
- **Screenshots:** _To be attached to submission (before/after on the real site)._

### Sample translations (captured from the deployed gateway)

| Original (EN) | Translation (es-MX) | Numbers/prices/codes kept? | OK? |
|---|---|---|---|
| Add to cart | Agregar al carrito | n/a | ✅ |
| Free shipping on orders over $50. | Envío gratis en pedidos mayores de $50. | `$50` ✅ | ✅ |
| Best sellers | Más vendidos | n/a | ✅ |
| A bold, dark roast built for espresso with a long, sweet finish. | Un tueste oscuro e intenso, hecho para espresso con un final largo y dulce. | n/a | ✅ |
| $14.99 — 12 oz bag (model MB-120) | $14.99 — bolsa de 12 oz (modelo MB-120) | `$14.99`, `MB-120` ✅ | ✅ |
| If you are not completely satisfied, we offer a full refund within 30 days. | Si no estás completamente satisfecho, te ofrecemos un reembolso completo dentro de los 30 días. | `30` ✅ | ✅ |
| Track your shipment | Rastrea tu envío | n/a | ✅ |
| Create an account | Crea una cuenta | n/a | ✅ |

Register is natural Mexican Spanish (informal *tú*: "estás", "te ofrecemos", "Rastrea
tu envío"; "Agregar al carrito", "Más vendidos"), translation-only with no preamble,
and prices/model codes preserved verbatim.

## 3. Dimension scorecard

| Dimension | Pass / Partial / Fail | Evidence |
|---|---|---|
| Translation accuracy | ✅ Pass | 8/8 sample pairs are correct, fluent translations |
| Mexican-Spanish register (es-MX) | ✅ Pass | Informal *tú*, MX-natural phrasing; not Castilian |
| Numbers / prices / codes preserved | ✅ Pass | `$14.99`, `$50`, `MB-120`, `30 days` all kept verbatim |
| Page coverage | ✅ Pass (demo page) | Demo page fully flipped to es-MX; real-site coverage pending |
| Cache effectiveness | ✅ Pass | 75% hit rate; hit 12 ms vs miss 1762 ms p95 (~148×); two-tier memory+SQLite |
| Latency vs SLA | ✅ Pass | All 5 SLAs pass with margin (`bench.py` exits 0) |
| Error handling (no silent English) | ✅ Pass | LLM errors propagate → gateway `502`; no try/except returns input; `400` on bad input |
| Resilience on a real site | ⏳ Pending | Requires the real-site (strict-CSP) test via the extension |
| UX polish | ✅ Pass (demo page) | Widget button + Translate/Restore flow work on the demo page |

**Observability:** structured JSON logs in both services; a single request ID
(inbound `X-Request-Id` reused or generated at the gateway) correlates one request
end-to-end across `gateway.log` and `ai-service.log` (`trace_correlated: true`).
Gateway `/health` nests the AI-service health; `/stats` reports an accurate hit rate.

**Deploy:** both services on Fly.io as separate apps; public gateway health check
passed (`deploy_health_ok: true`, `https://fde-lt-gw-dm.fly.dev/health`).

**Hygiene:** no secrets/junk tracked in git; provided files (`widget/`, `extension/`,
`benchmark/`) unchanged.

## 4. Top fixes before shipping

1. **Complete the live-website test** on a real site (homedepot.com) via the extension pointed at `https://fde-lt-gw-dm.fly.dev`, and attach before/after screenshots — this closes the three pending dimensions and is a hard submission requirement.
2. **Harden the deploy:** mount a Fly volume for `translations.db` so the SQLite cache survives machine restarts in production, and make the AI service `flycast`-private so only the gateway can reach it.
3. **Confirm cost inputs:** the `$/Mtok` prices in `benchmark/sla.json` are placeholders — set them to your provider's current published rates before quoting the monthly cost/savings figures.
