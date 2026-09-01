const OWNER = "RaoRakurty";
const REPO = "IMAX-70MM-Watcher";
const WORKFLOW = "watch.yml";

function toHex(buffer) {
  return [...new Uint8Array(buffer)].map((value) => value.toString(16).padStart(2, "0")).join("");
}

async function sign(secret, slot) {
  if (!secret || secret.length < 32) throw new Error("DISPATCH_HMAC_SECRET must be at least 32 characters");
  const encoder = new TextEncoder();
  const key = await crypto.subtle.importKey("raw", encoder.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return toHex(await crypto.subtle.sign("HMAC", key, encoder.encode(`imax-ten-minute:${slot}`)));
}

export { sign };

export default {
  async scheduled(event, env, ctx) {
    ctx.waitUntil((async () => {
      if (!env.GITHUB_ACTIONS_TOKEN) throw new Error("GITHUB_ACTIONS_TOKEN is missing");
      const slot = new Date(Math.floor(event.scheduledTime / 600000) * 600000).toISOString();
      const dispatchSignature = await sign(env.DISPATCH_HMAC_SECRET, slot);
      const response = await fetch(`https://api.github.com/repos/${OWNER}/${REPO}/actions/workflows/${WORKFLOW}/dispatches`, {
        method: "POST",
        headers: {
          "Accept": "application/vnd.github+json",
          "Authorization": `Bearer ${env.GITHUB_ACTIONS_TOKEN}`,
          "Content-Type": "application/json",
          "User-Agent": "imax-watcher-cloudflare-cron",
          "X-GitHub-Api-Version": "2022-11-28",
        },
        body: JSON.stringify({
          ref: "main",
          inputs: {
            test_notification: "false",
            scheduler_source: "cloudflare-cron",
            scheduled_slot: slot,
            dispatch_signature: dispatchSignature,
          },
        }),
      });
      if (response.status !== 204) {
        const detail = (await response.text()).slice(0, 500);
        throw new Error(`GitHub dispatch failed: HTTP ${response.status} ${detail}`);
      }
      console.log(JSON.stringify({ event: "workflow_dispatched", slot, status: "accepted" }));
    })());
  },
};
