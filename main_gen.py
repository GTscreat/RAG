from composer.selector import get_next_unprocessed_top_id
from composer.composing import prompt_gen_request, generate_content_with_openai, save_processed

def main():
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

if __name__ == "__main__":
    main()