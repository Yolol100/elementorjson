const fs = require('fs');
const path = require('path');
const { test, expect } = require('@playwright/test');

const templateDir = path.resolve(__dirname, '../../templates');
const screenshotDir = path.resolve(__dirname, '../../artifacts/screenshots');
const inventoryPath = path.resolve(__dirname, '../../wordpress-plugin/elementor-json-lab/.runtime/inventory.json');

function buildViewports() {
  const candidates = [
    { name: 'desktop', width: 1440, height: 900 },
    { name: 'tablet', width: 1024, height: 1366 },
    { name: 'mobile', width: 390, height: 844 }
  ];

  if (fs.existsSync(inventoryPath)) {
    const inventory = JSON.parse(fs.readFileSync(inventoryPath, 'utf8'));
    const breakpoints = inventory?.environment?.active_breakpoints || {};
    for (const [name, breakpoint] of Object.entries(breakpoints)) {
      const value = Number(breakpoint?.value);
      if (!Number.isFinite(value) || value < 240 || value > 3840) {
        continue;
      }
      candidates.push({ name: `breakpoint-${name}-at`, width: value, height: Math.max(844, Math.round(value * 1.2)) });
      if (value + 1 <= 3840) {
        candidates.push({ name: `breakpoint-${name}-above`, width: value + 1, height: Math.max(844, Math.round((value + 1) * 1.2)) });
      }
    }
  }

  const seen = new Set();
  return candidates.filter(({ width }) => {
    if (seen.has(width)) return false;
    seen.add(width);
    return true;
  });
}

const viewports = buildViewports();

function slugify(filename) {
  return path.basename(filename, '.json')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

const templates = fs.existsSync(templateDir)
  ? fs.readdirSync(templateDir).filter((name) => name.endsWith('.json')).sort()
  : [];

if (templates.length === 0) {
  test('no templates supplied', async () => {
    test.skip(true, 'Add Elementor JSON files to templates/ to generate previews.');
  });
}

for (const template of templates) {
  const slug = slugify(template);

  for (const viewport of viewports) {
    test(`${template} - ${viewport.name}`, async ({ page }, testInfo) => {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.emulateMedia({ reducedMotion: 'reduce' });

      const browserErrors = [];
      const consoleErrors = [];
      const failedRequests = [];
      const badResponses = [];

      page.on('pageerror', (error) => browserErrors.push(error.message));
      page.on('console', (message) => {
        if (message.type() === 'error') consoleErrors.push(message.text());
      });
      page.on('requestfailed', (request) => {
        const url = request.url();
        if (url.startsWith('http://127.0.0.1:8888/') || url.startsWith('http://localhost:8888/')) {
          failedRequests.push({ url, failure: request.failure(), resourceType: request.resourceType() });
        }
      });
      page.on('response', (response) => {
        const url = response.url();
        if (
          response.status() >= 400 &&
          !url.endsWith('/favicon.ico') &&
          (url.startsWith('http://127.0.0.1:8888/') || url.startsWith('http://localhost:8888/'))
        ) {
          badResponses.push({ url, status: response.status() });
        }
      });

      const response = await page.goto(`/${slug}/`, { waitUntil: 'networkidle' });
      expect(response, 'Expected a WordPress response').not.toBeNull();
      expect(response.ok(), `Expected HTTP success for /${slug}/`).toBeTruthy();

      await expect(page.locator('body')).toBeVisible();
      await expect(page.locator('[data-elementor-type]').first(), 'Expected rendered Elementor markup').toBeVisible();

      const overflow = await page.evaluate(() => ({
        scrollWidth: document.documentElement.scrollWidth,
        clientWidth: document.documentElement.clientWidth
      }));
      expect(overflow.scrollWidth, `Expected no horizontal page overflow: ${JSON.stringify(overflow)}`).toBeLessThanOrEqual(overflow.clientWidth + 1);

      const brokenImages = await page.locator('img').evaluateAll((images) =>
        images.filter((image) => image.complete && image.naturalWidth === 0).map((image) => image.currentSrc || image.src)
      );
      expect(brokenImages, 'Expected no broken rendered images').toEqual([]);

      const focusable = page.locator('a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])');
      if ((await focusable.count()) > 0) {
        await page.keyboard.press('Tab');
        const activeTag = await page.evaluate(() => document.activeElement && document.activeElement.tagName);
        expect(activeTag, 'Expected keyboard focus to move away from BODY').not.toBe('BODY');
      }

      fs.mkdirSync(screenshotDir, { recursive: true });
      const projectName = testInfo.project.name;
      const basename = `${slug}-${projectName}-${viewport.name}`;

      await page.screenshot({
        path: path.join(screenshotDir, `${basename}.png`),
        fullPage: true,
        animations: 'disabled'
      });

      fs.writeFileSync(
        path.join(screenshotDir, `${basename}.json`),
        JSON.stringify({
          template,
          slug,
          browser: projectName,
          viewport,
          reduced_motion: true,
          url: page.url(),
          title: await page.title(),
          browser_errors: browserErrors,
          console_errors: consoleErrors,
          failed_requests: failedRequests,
          bad_responses: badResponses,
          horizontal_overflow: overflow,
          broken_images: brokenImages
        }, null, 2) + '\n'
      );

      expect(browserErrors, 'Expected no uncaught browser errors').toEqual([]);
      expect(consoleErrors, 'Expected no browser console errors').toEqual([]);
      expect(failedRequests, 'Expected no failed same-origin requests').toEqual([]);
      expect(badResponses, 'Expected no same-origin HTTP 4xx/5xx asset responses').toEqual([]);
    });
  }
}
