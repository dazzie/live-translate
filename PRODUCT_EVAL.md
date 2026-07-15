# Product Evaluation — Live Translate

- **Student:** Daragh Moran
- **Date:** 2026-07-13
- **Video demo:** _(pending — paste your 60–90s demo link before submitting)_
- **LLM provider / model:** provider-swappable via `LLM_PROVIDER`. **Deployed on OpenRouter / `openai/gpt-4o-mini`**; also runs on Anthropic Claude / `claude-sonnet-4-6` (the benchmark numbers below were captured on the Anthropic run).
- **Backend target:** `http://localhost:8787` (local) · deployed gateway `https://fde-lt-gw-dm.fly.dev`

## Verdict

> This is shippable. The backend meets every automated criterion (70/70) and every
> SLA with wide margin, and it's deployed on Fly.io as two independent services with
> a working public gateway. The **strongest part is the caching**: a cache hit is
> ~148× faster than a miss (12 ms vs 1762 ms p95) with zero errors, and it fails
> loud on LLM errors rather than silently serving English. The **live-website test
> now passes**: the Chrome extension, pointed at the deployed gateway, translated a
> real site (`homedepot.com`) end-to-end into Mexican Spanish. Two minor production
> caveats remain: on Fly the SQLite cache is ephemeral (no volume mounted) and the
> AI service is publicly reachable rather than `flycast`-private.

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

**Real-site test — PASSED (two sites).** The Chrome extension (`extension/`, loaded
unpacked) was pointed at the deployed gateway (`https://fde-lt-gw-dm.fly.dev`) and run
on two real sites the student does not control:

1. **`https://www.homedepot.com/`** — a US retail site (product/nav/marketing copy).
2. **`https://www.rte.ie/news/`** — an Irish news site (live news headlines), which
   stress-tests numbers, currency, and dense proper nouns (place names, org names,
   and Irish-language terms such as *Taoiseach*).

In both cases **Check backend** returned `status: ok` with `model: openai/gpt-4o-mini`,
and **Translate this page** flipped the live site's text into Mexican Spanish
end-to-end. The RTÉ samples below were captured from the deployed gateway using the
same `POST /translate/batch` path the "Translate page" button uses.

- **Sites tested:** `demo-pages/index.html` (permissive) ✅ · `homedepot.com` ✅ · `rte.ie/news` ✅
- **Translated whole page?** Yes — product/nav/marketing copy (Home Depot) and news headlines (RTÉ) flipped to es-MX
- **Coverage gaps:** None blocking observed on either site
- **Cache on re-translate:** Proven on the live RTÉ batch — a repeat call returned `cached: [true, true, true]` with batch `latencyMs: 0`
- **Resilience:** Extension injected and translated on real, non-controlled sites (US retail + Irish news) without being blocked
- **Screenshots:** _To be attached to submission (before/after on Home Depot and/or RTÉ)._

### Sample translations — RTÉ News (`rte.ie/news`, captured from the deployed gateway)

| Original (EN) | Translation (es-MX) | Numbers / names kept? | OK? |
|---|---|---|---|
| Tusla experienced a 10% increase in child safety and welfare referrals last year. | Tusla experimentó un aumento del 10% en las referencias de seguridad y bienestar infantil el año pasado. | `10%`, `Tusla` ✅ | ✅ |
| T.Rex skeleton Gus sells for $50.1 million | El esqueleto de T.Rex llamado Gus se vende por $50.1 millones. | `$50.1`, `T.Rex`, `Gus` ✅ | ✅ |
| Emergency services attend large fire in Killarney | Los servicios de emergencia atienden un gran incendio en Killarney. | `Killarney` ✅ | ✅ |
| At least 27 people killed in fire at pub in Thai capital Bangkok | Al menos 27 personas murieron en un incendio en un bar en la capital tailandesa, Bangkok. | `27`, `Bangkok` ✅ | ✅ |
| Taoiseach welcomes Intel's multi-billion euro investment in Leixlip | El Taoiseach da la bienvenida a la inversión de varios miles de millones de euros de Intel en Leixlip. | `Taoiseach`, `Intel`, `Leixlip` ✅ | ✅ |
| Áine Lawlor bids farewell to RTÉ after more than 40 years | Áine Lawlor se despide de RTÉ después de más de 40 años. | `Áine Lawlor`, `RTÉ`, `40` ✅ | ✅ |
| Will you support England in the World Cup semi-final? | ¿Vas a apoyar a Inglaterra en la semifinal de la Copa del Mundo? | n/a | ✅ |

