const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const PROJECT_ROOT = path.join(__dirname, '..', '..');
const GITHUB_USER = process.env.GITHUB_PAGES_USER || 'Yugoge';
const GITHUB_REPO = process.env.GITHUB_PAGES_REPO || 'travel-planner-graph';
const TARGET_URL = process.env.GITHUB_PAGES_URL || `https://${GITHUB_USER}.github.io/${GITHUB_REPO}/beijing-exchange-bucket-list-20260202/2026-02-02/`;
const EXPECTED_BEIGE_BG = 'rgb(245, 241, 232)'; // #F5F1E8
const OUTPUT_DIR = path.join(PROJECT_ROOT, 'docs', 'dev', 'playwright-judge5-output');
const SCREENSHOT_DIR = path.join(OUTPUT_DIR, 'screenshots');

// Ensure output directories exist
if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}
if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

const report = {
  judge_id: 5,
  judge_name: "GitHub Pages Deployment Judge",
  severity: "critical",
  url: TARGET_URL,
  timestamp: new Date().toISOString(),
  page_load_status: "not_tested",
  http_status: 0,
  page_size_kb: 0,
  color_theme_correct: false,
  features_working: [],
  issues: [],
  comparison_with_previous: {
    file_size_fixed: false,
    colors_fixed: false,
    previous_size: "432KB",
    current_size: "unknown"
  },
  verdict: "FAIL",
  screenshots: [],
  evidence: [],
  network_requests: [],
  console_errors: [],
  timing: {}
};

