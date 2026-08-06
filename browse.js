const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const url = process.argv[2];
  if (!url) {
    console.log(JSON.stringify({error: "No URL provided"}));
    process.exit(1);
  }

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ignoreHTTPSErrors: true
  });
  const page = await context.newPage();

  // Collect network requests for POST analysis
  let postRequests = [];
  page.on('request', request => {
    if (request.method() === 'POST') {
      postRequests.push({
        url: request.url(),
        postData: request.postData()?.substring(0, 200) // truncated
      });
    }
  });

  try {
    await page.goto(url, { waitUntil: 'networkidle', timeout: 15000 });
    // Wait extra for dynamic content
    await page.waitForTimeout(3000);

    const finalUrl = page.url();
    const title = await page.title();
    const screenshot = await page.screenshot({ encoding: 'base64' });

    // Detect login forms (crude heuristic)
    const hasLoginForm = await page.evaluate(() => {
      const passwordFields = document.querySelectorAll('input[type="password"]');
      return passwordFields.length > 0;
    });

    // Fill fake credentials if login form found
    if (hasLoginForm) {
      try {
        const emailField = await page.$('input[type="email"], input[name="email"], input[name="username"]');
        const passField = await page.$('input[type="password"]');
        if (emailField) await emailField.fill('phishsandbox@example.com');
        if (passField) await passField.fill('FakePassword123!');
        // Click submit button (generic)
        const submitBtn = await page.$('button[type="submit"], input[type="submit"]');
        if (submitBtn) {
          await submitBtn.click();
          await page.waitForTimeout(2000);
        }
      } catch (e) {
        // non-critical
      }
    }

    // Certificate info via page (if possible)
    // Not directly exposed in Playwright without extra CDP, skip for simplicity

    const result = {
      initialUrl: url,
      finalUrl,
      title,
      screenshotBase64: screenshot.toString('base64'),
      hasLoginForm,
      postRequests,
      headers: await page.evaluate(() => document.documentElement.outerHTML.substring(0, 500)) // snippet
    };
    console.log(JSON.stringify(result));

  } catch (err) {
    console.log(JSON.stringify({error: err.message, url}));
  } finally {
    await browser.close();
  }
})();