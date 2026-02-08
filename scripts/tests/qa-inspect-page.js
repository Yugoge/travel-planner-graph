/**
 * Playwright script to inspect deployed travel planner page
 * Captures screenshots, extracts image URLs, checks Transportation sections
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const TARGET_URL = 'https://Yugoge.github.io/travel-planner-graph/china-feb-15-mar-7-2026-20260202-195429.html/2026-02-07/';
const OUTPUT_DIR = path.join(__dirname, '..', 'docs', 'dev', 'playwright-screenshots');
const REPORT_PATH = path.join(__dirname, '..', 'docs', 'dev', 'qa-report-playwright-20260207.json');

async function inspectPage() {
  console.log('Starting Playwright inspection...');

  // Ensure output directory exists
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });
  const page = await context.newPage();

  const report = {
    timestamp: new Date().toISOString(),
    url: TARGET_URL,
    screenshots: [],
    images: {
      all_urls: [],
      unsplash_count: 0,
      gaode_count: 0,
      google_count: 0,
      other_count: 0
    },
    transportation: {
      day2: { visible: false, html: '' },
      day3: { visible: false, html: '' },
      day4: { visible: false, html: '' },
      day8: { visible: false, html: '' }
    },
    timeline: {
      conflicts_visible: false,
      html: ''
    },
    console_errors: [],
    root_cause: ''
  };

  // Capture console errors
  page.on('console', msg => {
    if (msg.type() === 'error') {
      report.console_errors.push({
        type: 'console_error',
        text: msg.text(),
        timestamp: new Date().toISOString()
      });
    }
  });

  page.on('pageerror', error => {
    report.console_errors.push({
      type: 'page_error',
      text: error.message,
      stack: error.stack,
      timestamp: new Date().toISOString()
    });
  });

  try {
    console.log(`Navigating to: ${TARGET_URL}`);
    await page.goto(TARGET_URL, { waitUntil: 'networkidle', timeout: 30000 });

    console.log('Waiting for React app to load...');
    // Wait for the main content to render
    await page.waitForSelector('.plan-container, .travel-plan-container, body', { timeout: 10000 });

    // Give React time to render
    await page.waitForTimeout(3000);

    // Check if PLAN_DATA is available
    const planDataExists = await page.evaluate(() => {
      return typeof window.PLAN_DATA !== 'undefined';
    });
    console.log(`PLAN_DATA exists: ${planDataExists}`);

    // Take initial screenshot
    console.log('Taking initial screenshot...');
    const initialScreenshot = path.join(OUTPUT_DIR, '01-initial-load.png');
    await page.screenshot({ path: initialScreenshot, fullPage: true });
    report.screenshots.push(initialScreenshot);

    // Extract ALL image URLs
    console.log('Extracting image URLs...');
    const imageData = await page.evaluate(() => {
      const images = Array.from(document.querySelectorAll('img'));
      return images.map(img => ({
        src: img.src,
        alt: img.alt,
        visible: img.offsetWidth > 0 && img.offsetHeight > 0
      }));
    });

    report.images.all_urls = imageData;

    // Count image types
    imageData.forEach(img => {
      const src = img.src.toLowerCase();
      if (src.includes('unsplash')) {
        report.images.unsplash_count++;
      } else if (src.includes('autonavi') || src.includes('amap') || src.includes('gaode')) {
        report.images.gaode_count++;
      } else if (src.includes('googleapis') || src.includes('googleusercontent')) {
        report.images.google_count++;
      } else {
        report.images.other_count++;
      }
    });

    console.log(`Image counts - Unsplash: ${report.images.unsplash_count}, Gaode: ${report.images.gaode_count}, Google: ${report.images.google_count}, Other: ${report.images.other_count}`);

    // Check for day navigation buttons
    const dayButtonsExist = await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button, [role="tab"]'));
      return buttons.some(btn => btn.textContent.includes('Day') || btn.textContent.includes('日'));
    });

    console.log(`Day navigation buttons exist: ${dayButtonsExist}`);

    // Try to find and click Day 2
    if (dayButtonsExist) {
      // Take screenshot of Day 1 first
      console.log('Taking Day 1 screenshot...');
      const day1Screenshot = path.join(OUTPUT_DIR, '02-day1-view.png');
      await page.screenshot({ path: day1Screenshot, fullPage: true });
      report.screenshots.push(day1Screenshot);

      // Navigate to Day 2
      console.log('Navigating to Day 2...');
      const day2Clicked = await page.evaluate(() => {
        const buttons = Array.from(document.querySelectorAll('button, [role="tab"]'));
        const day2Button = buttons.find(btn =>
          btn.textContent.includes('Day 2') ||
          btn.textContent.includes('第2天') ||
          btn.textContent.includes('2月16日')
        );
        if (day2Button) {
          day2Button.click();
          return true;
        }
        return false;
      });

      if (day2Clicked) {
        await page.waitForTimeout(1500);

        // Check for Transportation section on Day 2
        const day2Transport = await page.evaluate(() => {
          const headings = Array.from(document.querySelectorAll('h3, h4, .section-title, [class*="title"]'));
          const transportHeading = headings.find(h =>
            h.textContent.includes('Transportation') ||
            h.textContent.includes('交通')
          );

          if (transportHeading) {
            const section = transportHeading.closest('section, div[class*="section"]') || transportHeading.parentElement;
            return {
              visible: true,
              html: section ? section.outerHTML.substring(0, 500) : transportHeading.outerHTML
            };
          }

          return { visible: false, html: '' };
        });

        report.transportation.day2 = day2Transport;

        const day2Screenshot = path.join(OUTPUT_DIR, '03-day2-view.png');
        await page.screenshot({ path: day2Screenshot, fullPage: true });
        report.screenshots.push(day2Screenshot);
      }

      // Navigate to Day 3
      console.log('Navigating to Day 3...');
      const day3Clicked = await page.evaluate(() => {
        const buttons = Array.from(document.querySelectorAll('button, [role="tab"]'));
        const day3Button = buttons.find(btn =>
          btn.textContent.includes('Day 3') ||
          btn.textContent.includes('第3天') ||
          btn.textContent.includes('2月17日')
        );
        if (day3Button) {
          day3Button.click();
          return true;
        }
        return false;
      });

      if (day3Clicked) {
        await page.waitForTimeout(1500);

        const day3Transport = await page.evaluate(() => {
          const headings = Array.from(document.querySelectorAll('h3, h4, .section-title, [class*="title"]'));
          const transportHeading = headings.find(h =>
            h.textContent.includes('Transportation') ||
            h.textContent.includes('交通')
          );

          if (transportHeading) {
            const section = transportHeading.closest('section, div[class*="section"]') || transportHeading.parentElement;
            return {
              visible: true,
              html: section ? section.outerHTML.substring(0, 500) : transportHeading.outerHTML
            };
          }

          return { visible: false, html: '' };
        });

        report.transportation.day3 = day3Transport;

        const day3Screenshot = path.join(OUTPUT_DIR, '04-day3-view.png');
        await page.screenshot({ path: day3Screenshot, fullPage: true });
        report.screenshots.push(day3Screenshot);
      }

      // Navigate to Day 4
      console.log('Navigating to Day 4...');
      const day4Clicked = await page.evaluate(() => {
        const buttons = Array.from(document.querySelectorAll('button, [role="tab"]'));
        const day4Button = buttons.find(btn =>
          btn.textContent.includes('Day 4') ||
          btn.textContent.includes('第4天') ||
          btn.textContent.includes('2月18日')
        );
        if (day4Button) {
          day4Button.click();
          return true;
        }
        return false;
      });

      if (day4Clicked) {
        await page.waitForTimeout(1500);

        const day4Transport = await page.evaluate(() => {
          const headings = Array.from(document.querySelectorAll('h3, h4, .section-title, [class*="title"]'));
          const transportHeading = headings.find(h =>
            h.textContent.includes('Transportation') ||
            h.textContent.includes('交通')
          );

          if (transportHeading) {
            const section = transportHeading.closest('section, div[class*="section"]') || transportHeading.parentElement;
            return {
              visible: true,
              html: section ? section.outerHTML.substring(0, 500) : transportHeading.outerHTML
            };
          }

          return { visible: false, html: '' };
        });

        report.transportation.day4 = day4Transport;

        const day4Screenshot = path.join(OUTPUT_DIR, '05-day4-view.png');
        await page.screenshot({ path: day4Screenshot, fullPage: true });
        report.screenshots.push(day4Screenshot);
      }

      // Navigate to Day 8
      console.log('Navigating to Day 8...');
      const day8Clicked = await page.evaluate(() => {
        const buttons = Array.from(document.querySelectorAll('button, [role="tab"]'));
        const day8Button = buttons.find(btn =>
          btn.textContent.includes('Day 8') ||
          btn.textContent.includes('第8天') ||
          btn.textContent.includes('2月22日')
        );
        if (day8Button) {
          day8Button.click();
          return true;
        }
        return false;
      });

      if (day8Clicked) {
        await page.waitForTimeout(1500);

        const day8Transport = await page.evaluate(() => {
          const headings = Array.from(document.querySelectorAll('h3, h4, .section-title, [class*="title"]'));
          const transportHeading = headings.find(h =>
            h.textContent.includes('Transportation') ||
            h.textContent.includes('交通')
          );

          if (transportHeading) {
            const section = transportHeading.closest('section, div[class*="section"]') || transportHeading.parentElement;
            return {
              visible: true,
              html: section ? section.outerHTML.substring(0, 500) : transportHeading.outerHTML
            };
          }

          return { visible: false, html: '' };
        });

        report.transportation.day8 = day8Transport;

        const day8Screenshot = path.join(OUTPUT_DIR, '06-day8-view.png');
        await page.screenshot({ path: day8Screenshot, fullPage: true });
        report.screenshots.push(day8Screenshot);
      }
    }

    // Try to switch to Timeline view
    console.log('Looking for Timeline view...');
    const timelineClicked = await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button, [role="tab"]'));
      const timelineButton = buttons.find(btn =>
        btn.textContent.includes('Timeline') ||
        btn.textContent.includes('时间轴') ||
        btn.textContent.includes('时间线')
      );
      if (timelineButton) {
        timelineButton.click();
        return true;
      }
      return false;
    });

    if (timelineClicked) {
      await page.waitForTimeout(2000);

      const timelineData = await page.evaluate(() => {
        // Look for conflict indicators
        const conflictElements = document.querySelectorAll('[class*="conflict"], [class*="overlap"]');
        const hasConflicts = conflictElements.length > 0;

        // Get timeline HTML sample
        const timelineContainer = document.querySelector('[class*="timeline"], [class*="Timeline"]');
        const html = timelineContainer ? timelineContainer.outerHTML.substring(0, 1000) : '';

        return {
          conflicts_visible: hasConflicts,
          conflict_count: conflictElements.length,
          html: html
        };
      });

      report.timeline = timelineData;

      const timelineScreenshot = path.join(OUTPUT_DIR, '07-timeline-view.png');
      await page.screenshot({ path: timelineScreenshot, fullPage: true });
      report.screenshots.push(timelineScreenshot);
    }

    // Determine root cause
    console.log('Analyzing root cause...');
    if (report.images.unsplash_count > 0) {
      report.root_cause = `CRITICAL: Page still showing ${report.images.unsplash_count} Unsplash images. Expected 0 Unsplash, all images should be Gaode/Google. This indicates HTML was not regenerated with the fixed data.`;
    } else if (report.images.gaode_count === 0 && report.images.google_count === 0) {
      report.root_cause = `CRITICAL: No Gaode or Google images found. Found ${report.images.other_count} other images. The image source fixes were not applied.`;
    } else if (!report.transportation.day2.visible && !report.transportation.day3.visible) {
      report.root_cause = `CRITICAL: Transportation sections not visible on any checked days. The transportation data additions were not applied to the HTML.`;
    } else {
      report.root_cause = 'Some fixes may be partially applied but inconsistently.';
    }

  } catch (error) {
    report.console_errors.push({
      type: 'playwright_error',
      text: error.message,
      stack: error.stack,
      timestamp: new Date().toISOString()
    });
    report.root_cause = `Failed to complete inspection: ${error.message}`;
  } finally {
    await browser.close();
  }

  // Write report
  console.log('Writing report...');
  fs.writeFileSync(REPORT_PATH, JSON.stringify(report, null, 2));
  console.log(`Report written to: ${REPORT_PATH}`);
  console.log('\n=== QA INSPECTION SUMMARY ===');
  console.log(`Unsplash images: ${report.images.unsplash_count}`);
  console.log(`Gaode images: ${report.images.gaode_count}`);
  console.log(`Google images: ${report.images.google_count}`);
  console.log(`Day 2 Transportation: ${report.transportation.day2.visible ? 'VISIBLE' : 'NOT VISIBLE'}`);
  console.log(`Day 3 Transportation: ${report.transportation.day3.visible ? 'VISIBLE' : 'NOT VISIBLE'}`);
  console.log(`Day 4 Transportation: ${report.transportation.day4.visible ? 'VISIBLE' : 'NOT VISIBLE'}`);
  console.log(`Day 8 Transportation: ${report.transportation.day8.visible ? 'VISIBLE' : 'NOT VISIBLE'}`);
  console.log(`\nRoot Cause: ${report.root_cause}`);
  console.log('========================\n');

  return report;
}

inspectPage().catch(console.error);
