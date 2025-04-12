from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import yake
from collections import defaultdict
import math
from .keyword_grouper import group_similar_keywords

# ❌ Skip irrelevant keywords entirely
SKIP_TERMS = {
    "today", "entire", "lady", "thing", "point", "understand", "looked",
    "grabbed", "annoyed", "left", "fine", "positive", "experience", "broth",
    "sensennthe", "crazy", "great", "states", "brag", "absolute", "fast",
    "subpar", "good", "coming", "asked"
}

def generate_actionable_insights(reviews: list[str], max_keywords=30) -> tuple[dict, dict]:
    analyzer = SentimentIntensityAnalyzer()
    kw_extractor = yake.KeywordExtractor(lan="en", n=1, top=max_keywords)

    keyword_sentiments = defaultdict(lambda: {"count": 0, "neg_sum": 0.0, "pos_sum": 0.0})
    all_keywords = set()

    for review in reviews:
        # Normalize phrases like "spring rolls" before extracting
        review = review.replace("spring rolls", "spring_rolls")

        sentiment = analyzer.polarity_scores(review)["compound"]
        keywords = kw_extractor.extract_keywords(review)

        for kw, _ in keywords:
            kw = kw.lower().strip().replace("_", " ")
            if not kw.replace(" ", "").isalpha() or len(kw) < 3:
                continue

            all_keywords.add(kw)

            if sentiment < 0:
                keyword_sentiments[kw]["count"] += 1
                keyword_sentiments[kw]["neg_sum"] += abs(sentiment)
            elif sentiment > 0:
                keyword_sentiments[kw]["count"] += 1
                keyword_sentiments[kw]["pos_sum"] += sentiment

    grouped = group_similar_keywords(list(all_keywords))

    insights = {}
    strengths = {}
    scaling_factor = 7.0  # increased sensitivity

    for group_label, group_words in grouped.items():
        if group_label in SKIP_TERMS:
            continue

        total_count = 0
        total_neg = 0.0
        total_pos = 0.0

        for word in group_words:
            data = keyword_sentiments.get(word)
            if data:
                total_count += data["count"]
                total_neg += data["neg_sum"]
                total_pos += data["pos_sum"]

        if total_count < 2:
            continue

        if total_neg > total_pos:
            avg_neg = total_neg / total_count
            raw_score = math.log1p(total_count) * (avg_neg ** 1.3) * scaling_factor
            if avg_neg > 0.8:
                raw_score += 2

            importance = max(1, min(10, math.ceil(raw_score)))

            if importance >= 5:
                insights[group_label] = {
                    "mention_count": total_count,
                    "avg_neg_sentiment": round(avg_neg, 3),
                    "importance_rating": importance
                }
        else:
            avg_pos = total_pos / total_count
            strengths[group_label] = {
                "mention_count": total_count,
                "avg_pos_sentiment": round(avg_pos, 3)
            }

    sorted_insights = dict(sorted(insights.items(), key=lambda x: x[1]["importance_rating"], reverse=True)[:10])
    sorted_strengths = dict(sorted(strengths.items(), key=lambda x: x[1]["mention_count"], reverse=True))

    return sorted_insights, sorted_strengths

def generate_actionable_summaries(insights: dict) -> list[str]:
    summaries = []

    for keyword, data in insights.items():
        count = data["mention_count"]
        avg_neg = data.get("avg_neg_sentiment", 0.0)
        rating = data["importance_rating"]

        if rating >= 8:
            status = "⚠️ URGENT"
            tone = f"Multiple customers have complained about issues related to '{keyword}'. Immediate improvement is recommended."
        elif rating >= 5:
            status = "⏳ Moderate"
            tone = f"There are noticeable concerns around '{keyword}'. It's a good idea to review and enhance this area."
        else:
            status = "✅ Low"
            tone = f"'{keyword}' appears to be under control and isn't a major concern right now."

        summary = (
            f"{status} – {tone} Mentioned {count} times with an average negativity score of {avg_neg}."
        )
        summaries.append(summary)

    return summaries