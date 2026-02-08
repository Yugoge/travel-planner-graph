/**
 * Playwright script to inspect LOCAL travel planner HTML file
 * Captures screenshots, extracts image URLs, checks Transportation sections
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const LOCAL_HTML = path.join(__dirname, '..', 'travel-plan-china-feb-15-mar-7-2026-20260202-195429.html');
const OUTPUT_DIR = path.join(__dirname, '..', 'docs', 'dev', 'playwright-screenshots');
const REPORT_PATH = path.join(__dirname, '..', 'docs', 'dev', 'qa-report-playwright-20260207.json');

async function inspectPage() {
  console.log('Starting Playwright inspection of LOCAL HTML...');
  console.log(`Target file: ${LOCAL_HTML}`);

  // Check file exists
  if (!fs.existsSync(LOCAL_HTML)) {
    console.error(`ERROR: HTML file not found at ${LOCAL_HTML}`);
    process.exit(1);
  }

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
    source: 'local_file',
    file_path: LOCAL_HTML,
    screenshots: [],
    images: {
      all_urls: [],
      unsplash_count: 0,
      gaode_count: 0,
      google_count: 0,
      other_count: 0,
      unsplash_examples: [],
      gaode_examples: [],
      google_examples: []
    },
    transportation: {
      day2: { visible: false, html: '', data_exists: false },
      day3: { visible: false, html: '', data_exists: false },
      day4: { visible: false, html: '', data_exists: false },
      day8: { visible: false, html: '', data_exists: false }
    },
    timeline: {
      conflicts_visible: false,
      html: ''
    },
    plan_data: {
      exists: false,
      sample: {}
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
    console.log(`Loading file: file://${LOCAL_HTML}`);
    await page.goto(`file://${LOCAL_HTML}`, { waitUntil: 'networkidle', timeout: 30000 });

    console.log('Waiting for React app to load...');
    await page.waitForTimeout(3000);

    // Check if PLAN_DATA is available
    const planDataCheck = await page.evaluate(() => {
      if (typeof window.PLAN_DATA === 'undefined') {
        return { exists: false, sample: {} };
      }

      // Get sample of PLAN_DATA structure
      const sample = {
        exists: true,
        has_trips: Array.isArray(window.PLAN_DATA.trips),
        trip_count: window.PLAN_DATA.trips ? window.PLAN_DATA.trips.length : 0,
        first_trip_days: window.PLAN_DATA.trips && window.PLAN_DATA.trips[0] ? window.PLAN_DATA.trips[0].days.length : 0,
        day2_has_transportation: false,
        day2_transportation_sample: null
      };

      if (window.PLAN_DATA.trips && window.PLAN_DATA.trips[0] && window.PLAN_DATA.trips[0].days[1]) {
        const day2 = window.PLAN_DATA.trips[0].days[1];
        sample.day2_has_transportation = !!day2.transportation;
        if (day2.transportation) {
          sample.day2_transportation_sample = {
            morning: day2.transportation.morning ? day2.transportation.morning.substring(0, 100) : null,
            afternoon: day2.transportation.afternoon ? day2.transportation.afternoon.substring(0, 100) : null,
            evening: day2.transportation.evening ? day2.transportation.evening.substring(0, 100) : null
          };
        }
      }

      return sample;
    });

    report.plan_data = planDataCheck;
    console.log(`PLAN_DATA exists: ${planDataCheck.exists}`);
    console.log(`Day 2 has transportation in data: ${planDataCheck.day2_has_transportation}`);

    // Take initial screenshot
    console.log('Taking initial screenshot...');
    const initialScreenshot = path.join(OUTPUT_DIR, '01-initial-load.png');
    await page.screenshot({ path: initialScreenshot, fullPage: true });
    report.screenshots.push('01-initial-load.png');

    // Extract ALL image URLs
    console.log('Extracting image URLs...');
    const imageData = await page.evaluate(() => {
      const images = Array.from(document.querySelectorAll('img'));
      return images.map(img => ({
        src: img.src,
        alt: img.alt,
        visible: img.offsetWidth > 0 && img.offsetHeight > 0,
        width: img.offsetWidth,
        height: img.offsetHeight
      }));
    });

    report.images.all_urls = imageData;

    // Count image types and collect examples
    imageData.forEach(img => {
      const src = img.src.toLowerCase();
      if (src.includes('unsplash')) {
        report.images.unsplash_count++;
        if (report.images.unsplash_examples.length < 3) {
          report.images.unsplash_examples.push(img.src);
        }
      } else if (src.includes('autonavi') || src.includes('amap') || src.includes('gaode')) {
        report.images.gaode_count++;
        if (report.images.gaode_examples.length < 3) {
          report.images.gaode_examples.push(img.src);
        }
      } else if (src.includes('googleapis') || src.includes('googleusercontent')) {
        report.images.google_count++;
        if (report.images.google_examples.length < 3) {
          report.images.google_examples.push(img.src);
        }
      } else {
        report.images.other_count++;
      }
    });

    console.log(`Image counts - Unsplash: ${report.images.unsplash_count}, Gaode: ${report.images.gaode_count}, Google: ${report.images.google_count}, Other: ${report.images.other_count}`);

    // Check for day navigation buttons
    const dayButtonsExist = await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button, [role="tab"]'));
      const dayButtons = buttons.filter(btn => btn.textContent.includes('Day') || btn.textContent.includes('日'));
      return dayButtons.length > 0;
    });

    console.log(`Day navigation buttons exist: ${dayButtonsExist}`);

    // Try to find and click Day 2
    if (dayButtonsExist) {
      // Take screenshot of Day 1 first
      console.log('Taking Day 1 screenshot...');
      const day1Screenshot = path.join(OUTPUT_DIR, '02-day1-view.png');
      await page.screenshot({ path: day1Screenshot, fullPage: true });
      report.screenshots.push('02-day1-view.png');

      // Navigate to Day 2
      console.log('Navigating to Day 2...');
      const day2Result = await page.evaluate(() => {
        const buttons = Array.from(document.querySelectorAll('button, [role="tab"]'));
        const day2Button = buttons.find(btn =>
          btn.textContent.includes('Day 2') ||
          btn.textContent.includes('第2天') ||
          btn.textContent.includes('2月16日')
        );
        if (day2Button) {
          day2Button.click();
          return { clicked: true, text: day2Button.textContent };
        }
        return { clicked: false, text: null };
      });

      console.log(`Day 2 button clicked: ${day2Result.clicked}, text: ${day2Result.text}`);

      if (day2Result.clicked) {
        await page.waitForTimeout(1500);

        // Check for Transportation section on Day 2
        const day2Transport = await page.evaluate(() => {
          const headings = Array.from(document.querySelectorAll('h3, h4, h5, .section-title, [class*="title"], [class*="Title"]'));
          const transportHeading = headings.find(h =>
            h.textContent.includes('Transportation') ||
            h.textContent.includes('交通') ||
            h.textContent.includes('Transport')
          );

          const result = {
            visible: false,
            html: '',
            data_exists: false,
            heading_found: !!transportHeading,
            all_headings: headings.map(h => h.textContent.substring(0, 50))
          };

          if (transportHeading) {
            const section = transportHeading.closest('section, div[class*="section"], div[class*="Section"]') || transportHeading.parentElement;
            result.visible = true;
            result.html = section ? section.outerHTML.substring(0, 500) : transportHeading.outerHTML;
          }

          // Check PLAN_DATA
          if (window.PLAN_DATA && window.PLAN_DATA.trips && window.PLAN_DATA.trips[0] && window.PLAN_DATA.trips[0].days[1]) {
            result.data_exists = !!window.PLAN_DATA.trips[0].days[1].transportation;
          }

          return result;
        });

        report.transportation.day2 = day2Transport;
        console.log(`Day 2 Transportation - Heading found: ${day2Transport.heading_found}, Visible: ${day2Transport.visible}, Data exists: ${day2Transport.data_exists}`);

        const day2Screenshot = path.join(OUTPUT_DIR, '03-day2-view.png');
        await page.screenshot({ path: day2Screenshot, fullPage: true });
        report.screenshots.push('03-day2-view.png');
      }

      // Navigate to Day 3
      console.log('Navigating to Day 3...');
      const day3Result = await page.evaluate(() => {
        const buttons = Array.from(document.querySelectorAll('button, [role="tab"]'));
        const day3Button = buttons.find(btn =>
          btn.textContent.includes('Day 3') ||
          btn.textContent.includes('第3天') ||
          btn.textContent.includes('2月17日')
        );
        if (day3Button) {
          day3Button.click();
          return { clicked: true, text: day3Button.textContent };
        }
        return { clicked: false, text: null };
      });

      if (day3Result.clicked) {
        await page.waitForTimeout(1500);

        const day3Transport = await page.evaluate(() => {
          const headings = Array.from(document.querySelectorAll('h3, h4, h5, .section-title, [class*="title"], [class*="Title"]'));
          const transportHeading = headings.find(h =>
            h.textContent.includes('Transportation') ||
            h.textContent.includes('交通') ||
            h.textContent.includes('Transport')
          );

          const result = {
            visible: false,
            html: '',
            data_exists: false
          };

          if (transportHeading) {
            const section = transportHeading.closest('section, div[class*="section"], div[class*="Section"]') || transportHeading.parentElement;
            result.visible = true;
            result.html = section ? section.outerHTML.substring(0, 500) : transportHeading.outerHTML;
          }

          if (window.PLAN_DATA && window.PLAN_DATA.trips && window.PLAN_DATA.trips[0] && window.PLAN_DATA.trips[0].days[2]) {
            result.data_exists = !!window.PLAN_DATA.trips[0].days[2].transportation;
          }

          return result;
        });

        report.transportation.day3 = day3Transport;

        const day3Screenshot = path.join(OUTPUT_DIR, '04-day3-view.png');
        await page.screenshot({ path: day3Screenshot, fullPage: true });
        report.screenshots.push('04-day3-view.png');
      }

      // Navigate to Day 4
      console.log('Navigating to Day 4...');
      const day4Result = await page.evaluate(() => {
        const buttons = Array.from(document.querySelectorAll('button, [role="tab"]'));
        const day4Button = buttons.find(btn =>
          btn.textContent.includes('Day 4') ||
          btn.textContent.includes('第4天') ||
          btn.textContent.includes('2月18日')
        );
        if (day4Button) {
          day4Button.click();
          return { clicked: true };
        }
        return { clicked: false };
      });

      if (day4Result.clicked) {
        await page.waitForTimeout(1500);

        const day4Transport = await page.evaluate(() => {
          const headings = Array.from(document.querySelectorAll('h3, h4, h5, .section-title, [class*="title"], [class*="Title"]'));
          const transportHeading = headings.find(h =>
            h.textContent.includes('Transportation') ||
            h.textContent.includes('交通') ||
            h.textContent.includes('Transport')
          );

          const result = {
            visible: false,
            html: '',
            data_exists: false
          };

          if (transportHeading) {
            const section = transportHeading.closest('section, div[class*="section"], div[class*="Section"]') || transportHeading.parentElement;
            result.visible = true;
            result.html = section ? section.outerHTML.substring(0, 500) : transportHeading.outerHTML;
          }

          if (window.PLAN_DATA && window.PLAN_DATA.trips && window.PLAN_DATA.trips[0] && window.PLAN_DATA.trips[0].days[3]) {
            result.data_exists = !!window.PLAN_DATA.trips[0].days[3].transportation;
          }

          return result;
        });

        report.transportation.day4 = day4Transport;

        const day4Screenshot = path.join(OUTPUT_DIR, '05-day4-view.png');
        await page.screenshot({ path: day4Screenshot, fullPage: true });
        report.screenshots.push('05-day4-view.png');
      }

      // Navigate to Day 8
      console.log('Navigating to Day 8...');
      const day8Result = await page.evaluate(() => {
        const buttons = Array.from(document.querySelectorAll('button, [role="tab"]'));
        const day8Button = buttons.find(btn =>
          btn.textContent.includes('Day 8') ||
          btn.textContent.includes('第8天') ||
          btn.textContent.includes('2月22日')
        );
        if (day8Button) {
          day8Button.click();
          return { clicked: true };
        }
        return { clicked: false };
      });

      if (day8Result.clicked) {
        await page.waitForTimeout(1500);

        const day8Transport = await page.evaluate(() => {
          const headings = Array.from(document.querySelectorAll('h3, h4, h5, .section-title, [class*="title"], [class*="Title"]'));
          const transportHeading = headings.find(h =>
            h.textContent.includes('Transportation') ||
            h.textContent.includes('交通') ||
            h.textContent.includes('Transport')
          );

          const result = {
            visible: false,
            html: '',
            data_exists: false
          };

          if (transportHeading) {
            const section = transportHeading.closest('section, div[class*="section"], div[class*="Section"]') || transportHeading.parentElement;
            result.visible = true;
            result.html = section ? section.outerHTML.substring(0, 500) : transportHeading.outerHTML;
          }

          if (window.PLAN_DATA && window.PLAN_DATA.trips && window.PLAN_DATA.trips[0] && window.PLAN_DATA.trips[0].days[7]) {
            result.data_exists = !!window.PLAN_DATA.trips[0].days[7].transportation;
          }

          return result;
        });

        report.transportation.day8 = day8Transport;

        const day8Screenshot = path.join(OUTPUT_DIR, '06-day8-view.png');
        await page.screenshot({ path: day8Screenshot, fullPage: true });
        report.screenshots.push('06-day8-view.png');
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
        const conflictElements = document.querySelectorAll('[class*="conflict"], [class*="overlap"], [class*="Conflict"], [class*="Overlap"]');
        const hasConflicts = conflictElements.length > 0;

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
      report.screenshots.push('07-timeline-view.png');
    }

    // Determine root cause
    console.log('Analyzing root cause...');
    const issues = [];

    if (report.images.unsplash_count > 0) {
      issues.push(`CRITICAL: Page showing ${report.images.unsplash_count} Unsplash images (expected 0)`);
    }

    if (report.images.gaode_count === 0 && report.images.google_count === 0) {
      issues.push(`CRITICAL: No Gaode or Google images found (expected 100)`);
    }

    if (report.transportation.day2.data_exists && !report.transportation.day2.visible) {
      issues.push(`CRITICAL: Day 2 transportation exists in PLAN_DATA but not rendered in UI`);
    } else if (!report.transportation.day2.data_exists) {
      issues.push(`CRITICAL: Day 2 transportation missing from PLAN_DATA`);
    }

    if (!report.transportation.day3.visible && !report.transportation.day4.visible && !report.transportation.day8.visible) {
      issues.push(`CRITICAL: Transportation sections not visible on any checked days`);
    }

    report.root_cause = issues.length > 0 ? issues.join('\n') : 'Unable to determine specific issues - inspection incomplete';

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
  console.log(`Total images: ${report.images.all_urls.length}`);
  console.log(`Unsplash images: ${report.images.unsplash_count}`);
  console.log(`Gaode images: ${report.images.gaode_count}`);
  console.log(`Google images: ${report.images.google_count}`);
  console.log(`Other images: ${report.images.other_count}`);
  console.log(`\nPLAN_DATA exists: ${report.plan_data.exists}`);
  console.log(`Day 2 Transportation in data: ${report.plan_data.day2_has_transportation}`);
  console.log(`Day 2 Transportation visible: ${report.transportation.day2.visible ? 'YES' : 'NO'}`);
  console.log(`Day 3 Transportation visible: ${report.transportation.day3.visible ? 'YES' : 'NO'}`);
  console.log(`Day 4 Transportation visible: ${report.transportation.day4.visible ? 'YES' : 'NO'}`);
  console.log(`Day 8 Transportation visible: ${report.transportation.day8.visible ? 'YES' : 'NO'}`);
  console.log(`\nRoot Cause:\n${report.root_cause}`);
  console.log('========================\n');

  return report;
}

inspectPage().catch(console.error);
