// Manual verification script to check shadcn sidebar conversion
// Run this in browser console at http://localhost:8081

console.log('=== SHADCN SIDEBAR VERIFICATION ===\n');

// 1. Check if React root is mounted
const root = document.getElementById('root');
console.log('✓ React root found:', root !== null);
console.log('  Root has children:', root?.children.length > 0);

// 2. Check for Header component
const header = document.querySelector('header');
console.log('\n✓ Header component found:', header !== null);
if (header) {
  console.log('  Header text:', header.textContent.trim());
  console.log('  Header classes:', header.className);
}

// 3. Check for Sidebar component
const sidebar = document.querySelector('aside');
console.log('\n✓ Sidebar component found:', sidebar !== null);
if (sidebar) {
  console.log('  Sidebar classes:', sidebar.className);
  console.log('  Sidebar width class:', sidebar.className.includes('w-60') ? 'w-60 ✓' : 'MISSING');
  console.log('  Border right:', sidebar.className.includes('border-r') ? 'border-r ✓' : 'MISSING');
  console.log('  Background:', sidebar.className.includes('bg-background') ? 'bg-background ✓' : 'MISSING');
}

// 4. Check for shadcn Button components in sidebar
const buttons = sidebar?.querySelectorAll('button');
console.log('\n✓ Buttons in sidebar:', buttons?.length || 0);
if (buttons && buttons.length > 0) {
  buttons.forEach((btn, i) => {
    console.log(`  Button ${i + 1}:`, btn.textContent.trim());
    console.log(`    Classes:`, btn.className);
    console.log(`    Has "justify-start":`, btn.className.includes('justify-start') ? '✓' : 'MISSING');
  });
}

// 5. Check for Separator components
const separators = sidebar?.querySelectorAll('[data-orientation], hr, .bg-border');
console.log('\n✓ Separators in sidebar:', separators?.length || 0);

// 6. Check for navigation content
const allLandingsBtn = Array.from(buttons || []).find(btn =>
  btn.textContent.trim() === 'All Landings'
);
console.log('\n✓ "All Landings" button found:', allLandingsBtn !== undefined);

const pinnedSection = document.getElementById('pinnedSection');
console.log('✓ "Pinned" section found:', pinnedSection !== null);

const sanDiegoSection = document.getElementById('sanDiegoSection');
console.log('✓ "San Diego" section found:', sanDiegoSection !== null);

// 7. Check main content area
const mainContent = document.querySelector('.flex-1.overflow-auto');
console.log('\n✓ Main content area found:', mainContent !== null);

const h1 = document.querySelector('h1');
console.log('✓ H1 title found:', h1 !== null);
if (h1) {
  console.log('  H1 text:', h1.textContent.trim());
}

// 8. Check for metrics cards
const cards = document.querySelectorAll('[class*="Card"]');
console.log('\n✓ Cards found:', cards.length);

// 9. Check for HSL color tokens in computed styles
if (sidebar) {
  const computedStyle = window.getComputedStyle(sidebar);
  console.log('\n✓ Sidebar computed background:', computedStyle.backgroundColor);
  console.log('✓ Sidebar computed border:', computedStyle.borderRight);
}

// 10. Console errors check
console.log('\n✓ Check browser console for any errors');
console.log('  (If you see React errors, the conversion needs fixing)');

console.log('\n=== VERIFICATION COMPLETE ===');