async function testGitHubPagesDeployment() {
  let browser;
  let context;
  let page;

  try {
    console.log('🚀 Starting Playwright test for GitHub Pages deployment...');
    console.log(`📍 URL: ${TARGET_URL}`);

    const startTime = Date.now();

    // Launch browser
    browser = await chromium.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    context = await browser.newContext({
      viewport: { width: 1920, height: 1080 },
      userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    });

    page = await context.newPage();

    // Collect network requests
    const networkRequests = [];
    let htmlSize = 0;
    let totalSize = 0;

    page.on('response', async (response) => {
      const url = response.url();
      const status = response.status();
      const size = (await response.body().catch(() => Buffer.from(''))).length;

      networkRequests.push({
        url: url,
        status: status,
        size: size,
        contentType: response.headers()['content-type'] || 'unknown'
      });

      if (url === TARGET_URL || url.endsWith('index.html')) {
        htmlSize = size;
      }
      totalSize += size;
    });

    // Collect console errors
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    page.on('pageerror', error => {
      consoleErrors.push(`Page Error: ${error.message}`);
    });

    // Navigate with retry logic
    let navigationSuccess = false;
    let httpStatus = 0;

    for (let attempt = 1; attempt <= 3; attempt++) {
      try {
        console.log(`🔄 Navigation attempt ${attempt}/3...`);
        const response = await page.goto(TARGET_URL, {
          waitUntil: 'networkidle',
          timeout: 30000
        });

        httpStatus = response.status();
        console.log(`✅ HTTP Status: ${httpStatus}`);

        if (httpStatus === 200) {
          navigationSuccess = true;
          report.page_load_status = "success";
          report.http_status = httpStatus;
          break;
        } else {
          report.issues.push({
            severity: 'critical',
            category: 'page_load',
            description: `HTTP ${httpStatus} - Expected 200`,
            location: TARGET_URL
          });
        }
      } catch (error) {
        console.log(`❌ Attempt ${attempt} failed: ${error.message}`);
        if (attempt === 3) {
          report.page_load_status = "failed";
          report.issues.push({
            severity: 'critical',
            category: 'page_load',
            description: `Failed to load page after 3 attempts: ${error.message}`,
            location: TARGET_URL
          });
          throw error;
        }
        await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2s before retry
      }
    }

    const loadTime = Date.now() - startTime;
    report.timing.page_load_ms = loadTime;
    console.log(`⏱️  Page load time: ${loadTime}ms`);

    if (loadTime > 5000) {
      report.issues.push({
        severity: 'major',
        category: 'performance',
        description: `Page load time ${loadTime}ms exceeds 5000ms threshold`,
        location: 'page_load'
      });
    }

    // Wait for page to be ready
    await page.waitForTimeout(2000);

    // Take initial screenshot
    const initialScreenshot = path.join(SCREENSHOT_DIR, '01-initial-load.png');
    await page.screenshot({ path: initialScreenshot, fullPage: true });
    report.screenshots.push('screenshots/01-initial-load.png');
    console.log('📸 Screenshot: Initial load');

    // Store network data
    report.network_requests = networkRequests;
    report.console_errors = consoleErrors;

    // Calculate sizes
    report.page_size_kb = Math.round(htmlSize / 1024);
    report.total_page_size_kb = Math.round(totalSize / 1024);
    report.comparison_with_previous.current_size = `${report.page_size_kb}KB`;

    console.log(`📊 HTML Size: ${report.page_size_kb}KB`);
    console.log(`📊 Total Size: ${report.total_page_size_kb}KB`);

    // Check file size expectations
    if (report.page_size_kb >= 200 && report.page_size_kb <= 250) {
      report.comparison_with_previous.file_size_fixed = true;
      report.features_working.push('HTML file size is correct (200-250KB range)');
      console.log('✅ File size check: PASS');
    } else if (report.page_size_kb > 400) {
      report.comparison_with_previous.file_size_fixed = false;
      report.issues.push({
        severity: 'critical',
        category: 'file_size',
        description: `HTML file size ${report.page_size_kb}KB is too large (expected 200-250KB, matches old 432KB bug)`,
        location: 'index.html'
      });
      console.log('❌ File size check: FAIL (too large)');
    } else {
      report.issues.push({
        severity: 'major',
        category: 'file_size',
        description: `HTML file size ${report.page_size_kb}KB outside expected range (200-250KB)`,
        location: 'index.html'
      });
      console.log('⚠️  File size check: WARNING (unexpected size)');
    }

    // Check for console errors
    if (consoleErrors.length > 0) {
      report.issues.push({
        severity: 'major',
        category: 'javascript_errors',
        description: `${consoleErrors.length} console error(s) detected`,
        details: consoleErrors.slice(0, 5) // First 5 errors
      });
      console.log(`❌ Console errors: ${consoleErrors.length}`);
    } else {
      report.features_working.push('No JavaScript console errors');
      console.log('✅ Console errors: None');
    }

    // Check for 404s
    const failed404s = networkRequests.filter(req => req.status === 404);
    if (failed404s.length > 0) {
      report.issues.push({
        severity: 'major',
        category: 'resource_loading',
        description: `${failed404s.length} resource(s) failed to load (404)`,
        details: failed404s.map(r => r.url)
      });
      console.log(`❌ 404 errors: ${failed404s.length}`);
    } else {
      report.features_working.push('All resources loaded successfully (no 404s)');
      console.log('✅ 404 check: None');
    }

    // **COLOR THEME VERIFICATION**
    console.log('\n🎨 Testing color theme...');

    const bodyBgColor = await page.evaluate(() => {
      const body = document.body;
      return window.getComputedStyle(body).backgroundColor;
    });

    console.log(`🎨 Body background color: ${bodyBgColor}`);
    report.evidence.push(`Body background color: ${bodyBgColor}`);

    if (bodyBgColor === EXPECTED_BEIGE_BG || bodyBgColor === 'rgb(245, 241, 232)') {
      report.color_theme_correct = true;
      report.comparison_with_previous.colors_fixed = true;
      report.features_working.push('Beige color theme correctly applied');
      console.log('✅ Color theme: PASS (beige)');
    } else {
      report.color_theme_correct = false;
      report.comparison_with_previous.colors_fixed = false;
      report.issues.push({
        severity: 'critical',
        category: 'color_theme',
        description: `Background color is ${bodyBgColor}, expected ${EXPECTED_BEIGE_BG}`,
        location: 'body element'
      });
      console.log('❌ Color theme: FAIL (not beige)');
    }

    // Check for purple gradient (should NOT exist)
    const hasPurpleGradient = await page.evaluate(() => {
      const elements = document.querySelectorAll('*');
      for (let el of elements) {
        const bg = window.getComputedStyle(el).background;
        const bgImage = window.getComputedStyle(el).backgroundImage;
        if (bg.includes('#667eea') || bg.includes('#764ba2') ||
            bgImage.includes('667eea') || bgImage.includes('764ba2')) {
          return true;
        }
      }
      return false;
    });

    if (hasPurpleGradient) {
      report.issues.push({
        severity: 'critical',
        category: 'color_theme',
        description: 'Purple gradient (#667eea, #764ba2) detected - should be beige theme',
        location: 'CSS styles'
      });
      console.log('❌ Purple gradient found (should not exist)');
    } else {
      report.features_working.push('No purple gradient (correctly removed)');
      console.log('✅ No purple gradient');
    }

    // **CONTENT VERIFICATION**
    console.log('\n📋 Testing content and features...');

    // Check for stats dashboard
    const statsExists = await page.locator('text=Statistics Dashboard').count() > 0;
    if (statsExists) {
      report.features_working.push('Statistics Dashboard present');
      console.log('✅ Stats Dashboard: Present');
    } else {
      report.issues.push({
        severity: 'critical',
        category: 'content',
        description: 'Statistics Dashboard not found',
        location: 'page content'
      });
      console.log('❌ Stats Dashboard: Missing');
    }

    // Test expand/collapse
    try {
      const expandBtn = page.locator('button:has-text("Expand All")').first();
      if (await expandBtn.count() > 0) {
        await expandBtn.click();
        await page.waitForTimeout(500);
        const screenshot2 = path.join(SCREENSHOT_DIR, '02-expanded-stats.png');
        await page.screenshot({ path: screenshot2, fullPage: true });
        report.screenshots.push('screenshots/02-expanded-stats.png');
        report.features_working.push('Expand/collapse buttons working');
        console.log('✅ Expand/collapse: Working');
      }
    } catch (error) {
      report.issues.push({
        severity: 'major',
        category: 'interactivity',
        description: `Expand/collapse test failed: ${error.message}`,
        location: 'stats controls'
      });
      console.log(`⚠️  Expand/collapse: Error - ${error.message}`);
    }

    // Check for Kanban route map
    const kanbanExists = await page.locator('text=Route Map').count() > 0 ||
                         await page.locator('.kanban').count() > 0;
    if (kanbanExists) {
      report.features_working.push('Kanban route map present');
      console.log('✅ Kanban Route Map: Present');

      const screenshot3 = path.join(SCREENSHOT_DIR, '03-kanban-route.png');
      await page.screenshot({ path: screenshot3, fullPage: true });
      report.screenshots.push('screenshots/03-kanban-route.png');
    } else {
      report.issues.push({
        severity: 'critical',
        category: 'content',
        description: 'Kanban route map not found',
        location: 'page content'
      });
      console.log('❌ Kanban Route Map: Missing');
    }

    // Check for budget charts
    const budgetChartExists = await page.locator('canvas').count() > 0 ||
                              await page.locator('text=Budget').count() > 0;
    if (budgetChartExists) {
      report.features_working.push('Budget charts present');
      console.log('✅ Budget Charts: Present');
    } else {
      report.issues.push({
        severity: 'major',
        category: 'content',
        description: 'Budget charts not found',
        location: 'page content'
      });
      console.log('❌ Budget Charts: Missing');
    }

    // Check for Chart.js library
    const hasChartJS = await page.evaluate(() => {
      return typeof window.Chart !== 'undefined';
    });

    if (hasChartJS) {
      report.features_working.push('Chart.js library loaded');
      console.log('✅ Chart.js: Loaded');
    } else {
      report.issues.push({
        severity: 'major',
        category: 'libraries',
        description: 'Chart.js library not loaded',
        location: 'JavaScript libraries'
      });
      console.log('❌ Chart.js: Not loaded');
    }

    // Check for map links with brand colors
    const mapLinks = await page.locator('a[href*="maps"]').count();
    if (mapLinks > 0) {
      report.features_working.push(`${mapLinks} map link(s) found`);
      console.log(`✅ Map Links: ${mapLinks} found`);

      // Test hover on first map link
      try {
        const firstMapLink = page.locator('a[href*="maps"]').first();
        await firstMapLink.hover();
        await page.waitForTimeout(300);
        const screenshot4 = path.join(SCREENSHOT_DIR, '04-map-link-hover.png');
        await page.screenshot({ path: screenshot4, fullPage: true });
        report.screenshots.push('screenshots/04-map-link-hover.png');
        console.log('✅ Map link hover: Tested');
      } catch (error) {
        console.log(`⚠️  Map link hover: ${error.message}`);
      }
    } else {
      report.issues.push({
        severity: 'major',
        category: 'content',
        description: 'No map links found',
        location: 'page content'
      });
      console.log('❌ Map Links: None found');
    }

    // Check for cities panel
    const citiesExists = await page.locator('text=Cities').count() > 0 ||
                         await page.locator('text=Beijing').count() > 0;
    if (citiesExists) {
      report.features_working.push('Cities panel present');
      console.log('✅ Cities Panel: Present');
    } else {
      report.issues.push({
        severity: 'major',
        category: 'content',
        description: 'Cities panel not found',
        location: 'page content'
      });
      console.log('❌ Cities Panel: Missing');
    }

    // Check for NaN or undefined values
    const pageText = await page.textContent('body');
    const hasNaN = pageText.includes('NaN') || pageText.includes('undefined');

    if (hasNaN) {
      report.issues.push({
        severity: 'major',
        category: 'data',
        description: 'Found "NaN" or "undefined" in page content',
        location: 'page content'
      });
      console.log('❌ Data validation: Found NaN/undefined');
    } else {
      report.features_working.push('No NaN or undefined values in content');
      console.log('✅ Data validation: No NaN/undefined');
    }

    // Check for currency symbols
    const hasCurrency = pageText.includes('¥') || pageText.includes('CNY') || pageText.includes('RMB');
    if (hasCurrency) {
      report.features_working.push('Currency values displayed');
      console.log('✅ Currency: Displayed');
    } else {
      report.issues.push({
        severity: 'minor',
        category: 'content',
        description: 'No currency symbols found',
        location: 'page content'
      });
      console.log('⚠️  Currency: Not found');
    }

    // Test horizontal scroll on Kanban
    try {
      const kanbanContainer = page.locator('.kanban').first();
      if (await kanbanContainer.count() > 0) {
        const scrollWidth = await kanbanContainer.evaluate(el => el.scrollWidth);
        const clientWidth = await kanbanContainer.evaluate(el => el.clientWidth);

        if (scrollWidth > clientWidth) {
          await kanbanContainer.evaluate(el => el.scrollLeft = 100);
          await page.waitForTimeout(300);
          report.features_working.push('Kanban horizontal scroll working');
          console.log('✅ Kanban scroll: Working');
        }
      }
    } catch (error) {
      console.log(`⚠️  Kanban scroll test: ${error.message}`);
    }

    // Final full page screenshot
    const finalScreenshot = path.join(SCREENSHOT_DIR, '05-final-state.png');
    await page.screenshot({ path: finalScreenshot, fullPage: true });
    report.screenshots.push('screenshots/05-final-state.png');
    console.log('📸 Screenshot: Final state');

    // **VERDICT DETERMINATION**
    const criticalIssues = report.issues.filter(i => i.severity === 'critical');
    const majorIssues = report.issues.filter(i => i.severity === 'major');

    if (criticalIssues.length === 0 && majorIssues.length === 0) {
      report.verdict = 'PASS';
      console.log('\n✅ VERDICT: PASS');
    } else if (criticalIssues.length > 0) {
      report.verdict = 'FAIL';
      console.log(`\n❌ VERDICT: FAIL (${criticalIssues.length} critical issue(s))`);
    } else {
      report.verdict = 'PASS_WITH_WARNINGS';
      console.log(`\n⚠️  VERDICT: PASS WITH WARNINGS (${majorIssues.length} major issue(s))`);
    }

    console.log(`\n📊 Summary:`);
    console.log(`   - Features working: ${report.features_working.length}`);
    console.log(`   - Critical issues: ${criticalIssues.length}`);
    console.log(`   - Major issues: ${majorIssues.length}`);
    console.log(`   - Total issues: ${report.issues.length}`);

  } catch (error) {
    console.error('❌ Fatal error:', error);
    report.verdict = 'FAIL';
    report.issues.push({
      severity: 'critical',
      category: 'test_execution',
      description: `Test execution failed: ${error.message}`,
      stack: error.stack
    });
  } finally {
    // Cleanup
    if (page) await page.close();
    if (context) await context.close();
    if (browser) await browser.close();
  }

  // Save report
  const reportPath = path.join(PROJECT_ROOT, 'docs', 'dev', 'judge-5-github-pages-20260203.json');
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
  console.log(`\n💾 Report saved to: ${reportPath}`);

  // Save summary
  const summaryPath = path.join(PROJECT_ROOT, 'docs', 'dev', 'judge-5-github-pages-20260203-summary.md');
  const summary = generateSummary(report);
  fs.writeFileSync(summaryPath, summary);
  console.log(`💾 Summary saved to: ${summaryPath}`);

  return report;
}

