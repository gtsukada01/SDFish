#!/usr/bin/env python3
"""
Playwright inspection script for fish-scraper dashboard
Captures screenshots and console logs from http://localhost:8081/index.html
"""

import asyncio
import json
from playwright.async_api import async_playwright
from pathlib import Path
import sys

async def inspect_dashboard():
    """Inspect the dashboard using Playwright"""
    async with async_playwright() as p:
        print("Launching browser...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        # Collect console messages
        console_messages = []
        page.on('console', lambda msg: console_messages.append({
            'type': msg.type,
            'text': msg.text
        }))

        # Collect errors
        page.on('pageerror', lambda err: console_messages.append({
            'type': 'error',
            'text': str(err)
        }))

        try:
            print("Navigating to http://localhost:8081/index.html...")
            await page.goto('http://localhost:8081/index.html', wait_until='networkidle', timeout=10000)

            # Wait for React to mount
            print("Waiting for React to mount...")
            await page.wait_for_selector('#root', timeout=5000)
            await asyncio.sleep(2)  # Give React time to render

            # Take full page screenshot
            print("Taking full page screenshot...")
            await page.screenshot(path='screenshot_full_page.png', full_page=True)

            # Take sidebar screenshot
            print("Taking sidebar screenshot...")
            sidebar = await page.query_selector('.sidebar')
            if sidebar:
                await sidebar.screenshot(path='screenshot_sidebar.png')

            # Take main content screenshot
            print("Taking main content screenshot...")
            main_content = await page.query_selector('.main-content')
            if main_content:
                await main_content.screenshot(path='screenshot_main_content.png')

            # Evaluate JavaScript to get React state
            print("Evaluating JavaScript...")
            react_info = await page.evaluate("""() => {
                const root = document.getElementById('root');
                const hasReactContent = root && root.innerHTML.length > 0;
                const metricsCards = document.querySelectorAll('[class*="metric"], [class*="card"]');
                const sidebar = document.querySelector('.sidebar');
                const filters = {
                    startDate: document.querySelector('[name="startDate"], #startDate'),
                    endDate: document.querySelector('[name="endDate"], #endDate'),
                    landingName: document.querySelector('[name="landingName"], #landingName'),
                    boat: document.querySelector('[name="boat"], #boat'),
                    allSpecies: document.querySelector('[name="allSpecies"], #allSpecies, [id*="species"]')
                };

                return {
                    reactMounted: hasReactContent,
                    rootInnerHTML: root ? root.innerHTML.substring(0, 500) : 'No root element',
                    metricsCardCount: metricsCards.length,
                    metricsCardClasses: Array.from(metricsCards).slice(0, 5).map(card => card.className),
                    sidebarHTML: sidebar ? sidebar.innerHTML.substring(0, 1000) : 'No sidebar',
                    filtersFound: {
                        startDate: !!filters.startDate,
                        endDate: !!filters.endDate,
                        landingName: !!filters.landingName,
                        boat: !!filters.boat,
                        allSpecies: !!filters.allSpecies
                    },
                    bodyClasses: document.body.className,
                    documentTitle: document.title
                };
            }""")

            # Get computed styles of key elements
            print("Getting computed styles...")
            styles_info = await page.evaluate("""() => {
                const sidebar = document.querySelector('.sidebar');
                const mainContent = document.querySelector('.main-content');
                const root = document.getElementById('root');

                const getStyles = (elem) => {
                    if (!elem) return null;
                    const computed = window.getComputedStyle(elem);
                    return {
                        display: computed.display,
                        backgroundColor: computed.backgroundColor,
                        color: computed.color,
                        width: computed.width,
                        padding: computed.padding,
                        border: computed.border
                    };
                };

                return {
                    sidebar: getStyles(sidebar),
                    mainContent: getStyles(mainContent),
                    root: getStyles(root)
                };
            }""")

            # Generate report
            report = {
                'url': page.url,
                'title': await page.title(),
                'console_messages': console_messages,
                'react_info': react_info,
                'styles_info': styles_info,
                'screenshots': {
                    'full_page': 'screenshot_full_page.png',
                    'sidebar': 'screenshot_sidebar.png',
                    'main_content': 'screenshot_main_content.png'
                }
            }

            # Save report as JSON
            with open('inspection_report.json', 'w') as f:
                json.dump(report, f, indent=2)

            # Print report
            print("\n" + "="*80)
            print("INSPECTION REPORT")
            print("="*80)
            print(f"\nURL: {report['url']}")
            print(f"Title: {report['title']}")
            print(f"\n--- React Mount Status ---")
            print(f"React Mounted: {react_info['reactMounted']}")
            print(f"Metrics Card Count: {react_info['metricsCardCount']}")
            print(f"Root innerHTML preview: {react_info['rootInnerHTML'][:200]}...")

            print(f"\n--- Filters Found (should be removed) ---")
            for filter_name, found in react_info['filtersFound'].items():
                status = "❌ FOUND (needs removal)" if found else "✅ Not found"
                print(f"{filter_name}: {status}")

            print(f"\n--- Console Messages ({len(console_messages)} total) ---")
            for msg in console_messages[:10]:  # Show first 10
                print(f"[{msg['type']}] {msg['text']}")
            if len(console_messages) > 10:
                print(f"... and {len(console_messages) - 10} more messages")

            print(f"\n--- Sidebar Styles ---")
            if styles_info['sidebar']:
                for key, value in styles_info['sidebar'].items():
                    print(f"{key}: {value}")

            print(f"\n--- Screenshots Generated ---")
            for name, path in report['screenshots'].items():
                print(f"{name}: {path}")

            print(f"\nFull report saved to: inspection_report.json")
            print("="*80)

        except Exception as e:
            print(f"Error during inspection: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(inspect_dashboard())
