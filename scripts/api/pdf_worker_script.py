"""
Standalone PDF worker — runs as a subprocess so Playwright gets a fresh
event loop (ProactorEventLoop on Windows) without conflicting with uvicorn.

Usage: python pdf_worker_script.py <folio> <frontend_url>
Output: raw PDF bytes written to stdout
"""
import sys
import asyncio
from playwright.async_api import async_playwright


async def main() -> None:
    folio = sys.argv[1]
    frontend_url = sys.argv[2]
    view_url = f"{frontend_url}/features/compressor-maintenance/reports/view?folio={folio}"

    print(f"📄 Opening: {view_url}", file=sys.stderr)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            page = await browser.new_page()
            await page.goto(view_url, wait_until="networkidle", timeout=30000)
            await page.wait_for_selector(".bg-white", timeout=10000)
            await page.wait_for_timeout(2000)

            await page.evaluate("""() => {
                document.querySelectorAll('.no-print').forEach(el => el.style.display = 'none');
                const sidebar = document.querySelector('aside');
                if (sidebar) sidebar.style.display = 'none';
                document.querySelectorAll('nav').forEach(nav => nav.style.display = 'none');
                document.querySelectorAll('[class*="fixed"], [class*="sticky"]').forEach(el => {
                    if (!el.closest('.bg-white.rounded-lg')) el.style.display = 'none';
                });
                document.body.style.backgroundColor = 'white';
                const main = document.querySelector('.min-h-screen');
                if (main) { main.style.minHeight = 'auto'; main.style.padding = '20px'; }
            }""")

            pdf_bytes = await page.pdf(
                format="A3",
                print_background=True,
                margin={"top": "0.5in", "right": "0.5in", "bottom": "0.5in", "left": "0.5in"},
                prefer_css_page_size=False,
            )
        finally:
            await browser.close()

    sys.stdout.buffer.write(pdf_bytes)
    print("✅ PDF generated", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
