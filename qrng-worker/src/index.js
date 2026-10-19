/**
 * qrng-seed: a tiny Cloudflare Worker that hands out 32-bit seeds drawn from the
 * ANU Quantum Random Number Generator (quantum vacuum fluctuation measurements).
 *
 * Why a proxy? The ANU API key must stay secret, and GitHub Pages is static.
 *
 * Quota safety: the ANU free tier allows 100 requests/month. One ANU request
 * returns 1024 uint16 values = 512 seeds, stored in Workers KV and handed out
 * sequentially (each seed is served once). The pool is refilled at most once
 * every 8 hours (<= 93 requests/month), no matter how much traffic arrives.
 * When the pool runs dry before the next refill window, the Worker returns 503
 * and the website falls back to its classical PRNG.
 */

const ANU_URL = 'https://api.quantumnumbers.anu.edu.au?length=1024&type=uint16';
const REFILL_INTERVAL_MS = 8 * 60 * 60 * 1000;
const POOL_KEY = 'pool';
const ALLOWED_ORIGINS = [
    'https://syedshubha.github.io',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
];

function json(body, status, headers) {
    return new Response(JSON.stringify(body), {
        status,
        headers: { ...headers, 'Content-Type': 'application/json' },
    });
}

async function savePool(env, state) {
    try {
        await env.QRNG_POOL.put(POOL_KEY, JSON.stringify(state));
        return true;
    } catch (e) {
        return false;
    }
}

export default {
    async fetch(request, env) {
        const origin = request.headers.get('Origin') || '';
        const cors = {
            'Access-Control-Allow-Origin': ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0],
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Cache-Control': 'no-store',
            'Vary': 'Origin',
        };

        if (request.method === 'OPTIONS') return new Response(null, { headers: cors });
        if (request.method !== 'GET') return json({ error: 'method not allowed' }, 405, cors);

        // Not configured yet: fail fast without consuming the refill window.
        if (!env.ANU_API_KEY) return json({ source: 'not-configured' }, 503, cors);

        const state = (await env.QRNG_POOL.get(POOL_KEY, 'json')) || { pool: [], cursor: 0, lastAttempt: 0 };
        const now = Date.now();
        const exhausted = () => state.cursor + 1 >= state.pool.length;

        if (exhausted() && now - state.lastAttempt >= REFILL_INTERVAL_MS) {
            // Record the attempt even if it fails, so a broken key or outage never burns the quota.
            state.lastAttempt = now;
            try {
                const res = await fetch(ANU_URL, { headers: { 'x-api-key': env.ANU_API_KEY } });
                const body = await res.json();
                if (res.ok && Array.isArray(body.data) && body.data.length >= 2) {
                    state.pool = body.data;
                    state.cursor = 0;
                    state.fetchedAt = now;
                }
            } catch (e) {
                // fall through: pool stays exhausted until the next refill window
            }
        }

        if (exhausted()) {
            await savePool(env, state);
            return json({
                source: 'depleted',
                retry_after_ms: Math.max(0, REFILL_INTERVAL_MS - (now - state.lastAttempt)),
            }, 503, cors);
        }

        const hi = state.pool[state.cursor];
        const lo = state.pool[state.cursor + 1];
        state.cursor += 2;

        // If the cursor cannot advance, refuse rather than serve the same seed twice.
        if (!(await savePool(env, state))) {
            return json({ source: 'kv-unavailable' }, 503, cors);
        }

        return json({
            source: 'ANU QRNG',
            seed: ((hi << 16) | lo) >>> 0,
            remaining: Math.floor((state.pool.length - state.cursor) / 2),
            fetched_at: state.fetchedAt,
        }, 200, cors);
    },
};
