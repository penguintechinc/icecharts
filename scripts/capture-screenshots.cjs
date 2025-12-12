const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

const BASE_URL = 'http://localhost:3000';
const OUTPUT_DIR = '/home/penguin/code/IceCharts/assets/screenshots';

// Pages to capture
const pages = [
  { name: 'login', path: '/login' },
  { name: 'dashboard', path: '/dashboard' },
  { name: 'drawings', path: '/drawings' },
  { name: 'groups', path: '/groups' },
  { name: 'templates', path: '/templates' },
  { name: 'collections', path: '/collections' },
  { name: 'settings', path: '/settings' },
  // Admin pages
  { name: 'admin-users', path: '/admin/users' },
  { name: 'admin-sso', path: '/admin/sso' },
  { name: 'admin-storage', path: '/admin/storage' },
  { name: 'admin-dashboard', path: '/admin/dashboard' },
];

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function captureScreenshots() {
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });

  // Capture login page first (unauthenticated)
  console.log('Capturing login...');
  await page.goto(`${BASE_URL}/login`, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await sleep(3000);  // Wait for React to render
  await page.screenshot({ path: path.join(OUTPUT_DIR, 'login.png') });
  console.log('  Saved login.png');

  // Perform actual login through UI
  console.log('Logging in...');

  // Find and fill login form
  const inputs = await page.$$('input');
  console.log(`Found ${inputs.length} input fields`);
  if (inputs.length >= 2) {
    await inputs[0].type('admin@localhost');  // Email field
    await inputs[1].type('admin123');                // Password field
  }

  // Click submit button
  await page.click('button[type="submit"]');

  // Wait for navigation to complete
  try {
    await page.waitForFunction(
      () => !window.location.pathname.includes('/login'),
      { timeout: 30000 }
    );
  } catch (e) {
    console.log('Navigation timeout - checking if login succeeded anyway');
  }
  await sleep(2000);
  console.log('Current URL after login:', page.url());

  // Capture all other pages
  for (const pageInfo of pages) {
    if (pageInfo.name === 'login') continue;

    try {
      console.log(`Capturing ${pageInfo.name}...`);
      await page.goto(`${BASE_URL}${pageInfo.path}`, { waitUntil: 'domcontentloaded', timeout: 30000 });
      await sleep(3000); // Wait for React to render and data to load

      // Check if we got redirected to login
      const currentUrl = page.url();
      if (currentUrl.includes('/login')) {
        console.log(`  WARNING: Redirected to login for ${pageInfo.name}, skipping...`);
        continue;
      }

      await page.screenshot({
        path: path.join(OUTPUT_DIR, `${pageInfo.name}.png`),
        fullPage: false,
      });
      console.log(`  Saved ${pageInfo.name}.png (URL: ${currentUrl})`);
    } catch (error) {
      console.error(`  Error capturing ${pageInfo.name}: ${error.message}`);
    }
  }

  await browser.close();
  console.log('\nScreenshots saved to:', OUTPUT_DIR);
}

captureScreenshots().catch(console.error);
