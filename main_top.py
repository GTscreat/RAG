# main_top.py

from ranking.top25 import get_top_ids, get_top_contents, ask_openai_for_top

def main():
    # 1. Թարմացնել TOP-25 աղյուսակը
    top_ids = get_top_ids()
    print("TOP-25 ids:", top_ids)

    # 2. Վերցնել TOP-25-ի կոնտենտները
    id_to_content = get_top_contents(top_ids)

    # 3. Ուղարկել OpenAI-ին և ստանալ պատասխաններ
    results = ask_openai_for_top(top_ids, id_to_content)
    for id_, answer in results.items():
        print(f"ID {id_}:\n{answer}\n{'-'*40}")

if __name__ == "__main__":
    main()