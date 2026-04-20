#!/usr/bin/env node

const fs = require("fs");
const os = require("os");
const path = require("path");
const { spawn } = require("child_process");
const { createRequire } = require("module");

const frontendRequire = createRequire(
  path.join(__dirname, "..", "..", "ai-pic-frontend", "package.json"),
);
const { chromium } = frontendRequire("@playwright/test");

async function delay(ms) {
  await new Promise((resolve) => setTimeout(resolve, ms));
}

async function waitForJsonVersion(debugUrl, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`${debugUrl.replace(/\/$/, "")}/json/version`);
      if (response.ok) {
        return await response.json();
      }
    } catch (_) {
      // keep polling
    }
    await delay(250);
  }
  throw new Error(`Timed out waiting for Chrome DevTools at ${debugUrl}`);
}

function resolveChromeExecutable() {
  const candidates = [
    process.env.HARNESS_CHROME_EXECUTABLE,
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    chromium.executablePath(),
  ].filter(Boolean);
  return candidates.find((candidate) => fs.existsSync(candidate)) || null;
}

async function launchChromeForCdp(debugPort) {
  const executablePath = resolveChromeExecutable();
  if (!executablePath) {
    throw new Error("No Chrome-compatible executable was found for CDP launch");
  }
  const userDataDir = fs.mkdtempSync(path.join(os.tmpdir(), "ai-video-studio-cdp-"));
  const child = spawn(
    executablePath,
    [
      "--headless=new",
      "--disable-gpu",
      "--disable-dev-shm-usage",
      "--disable-features=Translate,OptimizationGuideModelDownloading",
      "--disable-background-networking",
      "--no-first-run",
      "--no-default-browser-check",
      "--no-sandbox",
      `--remote-debugging-port=${debugPort}`,
      `--user-data-dir=${userDataDir}`,
      "about:blank",
    ],
    { stdio: "ignore" },
  );
  return { child, userDataDir };
}

function summarizeNode(node) {
  if (!node) {
    return null;
  }
  if (typeof node === "string") {
    return node;
  }
  const summary = {
    role: node.role || null,
    name: node.name || null,
  };
  if (node.children && node.children.length) {
    summary.children = node.children.slice(0, 20).map(summarizeNode);
  }
  return summary;
}

async function collectDomSnapshot(page) {
  const accessibility = await page.accessibility.snapshot({ interestingOnly: true });
  const dom = await page.evaluate(() => {
    const text = (value) => (value || "").replace(/\s+/g, " ").trim();
    return {
      title: document.title,
      url: location.href,
      headings: [...document.querySelectorAll("h1,h2,h3,[role='heading']")]
        .map((el) => text(el.textContent))
        .filter(Boolean)
        .slice(0, 20),
      buttons: [...document.querySelectorAll("button,[role='button']")]
        .map((el) => text(el.textContent))
        .filter(Boolean)
        .slice(0, 20),
      links: [...document.querySelectorAll("a")]
        .map((el) => ({
          text: text(el.textContent),
          href: el.href || "",
        }))
        .filter((item) => item.text)
        .slice(0, 20),
      inputs: [...document.querySelectorAll("input,textarea,select")]
        .map((el) => ({
          tag: el.tagName.toLowerCase(),
          name: el.getAttribute("name"),
          type: el.getAttribute("type"),
          placeholder: el.getAttribute("placeholder"),
        }))
        .slice(0, 20),
      bodyTextSample: text(document.body?.innerText || "").slice(0, 2000),
    };
  });
  return {
    ...dom,
    accessibility: summarizeNode(accessibility),
  };
}

async function loginIfNeeded(page, config) {
  if (!config.requiresAuth || !config.username || !config.password) {
    return;
  }
  await page.goto(`${config.baseUrl.replace(/\/$/, "")}/login`, {
    waitUntil: "networkidle",
  });
  await page.fill('input[name="username"]', config.username);
  await page.fill('input[name="password"]', config.password);
  await Promise.all([
    page.waitForLoadState("networkidle"),
    page.click('button[type="submit"]'),
  ]);
}

async function openWithEngine(engine, config) {
  let browser = null;
  let context = null;
  let launched = null;
  try {
    if (engine === "chrome_devtools_mcp") {
      try {
        await waitForJsonVersion(config.debugUrl, 1200);
      } catch (_) {
        launched = await launchChromeForCdp(config.debugPort);
        await waitForJsonVersion(config.debugUrl, 8000);
      }
      browser = await chromium.connectOverCDP(config.debugUrl);
      context = browser.contexts()[0] || (await browser.newContext());
    } else {
      const executablePath = resolveChromeExecutable();
      browser = await chromium.launch({
        headless: true,
        ...(executablePath ? { executablePath } : {}),
      });
      context = await browser.newContext();
    }

    const page = context.pages()[0] || (await context.newPage());
    const consoleMessages = [];
    const network = [];

    page.on("console", (msg) => {
      consoleMessages.push({
        type: msg.type(),
        text: msg.text(),
      });
    });
    page.on("response", async (response) => {
      network.push({
        event: "response",
        method: response.request().method(),
        status: response.status(),
        url: response.url(),
      });
    });
    page.on("requestfailed", (request) => {
      network.push({
        event: "requestfailed",
        method: request.method(),
        status: null,
        url: request.url(),
        failure: request.failure()?.errorText || "unknown",
      });
    });

    await loginIfNeeded(page, config);
    await page.goto(config.url, { waitUntil: "networkidle" });
    const domSnapshot = await collectDomSnapshot(page);
    const bodyIncludesRequiredText = await page.evaluate(
      (requiredText) => document.body?.innerText?.includes(requiredText) || false,
      config.requiredText,
    );
    await page.screenshot({ path: config.screenshotPath, fullPage: true });

    return {
      engine,
      ok: bodyIncludesRequiredText,
      currentUrl: page.url(),
      title: await page.title(),
      console: consoleMessages.slice(-50),
      network: network.slice(-50),
      domSnapshot,
      debugUrl: engine === "chrome_devtools_mcp" ? config.debugUrl : null,
    };
  } finally {
    try {
      if (context && engine !== "chrome_devtools_mcp") {
        await context.close();
      }
    } catch (_) {
      // ignore
    }
    try {
      if (browser) {
        await browser.close();
      }
    } catch (_) {
      // ignore
    }
    if (launched) {
      launched.child.kill("SIGTERM");
      fs.rmSync(launched.userDataDir, { recursive: true, force: true });
    }
  }
}

async function main() {
  const config = JSON.parse(process.argv[2]);
  const engine = process.argv[3];
  const result = await openWithEngine(engine, config);
  process.stdout.write(JSON.stringify(result));
}

main().catch((error) => {
  process.stderr.write(String(error && error.stack ? error.stack : error));
  process.exit(1);
});
