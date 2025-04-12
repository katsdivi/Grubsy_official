// index.js (ESM)
import { scraper } from 'google-maps-review-scraper';

const url = process.argv[2];
if (!url) {
  console.error("❌ Error: No URL provided.");
  process.exit(1);
}

(async () => {
  try {
    const reviews = await scraper(url, {
      sort_type: "newest",
      pages: 10,
      clean: true,
    });
    console.log(JSON.stringify(reviews));
  } catch (err) {
    console.error("❌ Scraper failed:", err.message || err);
    process.exit(1);
  }
})();