function generateSummary(report) {
  const criticalIssues = report.issues.filter(i => i.severity === 'critical');
  const majorIssues = report.issues.filter(i => i.severity === 'major');
  const minorIssues = report.issues.filter(i => i.severity === 'minor');

  let summary = `# Judge 5 - GitHub Pages Deployment Report\n\n`;
  summary += `**Test Date**: ${report.timestamp}\n`;
  summary += `**URL**: ${report.url}\n`;
  summary += `**Verdict**: ${report.verdict}\n\n`;

  summary += `## Page Load\n`;
  summary += `- HTTP Status: ${report.http_status}\n`;
  summary += `- Load Time: ${report.timing.page_load_ms}ms\n`;
  summary += `- HTML Size: ${report.page_size_kb}KB\n`;
  summary += `- Total Page Size: ${report.total_page_size_kb}KB\n\n`;

  summary += `## Color Theme\n`;
  summary += `- Beige Theme Correct: ${report.color_theme_correct ? '✅ YES' : '❌ NO'}\n`;
  summary += `- Colors Fixed from Previous: ${report.comparison_with_previous.colors_fixed ? '✅ YES' : '❌ NO'}\n\n`;

  summary += `## File Size Comparison\n`;
  summary += `- Previous Size: ${report.comparison_with_previous.previous_size}\n`;
  summary += `- Current Size: ${report.comparison_with_previous.current_size}\n`;
  summary += `- Size Fixed: ${report.comparison_with_previous.file_size_fixed ? '✅ YES' : '❌ NO'}\n\n`;

  summary += `## Features Working (${report.features_working.length})\n`;
  report.features_working.forEach(feature => {
    summary += `- ✅ ${feature}\n`;
  });
  summary += `\n`;

  summary += `## Issues Found\n`;
  summary += `- Critical: ${criticalIssues.length}\n`;
  summary += `- Major: ${majorIssues.length}\n`;
  summary += `- Minor: ${minorIssues.length}\n`;
  summary += `- **Total**: ${report.issues.length}\n\n`;

  if (criticalIssues.length > 0) {
    summary += `### Critical Issues\n`;
    criticalIssues.forEach((issue, idx) => {
      summary += `${idx + 1}. **${issue.category}**: ${issue.description}\n`;
      summary += `   - Location: ${issue.location}\n`;
    });
    summary += `\n`;
  }

  if (majorIssues.length > 0) {
    summary += `### Major Issues\n`;
    majorIssues.forEach((issue, idx) => {
      summary += `${idx + 1}. **${issue.category}**: ${issue.description}\n`;
      summary += `   - Location: ${issue.location}\n`;
    });
    summary += `\n`;
  }

  summary += `## Console Errors\n`;
  summary += `- Count: ${report.console_errors.length}\n`;
  if (report.console_errors.length > 0) {
    summary += `\nFirst 5 errors:\n`;
    report.console_errors.slice(0, 5).forEach(err => {
      summary += `- ${err}\n`;
    });
  }
  summary += `\n`;

  summary += `## Screenshots\n`;
  report.screenshots.forEach(screenshot => {
    summary += `- ${screenshot}\n`;
  });

  return summary;
}

// Run the test
testGitHubPagesDeployment().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
