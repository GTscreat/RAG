from ranker.top25 import refresh_top_and_score
from ranker.top_over import update_top_with_ai_score

def main():
    scores = refresh_top_and_score()
    if scores:
        print("OpenAI Scoring Results:\n", scores)
        update_top_with_ai_score(scores)
        print("Top table updated with ai_score and final_score.")
    else:
        print("No top content available.")

if __name__ == "__main__":
    main()