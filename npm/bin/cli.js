#!/usr/bin/env node

/**
 * npm wrapper for the ScrapeReviews MCP server.
 * Spawns the Python package via uvx (preferred) or python3 -m.
 */

const { spawn } = require("child_process");

function run(command, args) {
  const child = spawn(command, args, {
    stdio: "inherit",
    env: process.env,
  });
  child.on("error", () => null); // handled by exit code
  child.on("exit", (code) => process.exit(code ?? 1));
  return child;
}

// Try uvx first (fast, no install needed)
const uvx = spawn("uvx", ["scrapereviews-mcp"], {
  stdio: "inherit",
  env: process.env,
});

uvx.on("error", () => {
  // uvx not available, fall back to python3 -m
  run("python3", ["-m", "scrapereviews_mcp.server"]);
});

uvx.on("exit", (code) => {
  if (code !== null) process.exit(code);
});
