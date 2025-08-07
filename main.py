import time
import threading

# --- Collector Imports ---
# ՓՈՓՈԽՎԱԾ Է. Հեռացնում ենք հին ֆունկցիաները, ներմուծում ենք նորը
from collector.article_selector import select_new_articles
from collector.chunker import chunk_articles_and_store
from collector.embedding import embed_chunks
from collector.ner import load_ner_pipeline, run_ner_on_articles, save_ner_results_to_db
# --- Ranker Imports ---
from ranker.frequency_classifier import update_aver_embeddings, run_frequency_classifier
from ranker.thematic_classifier import run_thematic_classifier
from ranker.ranking import rank_news
from db import SessionLocal, Embedding

# --- Top Scoring Imports ---
from ranker.top25 import refresh_top_and_score

# --- Content Generation Imports ---
from composer.selector import get_next_unprocessed_top_id
from composer.composing import prompt_gen_request, generate_content_with_openai, save_processed
from composer.composing_ru import prompt_gen_request_ru, generate_content_with_openai_ru, save_processed_ru

# --- Spreader Imports ---
from spreader.selector import select_to_publish
from spreader.publishing import publishing_cycle, get_urgent_value, publishing_cycle_ru

def main_blocks():
    ner_pipeline = load_ner_pipeline()
    while True:
        # =================================================================
        # === ՀԻՄՆԱԿԱՆ ՌԵՖԱԿՏՈՐԻՆԳ ===
        # Հին API-ի հետ կապված տրամաբանությունը փոխարինվում է մեկ ֆունկցիայի կանչով
        # =================================================================
        
        new_articles_to_process = select_new_articles()

        if not new_articles_to_process:
            print("Նոր հոդվածներ չկան մշակման համար։ Սպասում ենք հաջորդ ցիկլին...")
            time.sleep(90)
            continue
        
        # Հաջորդ քայլերը սկսվում են անմիջապես, քանի որ հոդվածներն արդեն բազայում են
        # և ընտրված են մշակման համար։
        print("----- Կատարվում է չանկավորում և պահում -----")
        chunk_articles_and_store(new_articles_to_process)

        print("----- Կատարվում է embedding-ի հաշվարկ և պահում -----")
        # ԲԱՐԵԼԱՎՈՒՄ. Սեսիայի կառավարում 'with' բլոկով
        with SessionLocal() as session:
            chunks_to_embed = session.query(Embedding).filter(Embedding.embedding.is_(None)).all()
            # ՈՒՂՂՈՒՄ. 'website' -> 'website_id' մեր նոր մոդելին համապատասխան
            # ԹԱՐՄԱՑՎԱԾ ԲԱՌԱՐԱՆԻ ՍՏԵՂԾՈՒՄ
            chunk_dicts = [{
                "id": ch.id,
                "chunk_content": ch.chunk_content,
            } for ch in chunks_to_embed]

        if chunk_dicts:
            embed_chunks(chunk_dicts, save_mode="update")
            print(f"{len(chunk_dicts)} embedding հաշվարկվեց և պահպանվեց։")
        else:
            print("Embedding-ն արդեն հաշվարկված է բոլոր չանկերի համար։")
  

        print("----- Կատարվում է Named Entity Recognition (NER) և պահում -----")
        ner_results = run_ner_on_articles(new_articles_to_process, ner_pipeline)
        save_ner_results_to_db(ner_results)
        
        # NER-ի արդյունքների պահպանման տպելու հրամանը տեղափոխված է save_ner_results_to_db ֆունկցիայի մեջ,
        # ուստի այստեղ այն այլևս պետք չէ կրկնել։

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
            # update_top_with_ai_score-ը արդեն կանչվում է refresh_top_and_score-ի ներսում,
            # ուստի այստեղ այն կրկնելու կարիք չկա։
            print("Top table updated with ai_score and final_score.")
        else:
            print("No top content available.")

        print("----- Կատարվում է նոր գեներացված կոնտենտի ստեղծում TOP-ի համար -----")
        for _ in range(10): # Փորձում ենք մշակել մինչև 10 նյութ
            next_id = get_next_unprocessed_top_id()
            if not next_id:
                print("No new top content to process.")
                break
        
            # Armenian content
            prompt, content_data = prompt_gen_request(next_id)
            if prompt and content_data:
                generated = generate_content_with_openai(prompt, content_data)
                save_processed(next_id, generated)
                print(f"Generated and saved Armenian content for base_id={next_id}")
        
            # Russian content
            prompt_ru, content_data_ru = prompt_gen_request_ru(next_id)
            if prompt_ru and content_data_ru:
                generated_ru = generate_content_with_openai_ru(prompt_ru, content_data_ru)
                save_processed_ru(next_id, generated_ru)
                print(f"Generated and saved Russian content for base_id={next_id}")

        print("----- Շրջանն ավարտվեց, սպասում ենք 1.5 րոպե -----")
        time.sleep(90)

# spreader_block, spreader_monitor և if __name__ == "__main__" բլոկերը մնում են անփոփոխ
def spreader_block(wakeup_event):
    # ... (անփոփոխ)
    while True:
        print("----- Սկսվում է հրապարակման ցիկլ (SPREADER) -----")
        select_to_publish()
        print("[DEBUG] select_to_publish() ավարտվեց")
        sleep_time = publishing_cycle()
        if sleep_time is None:
            sleep_time = 90  # default value
        publishing_cycle_ru() # Ru cycle doesn't need to return sleep time
        print(f"Հրապարակման ցիկլից հետո սպասում ենք {sleep_time} վայրկյան...")
        woke_up = wakeup_event.wait(timeout=sleep_time)
        if woke_up:
            print("[SPREADER] Urgent detected, waking up for immediate publishing.")
            wakeup_event.clear()

def spreader_monitor(wakeup_event, check_interval=30):
    # ... (անփոփոխ)
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
    # ... (անփոփոխ)
    main_thread = threading.Thread(target=main_blocks, daemon=True)
    main_thread.start()
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