RTÉ register is natural Mexican Spanish (informal *tú*: "¿Vas a apoyar…?"), translation-only
with no preamble. Proper nouns and org/place names are preserved verbatim (`Tusla`, `Gus`,
`Killarney`, `Bangkok`, `Intel`, `Leixlip`, `RTÉ`), the Irish-language title *Taoiseach* is
sensibly left untranslated, percentages/counts/years are kept (`10%`, `27`, `40`), and
currency is preserved while the surrounding word is localized (`$50.1 million` → `$50.1 millones`).
Only genuinely translatable proper nouns are localized (`England` → `Inglaterra`, `World Cup` → `Copa del Mundo`).

### Sample translations — retail / demo content (captured from the deployed gateway)

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
| Translation accuracy | ✅ Pass | 15/15 sample pairs correct and fluent (8 retail/demo + 7 live RTÉ news headlines) |
| Mexican-Spanish register (es-MX) | ✅ Pass | Informal *tú*, MX-natural phrasing; not Castilian |
| Numbers / prices / codes preserved | ✅ Pass | `$14.99`, `$50`, `MB-120`, `30 days` + live RTÉ `10%`, `$50.1`, `27`, `40` and proper nouns (`Tusla`, `Killarney`, `Intel`, `Leixlip`, `RTÉ`, *Taoiseach*) kept verbatim |
| Page coverage | ✅ Pass | Demo page + two real sites (homedepot.com, rte.ie/news) fully flipped to es-MX |
| Cache effectiveness | ✅ Pass | 75% hit rate; hit 12 ms vs miss 1762 ms p95 (~148×); two-tier memory+SQLite; live RTÉ re-translate returned `cached:true`, `latencyMs:0` |
| Latency vs SLA | ✅ Pass | All 5 SLAs pass with margin (`bench.py` exits 0) |
| Error handling (no silent English) | ✅ Pass | LLM errors propagate → gateway `502`; no try/except returns input; `400` on bad input |
| Resilience on a real site | ✅ Pass | Extension translated `homedepot.com` and `rte.ie/news` end-to-end via the deployed gateway |
| UX polish | ✅ Pass | Widget button + Translate/Restore flow work on the demo page and via the extension |

**Observability:** structured JSON logs in both services; a single request ID
(inbound `X-Request-Id` reused or generated at the gateway) correlates one request
end-to-end across `gateway.log` and `ai-service.log` (`trace_correlated: true`).
Gateway `/health` nests the AI-service health; `/stats` reports an accurate hit rate.

**Deploy:** both services on Fly.io as separate apps; public gateway health check
passed (`deploy_health_ok: true`, `https://fde-lt-gw-dm.fly.dev/health`).

**Hygiene:** no secrets/junk tracked in git; provided files (`widget/`, `extension/`,
`benchmark/`) unchanged.

## 4. Top fixes before shipping

1. **Attach artifacts:** the live-website test passed on `homedepot.com` — still need before/after screenshots and the 60–90s demo video pasted in above before final submission.
2. **Harden the deploy:** mount a Fly volume for `translations.db` so the SQLite cache survives machine restarts in production, and make the AI service `flycast`-private so only the gateway can reach it.
3. **Confirm cost inputs:** the `$/Mtok` prices in `benchmark/sla.json` are placeholders — set them to your provider's current published rates before quoting the monthly cost/savings figures. (Note: OpenRouter `gpt-4o-mini` is materially cheaper than the Anthropic rates modeled above.)

## 5. Enhancements beyond the brief

- **Provider-swappable LLM:** `LLM_PROVIDER` selects Anthropic or OpenRouter at runtime (read at call time, so `.env` is honored). Deployed on OpenRouter `openai/gpt-4o-mini`.
- **Token-by-token streaming:** additive SSE endpoint `POST /translate/stream` on the AI service, proxied through the gateway, with a standalone `streaming-demo/` page. Cache hits replay instantly; misses stream live from the LLM and are cached on completion. The provided `widget/` and `extension/` are left untouched.
