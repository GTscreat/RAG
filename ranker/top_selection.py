def select_top_n(scored_articles, N=30):
    # scored_articles: list of dicts with 'score' key
    sorted_articles = sorted(scored_articles, key=lambda x: x['score'], reverse=True)
    return sorted_articles[:N]