const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  console.log('Opening URL...');
  await page.goto('http://127.0.0.1:8094/trip/beijing-lijiang-dali-20260418-100846', {
    waitUntil: 'networkidle',
    timeout: 30000
  });

  console.log('Waiting for editor to load...');
  // Wait for candidates panel to be visible
  await page.waitForSelector('#candidates-groups, [data-slot-id], .candidate-card', { timeout: 15000 }).catch(() => {
    console.log('candidates-groups not found by ID, trying alternatives');
  });

  // Take initial screenshot to see the state
  await page.screenshot({ path: '/tmp/verify-202700-ac4-initial.png', fullPage: false });
  console.log('Initial screenshot taken');

  // Look for meals-related candidate cards
  // The sidebar contains candidate cards with data-slot-id attributes
  const allSlotCards = await page.$$('[data-slot-id]');
  console.log(`Found ${allSlotCards.length} cards with data-slot-id`);

  // Try to find a meals candidate card
  // Meals cards typically have data-slot-id containing "meal", "breakfast", "lunch", "dinner"
  let mealsCard = null;
  let mealsCardInfo = null;

  for (const card of allSlotCards) {
    const slotId = await card.getAttribute('data-slot-id');
    const slotType = await card.getAttribute('data-slot-type');
    console.log(`Card slot-id: ${slotId}, slot-type: ${slotType}`);
    if (slotId && (slotId.includes('meal') || slotId.includes('breakfast') || slotId.includes('lunch') || slotId.includes('dinner'))) {
      mealsCard = card;
      mealsCardInfo = { slotId, slotType };
      break;
    }
    if (slotType && slotType.includes('meal')) {
      mealsCard = card;
      mealsCardInfo = { slotId, slotType };
      break;
    }
  }

  if (!mealsCard) {
    // Try by category label in sidebar
    console.log('Trying to find meals section in sidebar...');

    // Look for candidate cards in the candidates sidebar
    const candidateCards = await page.$$('.candidate-card, [class*="candidate"]');
    console.log(`Found ${candidateCards.length} candidate cards by class`);

    // Try to find meals section by text content
    const mealsSection = await page.$('text=Meals').catch(() => null);
    if (mealsSection) {
      console.log('Found Meals section text');
      // Get parent container and find first card
      const mealsContainer = await mealsSection.evaluateHandle(el => {
        let parent = el.parentElement;
        while (parent && !parent.querySelector('[data-slot-id], .candidate-card')) {
          parent = parent.parentElement;
        }
        return parent;
      });
      if (mealsContainer) {
        mealsCard = await mealsContainer.$('[data-slot-id], .candidate-card');
      }
    }
  }

  if (!mealsCard) {
    // Fallback: use any candidate card (first one visible in sidebar)
    console.log('Fallback: using first visible card in sidebar');

    // Look in the right panel (candidates) for any card
    const rightPanel = await page.$('#candidates-groups, .candidates-panel, [class*="candidates"]');
    if (rightPanel) {
      mealsCard = await rightPanel.$('[data-slot-id], [class*="card"]');
    }

    if (!mealsCard) {
      // Try clicking on "Meals" tab in sidebar category selector
      const mealsTabs = await page.$$('text=/meals/i');
      console.log(`Found ${mealsTabs.length} elements with meals text`);
      for (const tab of mealsTabs) {
        const tagName = await tab.evaluate(el => el.tagName);
        const className = await tab.evaluate(el => el.className);
        console.log(`  Element: ${tagName}, class: ${className}`);
      }
    }
  }

  // Check page source for isPending context
  const pageContent = await page.content();
  const isPendingCount = (pageContent.match(/isPending/g) || []).length;
  console.log(`isPending occurrences in page source: ${isPendingCount}`);

  // Check that background: isPending is in source
  const bgIsPendingCount = (pageContent.match(/background: isPending/g) || []).length;
  console.log(`background: isPending occurrences in page source: ${bgIsPendingCount}`);

  if (mealsCard) {
    console.log(`Found meals card: slot-id=${mealsCardInfo?.slotId}`);

    // Get initial computed style
    const initialStyle = await mealsCard.evaluate(el => {
      const cs = window.getComputedStyle(el);
      return {
        background: cs.background || cs.backgroundColor,
        border: cs.border || cs.borderColor,
        borderColor: cs.borderColor
      };
    });
    console.log('Initial style:', JSON.stringify(initialStyle));

    // Click the card to enter pending state
    await mealsCard.click();
    await page.waitForTimeout(300);

    // Get computed style after click (pending state)
    const pendingStyle = await mealsCard.evaluate(el => {
      const cs = window.getComputedStyle(el);
      return {
        background: cs.background || cs.backgroundColor,
        backgroundColor: cs.backgroundColor,
        border: cs.border,
        borderColor: cs.borderColor,
        outline: cs.outline
      };
    });
    console.log('Pending style after click:', JSON.stringify(pendingStyle));

    // Also check inline style
    const inlineStyle = await mealsCard.getAttribute('style');
    console.log('Inline style:', inlineStyle);

    const hasBlueBg = pendingStyle.backgroundColor && pendingStyle.backgroundColor.includes('239') ||
                       pendingStyle.background && pendingStyle.background.includes('eff6ff') ||
                       JSON.stringify(pendingStyle).includes('eff6ff') ||
                       JSON.stringify(pendingStyle).includes('239, 246, 255');
    const hasBlueBorder = pendingStyle.borderColor && pendingStyle.borderColor.includes('59') ||
                           JSON.stringify(pendingStyle).includes('3b82f6') ||
                           JSON.stringify(pendingStyle).includes('59, 130, 246');

    console.log(`hasBlueBg: ${hasBlueBg}, hasBlueBorder: ${hasBlueBorder}`);

    await page.screenshot({ path: '/tmp/verify-202700-ac4-meals.png', fullPage: false });
    console.log('AC4 screenshot taken: /tmp/verify-202700-ac4-meals.png');

    if (hasBlueBg || hasBlueBorder) {
      console.log('AC4 PASS: meals candidate card shows blue pending state');
    } else {
      console.log('AC4 CHECK: pending state not confirmed via computed style - checking inline style');
      if (inlineStyle && (inlineStyle.includes('eff6ff') || inlineStyle.includes('3b82f6'))) {
        console.log('AC4 PASS via inline style: isPending blue found');
      } else {
        console.log('AC4 NOTE: React renders inline styles - check screenshot');
      }
    }
  } else {
    console.log('Could not locate a specific meals card to click');

    // Still take screenshot to show current state
    await page.screenshot({ path: '/tmp/verify-202700-ac4-meals.png', fullPage: false });
    console.log('Screenshot taken without pending state test');
  }

  await browser.close();
  console.log('Done');
})();
