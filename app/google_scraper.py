from playwright.sync_api import sync_playwright
import time

def scrape_google_reviews(url: str, scrolls: int = 10) -> list[str]:
    reviews = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto(url, timeout=60000)

        time.sleep(5)  # Wait for content to load

        # Scroll the reviews modal
        for _ in range(scrolls):
            page.keyboard.press("PageDown")
            time.sleep(1)

        # Extract review text (adjust this selector as needed)
        review_blocks = page.locator("span[jsname='bN97Pc']").all()

        for block in review_blocks:
            text = block.inner_text().strip()
            if text:
                reviews.append(text)

        browser.close()

    return reviews