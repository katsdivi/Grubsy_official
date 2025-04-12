# app/keyword_grouper.py
from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering
from collections import defaultdict
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")  # Small and accurate

def group_similar_keywords(keywords: list[str], distance_threshold=0.5) -> dict:
    if len(keywords) <= 1:
        return {kw: [kw] for kw in keywords}

    embeddings = model.encode(keywords)

    clustering = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=distance_threshold,
        metric='euclidean',
        linkage='ward'
    )
    labels = clustering.fit_predict(embeddings)

    clusters = defaultdict(list)
    for idx, label in enumerate(labels):
        clusters[label].append(keywords[idx])

    grouped_keywords = {}
    for group in clusters.values():
        if len(group) == 1:
            grouped_keywords[group[0]] = group
        else:
            group_embeddings = model.encode(group)
            center = np.mean(group_embeddings, axis=0)
            distances = [np.linalg.norm(center - e) for e in group_embeddings]
            rep_idx = int(np.argmin(distances))
            grouped_keywords[group[rep_idx]] = group

    return grouped_keywords