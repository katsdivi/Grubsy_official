# utils.py
def calculate_average_rating(ratings: list[str | int]) -> float:
    numeric_ratings = [int(r) for r in ratings if str(r).strip().isdigit()]
    if not numeric_ratings:
        return 0.0
    return round(sum(numeric_ratings) / len(numeric_ratings), 2)
