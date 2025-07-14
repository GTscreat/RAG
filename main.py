import time
import threading

# --- Collector Imports ---
from collector.get_api import fetch_articles, insert_articles_to_db
from collector.chunker import chunk_articles_and_store
from collector.embedding import embed_chunks
from collector.utils import filter_new_articles
from collector.ner import load_ner_pipeline, run_ner_on_articles, save_ner_results_to_db
from ranker.frequency_classifier import update_aver_embeddings, run_frequency_classifier
from ranker.thematic_classifier import run_thematic_classifier
from ranker.ranking import rank_news
from db import SessionLocal, Embedding

# --- Top Scoring Imports ---
from ranker.top25 import refresh_top_and_score
from ranker.top_over import update_top_with_ai_score

# --- Content Generation Imports ---
from composer.selector import get_next_unprocessed_top_id
from composer.composing import prompt_gen_request, generate_content_with_openai, save_processed

# --- Spreader Imports ---
from spreader.selector import select_to_publish
from spreader.publishing import publishing_cycle, get_urgent_value

def main_blocks():
    ner_pipeline = load_ner_pipeline()
    while True:
        print("----- Կատարվում է API հարցում -----")
        data = fetch_articles()
        if data is None:
            print("Հոդվածներ ստանալը ձախողվեց։ Սպասում ենք հաջորդ ցիկլին...")
            time.sleep(180)
            continue

        articles = data.get('data', [])
        if not articles:
            print("Հոդվածների ցանկը դատարկ է։ Սպասում ենք հաջորդ ցիկլին...")
            time.sleep(180)
            continue

        new_articles = filter_new_articles(articles)
        if not new_articles:
            print("Նոր հոդվածներ չկան։ Սպասում ենք հաջորդ ցիկլին...")
            time.sleep(180)
            continue

        print(f"{len(new_articles)} նոր հոդված հայտնաբերվեց։")
        print("----- Ավելացնում ենք նոր հոդվածները բազայում -----")
        insert_articles_to_db(new_articles)

        print("----- Կատարվում է չանկավորում և պահում -----")
        chunk_articles_and_store(new_articles)

        print("----- Կատարվում է embedding-ի հաշվարկ և պահում -----")
        session = SessionLocal()
        chunks_to_embed = session.query(Embedding).filter(Embedding.embedding == None).all()
        chunk_dicts = [{
            "id": ch.id,
            "website": ch.website,
            "title": ch.title,
            "published_at": ch.published_at,
            "url": ch.url,
            "meta": ch.meta,
            "chunk_content": ch.chunk_content,
            "chunk_start": ch.chunk_start,
            "chunk_end": ch.chunk_end,
        } for ch in chunks_to_embed]
        session.close()

        if chunk_dicts:
            embed_chunks(chunk_dicts, save_mode="update")
            print(f"{len(chunk_dicts)} embedding computed and saved.")
        else:
            print("Embedding-ը արդեն հաշվարկված է բոլոր չանկերի համար։")

        print("----- Կատարվում է Named Entity Recognition (NER) և պահում -----")
        ner_results = run_ner_on_articles(new_articles, ner_pipeline)
        save_ner_results_to_db(ner_results)
        print(f"NER արդյունքները պահված են բազայում։")

        print("----- Կատարվում է aver_embedding-ի թարմացում -----")
        update_aver_embeddings()

        print("----- Կատարվում է թեմատիկ դասակարգում -----")
        run_thematic_classifier()

        print("----- Կատարվում է հաճախականության դասակարգում -----")
        run_frequency_classifier()

        print("----- Կատարվում է նյութերի վարկանիշավորում -----")
        rank_news()

        print("----- Կատարվում է TOP վարկանիշային աղյուսակի թարմացում և AI scoring -----")
        scores = refresh_top_and_score()
        if scores:
            print("OpenAI Scoring Results:\n", scores)
            update_top_with_ai_score(scores)
            print("Top table updated with ai_score and final_score.")
        else:
            print("No top content available.")

        print("----- Կատարվում է նոր գեներացված կոնտենտի ստեղծում TOP-ի համար -----")
        processed_count = 0
        for _ in range(10):
            next_id = get_next_unprocessed_top_id()
            if not next_id:
                print("No new top content to process.")
                break
            prompt, content = prompt_gen_request(next_id)
            generated = generate_content_with_openai(prompt, content)
            save_processed(next_id, generated)
            print(f"Generated and saved new content for base_id={next_id}")
            processed_count += 1
        print(f"Done. Total processed: {processed_count}")

        print("----- Բլոկները ավարտվեցին, սպասում ենք 3 րոպե -----")
        time.sleep(180)  # 3 րոպե

def spreader_block(wakeup_event):
    while True:
        print("----- Սկսվում է հրապարակման ցիկլ (SPREADER) -----")
        select_to_publish()
        print("[DEBUG] select_to_publish() ավարտվեց")
        sleep_time = publishing_cycle()
        print(f"[DEBUG] publishing_cycle() sleep_time={sleep_time}")
        print(f"Հրապարակման ցիկլից հետո սպասում ենք {sleep_time} վայրկյան...")
        woke_up = wakeup_event.wait(timeout=sleep_time)
        if woke_up:
            print("[SPREADER] Urgent detected, waking up for immediate publishing.")
            wakeup_event.clear()

def spreader_monitor(wakeup_event, check_interval=30):
    last_urgent = None
    while True:
        urgent = get_urgent_value()
        if urgent and urgent > 0:
            if last_urgent != urgent:
                print(f"[MONITOR] Urgent content detected ({urgent}), waking up spreader!")
                wakeup_event.set()
        last_urgent = urgent
        time.sleep(check_interval)

if __name__ == "__main__":
    main_thread = threading.Thread(target=main_blocks, daemon=True)
    main_thread.start()

    # Event to wake up spreader if urgent content appears
    wakeup_event = threading.Event()

    spreader_thread = threading.Thread(target=spreader_block, args=(wakeup_event,), daemon=True)
    spreader_thread.start()

    monitor_thread = threading.Thread(target=spreader_monitor, args=(wakeup_event,), daemon=True)
    monitor_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Դադարեցվեց գործարկումը։")