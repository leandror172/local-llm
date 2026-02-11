#!/usr/bin/env node
//
// validate-html.js — Headless browser smoke test for LLM-generated HTML/JS
//
// Opens each HTML file in Chromium, listens for runtime errors (console.error,
// uncaught exceptions, failed resource loads), waits for a configurable duration,
// and reports results as JSON to stdout.
//
// Usage:
//   node lib/validate-html.js [options] <file1.html> [file2.html ...]
//
// Options:
//   --wait <ms>         Time to keep page open (default: 2000)
//   --quiet             Only output JSON, suppress progress on stderr
//   --chrome-path <p>   Use a specific Chrome/Chromium binary
//
// Exit codes:
//   0 = all files pass (no errors)
//   1 = one or more files have errors
//   2 = tool error (missing files, Chromium launch failure, etc.)

const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

// ---------------------------------------------------------------------------
// Argument parsing
// ---------------------------------------------------------------------------
const args = process.argv.slice(2);
let waitMs = 2000;
let quiet = false;
let chromePath = null;
const files = [];

for (let i = 0; i < args.length; i++) {
  switch (args[i]) {
    case '--wait':
      waitMs = parseInt(args[++i], 10);
      if (isNaN(waitMs) || waitMs < 0) {
        process.stderr.write('Error: --wait requires a non-negative integer (ms)\n');
        process.exit(2);
      }
      break;
    case '--quiet':
      quiet = true;
      break;
    case '--chrome-path':
      chromePath = args[++i];
      break;
    case '--help':
    case '-h':
      process.stderr.write([
        'Usage: node lib/validate-html.js [options] <file1.html> [file2.html ...]',
        '',
        'Options:',
        '  --wait <ms>         Time to keep page open (default: 2000)',
        '  --quiet             Only output JSON, suppress progress on stderr',
        '  --chrome-path <p>   Use a specific Chrome/Chromium binary',
        '  --help, -h          Show this help message',
        '',
        'Exit codes: 0 = all pass, 1 = any fail, 2 = tool error',
        '',
      ].join('\n'));
      process.exit(0);
      break;
    default:
      if (args[i].startsWith('-')) {
        process.stderr.write(`Unknown option: ${args[i]}\n`);
        process.exit(2);
      }
      files.push(args[i]);
  }
}

if (files.length === 0) {
  process.stderr.write('Error: no HTML files specified\n');
  process.stderr.write('Usage: node lib/validate-html.js [options] <file1.html> [file2.html ...]\n');
  process.exit(2);
}

// ---------------------------------------------------------------------------
// Validate file paths up front
// ---------------------------------------------------------------------------
const resolved = [];
for (const f of files) {
  const abs = path.resolve(f);
  if (!fs.existsSync(abs)) {
    process.stderr.write(`Error: file not found: ${abs}\n`);
    process.exit(2);
  }
  resolved.push(abs);
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
(async () => {
  let browser;
  try {
    const launchOpts = {
      headless: true,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
      ],
    };
    if (chromePath) {
      launchOpts.executablePath = chromePath;
    }

    browser = await puppeteer.launch(launchOpts);
  } catch (err) {
    process.stderr.write(`Error: failed to launch Chromium: ${err.message}\n`);
    if (err.message.includes('shared libraries')) {
      process.stderr.write(
        '\nMissing system libraries. Install them with:\n' +
        '  sudo apt-get install -y ca-certificates fonts-liberation libasound2 \\\n' +
        '    libatk-bridge2.0-0 libatk1.0-0 libcairo2 libcups2 libdbus-1-3 \\\n' +
        '    libexpat1 libfontconfig1 libgbm1 libglib2.0-0 libgtk-3-0 libnspr4 \\\n' +
        '    libnss3 libpango-1.0-0 libpangocairo-1.0-0 libx11-6 libx11-xcb1 \\\n' +
        '    libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 \\\n' +
        '    libxi6 libxrandr2 libxrender1 libxss1 libxtst6\n\n' +
        'Or use --chrome-path to point to an existing Chrome installation.\n'
      );
    }
    process.exit(2);
  }

  const results = [];
  let anyFail = false;

  for (const filePath of resolved) {
    const basename = path.basename(filePath);
    if (!quiet) process.stderr.write(`  validating: ${basename} ... `);

    const startTime = Date.now();
    const errors = [];
    const warnings = [];
    let page;

    try {
      page = await browser.newPage();

      // Collect console messages
      page.on('console', (msg) => {
        const type = msg.type();
        const text = msg.text();

        if (type === 'error') {
          errors.push({
            type: 'console_error',
            text: text,
          });
        } else if (type === 'warning') {
          warnings.push({
            type: 'console_warning',
            text: text,
          });
        }
      });

      // Collect uncaught exceptions
      page.on('pageerror', (err) => {
        // Try to extract line number from stack trace
        let line = null;
        const stackMatch = err.stack && err.stack.match(/:(\d+):\d+/);
        if (stackMatch) {
          line = parseInt(stackMatch[1], 10);
        }
        errors.push({
          type: 'uncaught_exception',
          text: err.message,
          line: line,
        });
      });

      // Collect failed resource loads (images, scripts, etc.)
      page.on('requestfailed', (req) => {
        warnings.push({
          type: 'resource_failed',
          text: `${req.failure().errorText}: ${req.url()}`,
        });
      });

      // Navigate to the file
      const fileUrl = `file://${filePath}`;
      await page.goto(fileUrl, {
        waitUntil: 'domcontentloaded',
        timeout: 10000,
      });

      // Wait for animations/scripts to execute
      await new Promise((resolve) => setTimeout(resolve, waitMs));

    } catch (navErr) {
      errors.push({
        type: 'navigation_error',
        text: navErr.message,
        line: null,
      });
    } finally {
      if (page) await page.close();
    }

    const loadTimeMs = Date.now() - startTime;
    const status = errors.length === 0 ? 'pass' : 'fail';
    if (status === 'fail') anyFail = true;

    const result = {
      file: basename,
      path: filePath,
      status: status,
      errors: errors,
      warnings: warnings,
      error_count: errors.length,
      warning_count: warnings.length,
      load_time_ms: loadTimeMs,
      validated_at: new Date().toISOString(),
    };
    results.push(result);

    if (!quiet) {
      const tag = status === 'pass' ? 'PASS' : `FAIL (${errors.length} error(s))`;
      process.stderr.write(`${tag}  [${loadTimeMs}ms]\n`);
    }
  }

  await browser.close();

  // Output JSON array to stdout
  process.stdout.write(JSON.stringify(results, null, 2) + '\n');

  // Summary on stderr
  if (!quiet) {
    const passed = results.filter((r) => r.status === 'pass').length;
    const failed = results.filter((r) => r.status === 'fail').length;
    process.stderr.write(`\n  ${passed} passed, ${failed} failed out of ${results.length} file(s)\n`);
  }

  process.exit(anyFail ? 1 : 0);
})();
