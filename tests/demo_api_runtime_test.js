"use strict";

const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

class MemoryStorage {
  constructor() {
    this.values = new Map();
  }

  getItem(key) {
    return this.values.has(key) ? this.values.get(key) : null;
  }

  setItem(key, value) {
    this.values.set(key, String(value));
  }

  removeItem(key) {
    this.values.delete(key);
  }
}

function loadAdapter() {
  const localStorage = new MemoryStorage();
  const window = {
    crypto: crypto.webcrypto,
    fetch: globalThis.fetch,
    localStorage,
    location: {
      hostname: "lorenzo-holmes.github.io",
      href: "https://lorenzo-holmes.github.io/ProofOps/",
      protocol: "https:",
      search: "",
    },
  };
  const context = {
    URL,
    URLSearchParams,
    Request,
    Response,
    TextEncoder,
    Uint8Array,
    console,
    setTimeout,
    window,
  };
  const source = fs.readFileSync(path.join(__dirname, "..", "web", "demo-api.js"), "utf8");
  vm.runInNewContext(source, context, { filename: "demo-api.js" });
  assert.equal(window.ProofOpsDemoApi.enabled, true);
  return { api: window.ProofOpsDemoApi, localStorage };
}

async function request(api, route, options = {}) {
  const response = await api.handle(route, options);
  const payload = await response.json();
  assert.equal(response.ok, true, `${options.method || "GET"} ${route}: ${JSON.stringify(payload)}`);
  return payload;
}

async function createAndReachGate(api, scenarioId) {
  let { incident } = await request(api, "/api/incidents", {
    method: "POST",
    body: JSON.stringify({ scenario_id: scenarioId }),
  });
  while (incident.status !== "awaiting_approval") {
    ({ incident } = await request(api, `/api/incidents/${incident.id}/advance`, {
      method: "POST",
      body: "{}",
    }));
  }
  return incident;
}

async function approveAndFinish(api, incident) {
  ({ incident } = await request(api, `/api/incidents/${incident.id}/approve`, {
    method: "POST",
    body: JSON.stringify({ actor: "runtime-test", reason: "verify static flow" }),
  }));
  while (!new Set(["resolved", "rolled_back", "rejected"]).has(incident.status)) {
    ({ incident } = await request(api, `/api/incidents/${incident.id}/advance`, {
      method: "POST",
      body: "{}",
    }));
  }
  return incident;
}

async function main() {
  const { api, localStorage } = loadAdapter();
  api.reset();

  let success = await createAndReachGate(api, "coupon-null-regression");
  success = await approveAndFinish(api, success);
  assert.equal(success.status, "resolved");
  assert.equal(success.events.length, 8);

  let rollback = await createAndReachGate(api, "inventory-timeout-cascade");
  rollback = await approveAndFinish(api, rollback);
  assert.equal(rollback.status, "rolled_back");
  assert.equal(rollback.events.length, 9);

  let rejected = await createAndReachGate(api, "coupon-null-regression");
  ({ incident: rejected } = await request(api, `/api/incidents/${rejected.id}/reject`, {
    method: "POST",
    body: JSON.stringify({ actor: "runtime-test", reason: "reject static flow" }),
  }));
  assert.equal(rejected.status, "rejected");
  assert.equal(rejected.events.length, 6);

  for (const incident of [success, rollback, rejected]) {
    const audit = await request(api, `/api/incidents/${incident.id}/audit`);
    assert.equal(audit.valid, true);
  }

  const stored = JSON.parse(localStorage.getItem(api.storageKey));
  stored.incidents[0].events[0].summary = "tampered summary";
  localStorage.setItem(api.storageKey, JSON.stringify(stored));
  const tamperedAudit = await request(api, `/api/incidents/${stored.incidents[0].id}/audit`);
  assert.equal(tamperedAudit.valid, false);
  const metrics = await request(api, "/api/metrics");
  assert.ok(metrics.audit_integrity_percent < 100);

  localStorage.setItem(api.storageKey, JSON.stringify({ version: 1, incidents: [null] }));
  const recovered = await request(api, "/api/metrics");
  assert.equal(recovered.incidents_total, 3);

  process.stdout.write("demo-api runtime checks passed\n");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
