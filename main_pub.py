import time
from spreader.selector import select_to_publish
from spreader.publishing import publishing_cycle

def main_loop():
    while True:
        select_to_publish()      # Սկզբում ընտրում ենք հրապարակման ենթակա նյութը 
        sleep_time = publishing_cycle()  # Հրապարակում ենք մեկ նյութ և ստանում ենք հաջորդ ցիկլի սպասման ժամանակը
        time.sleep(sleep_time)

if __name__ == "__main__":
    main_loop()