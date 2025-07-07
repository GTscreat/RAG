from ranking.top25 import refresh_top_and_score
from ranking.top10 import update_top_with_ai_score

def main():
    scores = refresh_top_and_score()
    if scores:
        print("OpenAI Scoring Results:\n", scores)
        # Call top10 to update ai_score and final_score
        update_top_with_ai_score(scores)
        print("Top table updated with ai_score and final_score.")
    else:
        print("No top content available.")

if __name__ == "__main__":
    main()