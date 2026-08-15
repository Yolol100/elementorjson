const fs = require('fs');
const path = require('path');
const { test, expect } = require('@playwright/test');
const AxeBuilder = require('@axe-core/playwright').default;

const templateDir = path.resolve(__dirname, '../../templates');
const screenshotDir = path.resolve(__dirname, '../../artifacts/screenshots');
const inventoryPath = path.resolve(__dirname, '../../wordpress-plugin/elementor-json-lab/.runtime/inventory.json');

function loadViewports() {
  const viewports = [
    { name: 'desktop', width: 1440, height: 900 },
    { name: 'tablet', width: 1024, height: 1366 },
    { name: 'mobile', width: 390, height: 844 }
  ];
  if (!fs.existsSync(inventoryPath)) return viewports;
  const inventory = JSON.parse(fs.readFileSync(inventoryPath, 'utf8'));
  const breakpoints = inventory?.environment?.active_breakpoints || {};
  const usedWidths = new Set(viewports.map((item) => item.width));
  for (const [name, config] of Object.entries(breakpoints)) {
    const width = Number(config?.value);
    if (!Number.isFinite(width) || width < 240 || width > 3000 || usedWidths.has(width)) continue;
    usedWidths.add(width);
    viewports.push({ name: `breakpoint-${name}`, width, height: 1000 });
  }
  return viewports;
}

function slugify(filename) {
  return path.basename(filename, '.json').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
}

function isRelevantResource(resourceType, url) {
  if (url.endsWith('/favicon.ico')) return false;
  return ['document', 'script', 'stylesheet', 'font', 'image'].includes(resourceType);
}

const templates = fs.existsSync(templateDir) ? fs.readdirSync(templateDir).filter((name) => name.endsWith('.json')).sort() : [];
const viewports = loadViewports();

if (templates.length === 0) {
  test('no templates supplied', async () => test.skip(true, 'Add Elementor JSON files to templates/.'));
}

for (const template of templates) {
  const slug = slugify(template);
  for (const viewport of viewports) {
    test(`${template} - ${viewport.name}`, async ({ page, browserName }, testInfo) => {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      const browserErrors = [];
      const consoleErrors = [];
      const failedRequests = [];
      const badResponses = [];
      page.on('pageerror', (error) => browserErrors.push(error.message));
      page.on('console', (message) => { if (message.type() === 'error') consoleErrors.push(message.text()); });
      page.on('requestfailed', (request) => {
        if (isRelevantResource(request.resourceType(), request.url())) failedRequests.push({ url: request.url(), resource_type: request.resourceType(), error: request.failure()?.errorText || 'unknown' });
      });
      page.on('response', (response) => {
        const request = response.request();
        if (response.status() >= 400 && isRelevantResource(request.resourceType(), response.url())) badResponses.push({ url: response.url(), resource_type: request.resourceType(), status: response.status() });
      });

      const response = await page.goto(`/${slug}/`, { waitUntil: 'networkidle' });
      expect(response, 'Expected a WordPress response').not.toBeNull();
      expect(response.ok(), `Expected HTTP success for /${slug}/`).toBeTruthy();
      await expect(page.locator('body')).toBeVisible();
      await expect(page.locator('[data-elementor-type]').first(), 'Expected rendered Elementor markup').toBeVisible();

      const overflow = await page.evaluate(() => ({
        scrollWidth: document.documentElement.scrollWidth,
        clientWidth: document.documentElement.clientWidth,
        bodyScrollWidth: document.body ? document.body.scrollWidth : 0
      }));
      expect(Math.max(overflow.scrollWidth, overflow.bodyScrollWidth), `Unexpected horizontal overflow at ${viewport.name}`).toBeLessThanOrEqual(overflow.clientWidth + 2);

      const interactiveCount = await page.locator('a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])').count();
      let keyboardFocusTag = null;
      if (interactiveCount > 0) {
        await page.keyboard.press('Tab');
        keyboardFocusTag = await page.evaluate(() => document.activeElement?.tagName || null);
        expect(keyboardFocusTag, 'Expected keyboard focus to leave the document body').not.toBe('BODY');
      }

      const accessibility = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze();
      const seriousA11y = accessibility.violations.filter((violation) => ['critical', 'serious'].includes(violation.impact));

      await page.emulateMedia({ reducedMotion: 'reduce' });
      await page.waitForTimeout(100);
      fs.mkdirSync(screenshotDir, { recursive: true });
      await page.screenshot({ path: path.join(screenshotDir, `${slug}-${viewport.name}-${browserName}.png`), fullPage: true, animations: 'disabled' });

      const snapshotName = `${slug}-${viewport.name}.png`;
      const expectedSnapshotPath = testInfo.snapshotPath(snapshotName);
      const visualBaseline = fs.existsSync(expectedSnapshotPath) ? 'present' : 'missing';
      if (visualBaseline === 'present') {
        await expect(page).toHaveScreenshot(snapshotName, { fullPage: true, animations: 'disabled', maxDiffPixelRatio: 0.002 });
      }

      fs.writeFileSync(path.join(screenshotDir, `${slug}-${viewport.name}-${browserName}.json`), JSON.stringify({
        template,
        slug,
        browser: browserName,
        viewport,
        url: page.url(),
        title: await page.title(),
        visual_baseline: visualBaseline,
        expected_snapshot_path: path.relative(process.cwd(), expectedSnapshotPath),
        browser_errors: browserErrors,
        console_errors: consoleErrors,
        failed_requests: failedRequests,
        bad_responses: badResponses,
        horizontal_overflow: overflow,
        keyboard_focus_tag: keyboardFocusTag,
        reduced_motion: true,
        serious_accessibility_violations: seriousA11y.map((item) => ({ id: item.id, impact: item.impact, help: item.help, nodes: item.nodes.length }))
      }, null, 2) + '\n');

      expect(browserErrors, 'Expected no uncaught browser errors').toEqual([]);
      expect(consoleErrors, 'Expected no browser console errors').toEqual([]);
      expect(failedRequests, 'Expected no failed essential frontend resources').toEqual([]);
      expect(badResponses, 'Expected no HTTP >=400 for essential frontend resources').toEqual([]);
      expect(seriousA11y, 'Expected no critical/serious automated WCAG violations').toEqual([]);
    });
  }
}
