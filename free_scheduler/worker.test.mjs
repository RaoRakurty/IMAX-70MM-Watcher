import assert from "node:assert/strict";
import { createHmac } from "node:crypto";
import test from "node:test";
import worker, { sign } from "./worker.js";

test("HMAC matches the Python dispatch guard format", async () => {
  const secret = "s".repeat(32);
  const slot = "2026-08-31T20:40:00.000Z";
  const expected = createHmac("sha256", secret).update(`imax-ten-minute:${slot}`).digest("hex");
  assert.equal(await sign(secret, slot), expected);
});

test("scheduled handler dispatches the exact UTC slot", async () => {
  const originalFetch = globalThis.fetch;
  let request;
  globalThis.fetch = async (url, options) => {
    request = { url, options };
    return new Response(null, { status: 204 });
  };
  let pending;
  const ctx = { waitUntil(promise) { pending = promise; } };
  try {
    await worker.scheduled(
      { scheduledTime: Date.parse("2026-08-31T20:40:00Z") },
      { GITHUB_ACTIONS_TOKEN: "token", DISPATCH_HMAC_SECRET: "s".repeat(32) },
      ctx,
    );
    await pending;
    const body = JSON.parse(request.options.body);
    assert.equal(body.inputs.scheduler_source, "cloudflare-cron");
    assert.equal(body.inputs.scheduled_slot, "2026-08-31T20:40:00.000Z");
    assert.match(request.options.headers.Authorization, /^Bearer /);
    assert.match(request.url, /actions\/workflows\/watch\.yml\/dispatches$/);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("GitHub rejection fails the scheduled invocation", async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => new Response("forbidden", { status: 403 });
  let pending;
  try {
    await worker.scheduled(
      { scheduledTime: Date.parse("2026-08-31T20:40:00Z") },
      { GITHUB_ACTIONS_TOKEN: "token", DISPATCH_HMAC_SECRET: "s".repeat(32) },
      { waitUntil(promise) { pending = promise; } },
    );
    await assert.rejects(pending, /HTTP 403/);
  } finally {
    globalThis.fetch = originalFetch;
  }
});
