const fs = require('fs');
const path = require('path');
const { test, expect } = require('@playwright/test');

const templateDir = path.resolve(__dirname, '../../templates');
const screenshotDir = path.resolve(__dirname, '../../artifacts/screenshots');
const inventoryPath = path.resolve(
  __dirname,
  '../../wordpress-plugin/elementor-json-lab/.runtime/inventory.json'
);

function slugify(filename) {
  return path.basename(filename, '.json')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

function runtimeViewports() {
  const result = [
    { name: 'desktop', width: 1440, height: 900 },
    { name: 'tablet', width: 1024, height: 1366 },
    { name: 'mobile', width: 390, height: 844 }
  ];
  const usedWidths = new Set(result.map((item) => item.width));

  if (!fs.existsSync(inventoryPath)) {
    return result;
  }

  let inventory;
  try {
    inventory = JSON.parse(fs.readFileSync(inventoryPath, 'utf8'));
  } catch (error) {
    throw new Error(`Could not parse runtime inventory: ${error.message}`);
  }

  const breakpoints = inventory?.environment?.active_breakpoints;
  if (!breakpoints || typeof breakpoints !== 'object') {
    return result;
  }

  for (const [name, breakpoint] of Object.entries(breakpoints)) {
    if (['mobile', 'tablet'].includes(name) || !breakpoint || typeof breakpoint !== 'object') {
      continue;
    }
    const value = Number(breakpoint.value);
    if (!Number.isFinite(value) || value <= 0) {
      continue;
    }
    const direction = String(breakpoint.direction || '').toLowerCase();
    const width = direction.includes('min') ? Math.round(value + 1) : Math.max(320, Math.round(value - 1));
    if (usedWidths.has(width)) {
      continue;
    }
    usedWidths.add(width);
    result.push({ name: `breakpoint-${name}`, width, height: 1000 });
  }

  return result;
}

const templates = fs.existsSync(templateDir)
  ? fs.readdirSync(templateDir).filter((name) => name.endsWith('.json')).sort()
  : [];
const viewports = runtimeViewports();

const slugMap = new Map();
for (const template of templates) {
  const slug = slugify(template);
  if (!slug) {
    throw new Error(`Template filename cannot produce a valid preview slug: ${template}`);
  }
  if (slugMap.has(slug)) {
    throw new Error(`Template slug collision: ${slugMap.get(slug)} and ${template} both map to ${slug}`);
  }
  slugMap.set(slug, template);
}

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
      const requestFailures = [];
      const httpErrors = [];

      page.on('pageerror', (error) => browserErrors.push(error.message));
      page.on('console', (message) => {
        if (message.type() === 'error') {
          consoleErrors.push(message.text());
        }
      });
      page.on('requestfailed', (request) => {
        requestFailures.push(`${request.method()} ${request.url()} :: ${request.failure()?.errorText || 'failed'}`);
      });
      page.on('response', (response) => {
        const request = response.request();
        const resourceType = request.resourceType();
        const url = response.url();
        if (
          response.status() >= 400 &&
          ['document', 'script', 'stylesheet', 'font', 'image'].includes(resourceType) &&
          !url.endsWith('/favicon.ico')
        ) {
          httpErrors.push(`${response.status()} ${resourceType} ${url}`);
        }
      });

      const response = await page.goto(`/${slug}/`, { waitUntil: 'networkidle' });
      expect(response, 'Expected a WordPress response').not.toBeNull();
      expect(response.ok(), `Expected HTTP success for /${slug}/`).toBeTruthy();

      await expect(page.locator('body')).toBeVisible();
      await expect(
        page.locator('[data-elementor-type]').first(),
        'Expected the page to contain rendered Elementor markup'
      ).toBeVisible();

      const layout = await page.evaluate(() => ({
        scrollWidth: document.documentElement.scrollWidth,
        clientWidth: document.documentElement.clientWidth,
        nestedInteractive: document.querySelectorAll(
          'a a, a button, button a, button button, a [role="button"], button [role="link"]'
        ).length
      }));
      expect(
        layout.scrollWidth <= layout.clientWidth + 2,
        `Unexpected horizontal overflow: ${layout.scrollWidth}px > ${layout.clientWidth}px`
      ).toBeTruthy();
      expect(layout.nestedInteractive, 'Expected no invalid nested interactive controls').toBe(0);

      const focusableCount = await page.locator(
        'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
      ).count();
      if (focusableCount > 0) {
        let visibleFocus = false;
        for (let index = 0; index < Math.min(focusableCount + 2, 10); index += 1) {
          await page.keyboard.press('Tab');
          visibleFocus = await page.locator(':focus').isVisible().catch(() => false);
          if (visibleFocus) {
            break;
          }
        }
        expect(visibleFocus, 'Expected keyboard navigation to reach a visible focus target').toBeTruthy();
      }

      await expect(page).toHaveScreenshot(`${slug}-${viewport.name}.png`, {
        fullPage: true,
        animations: 'disabled'
      });

      fs.mkdirSync(screenshotDir, { recursive: true });
      const artifactStem = `${slug}-${viewport.name}-${testInfo.project.name}`;
      await page.screenshot({
        path: path.join(screenshotDir, `${artifactStem}.png`),
        fullPage: true,
        animations: 'disabled'
      });

      fs.writeFileSync(
        path.join(screenshotDir, `${artifactStem}.json`),
        JSON.stringify(
          {
            template,
            slug,
            viewport,
            browser: testInfo.project.name,
            url: page.url(),
            title: await page.title(),
            reduced_motion: true,
            layout,
            browser_errors: browserErrors,
            console_errors: consoleErrors,
            request_failures: requestFailures,
            http_errors: httpErrors
          },
          null,
          2
        ) + '\n'
      );

      expect(browserErrors, 'Expected no uncaught browser errors').toEqual([]);
      expect(consoleErrors, 'Expected no browser console errors').toEqual([]);
      expect(requestFailures, 'Expected no failed browser requests').toEqual([]);
      expect(httpErrors, 'Expected no HTTP errors for rendered resources').toEqual([]);
    });
  }
}
