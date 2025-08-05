python -m venv venv
.\venv\Scripts\Activate.ps1
Եթե չի ստացվում - Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
pip install -r requirements.txt

.\venv\Scripts\python.exe -m pip install ......

2. 
python -m venv .venv
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python.exe -m pip install ......
pip install -r requirements.txt


git status
git add .
git commit -m "update 1"
git push origin master
git status

git pull

git reset --mixed HEAD~1 #չեղարկում է commit-ները
git rm --cached <ֆայլի_անունը> #Հեռացնել ֆայլը commit արված ցանկից (staging area-ից)


DELETE FROM embeddings;
DELETE FROM parameters;
DELETE FROM ranks;
DELETE FROM top;
DELETE FROM processed;

DROP TABLE ...;

GRANT SELECT ON entities TO public;
GRANT SELECT ON entity_categories TO public;

-- 2. Վերցնել INSERT, UPDATE, DELETE իրավունքները
REVOKE INSERT, UPDATE, DELETE ON entities FROM public;
REVOKE INSERT, UPDATE, DELETE ON entity_categories FROM public;


# AI-Powered News Pipeline - A System for News Aggregation and Content Generation

This is a multi-threaded Python application designed for the automated aggregation, processing, analysis, and ranking of news from Armenian sources. Based on this analysis, it generates unique content in both Armenian and Russian for subsequent publication on Telegram channels.

---

## **Core Features**

* **Automatic Aggregation:** Periodically fetches new articles from various news websites via an external API.
* **Intelligent Processing:**
    * Segments article text into logical parts (chunks).
    * Creates a vector representation (embedding) for each chunk using `sentence-transformers`.
    * Performs Named Entity Recognition (NER) to extract key persons, locations, and organizations from the text.
* **Multi-layered Ranking:** Articles are scored based on multiple factors, including thematic relevance, frequency, NER entity importance, and source reputation.
* **AI-Powered Scoring and Content Generation:**
    * The top-ranked articles are sent to OpenAI (GPT-4o/4.1) for additional scoring (importance, urgency, sentiment).
    * Based on the highest-ranking articles, new, summarized analytical texts are generated in both Armenian and Russian.
* **Automated Publishing:** The generated content is published to two separate Telegram channels according to urgency and other predefined rules.
* **Robust Database:** The system uses a PostgreSQL database via the SQLAlchemy ORM, which ensures high performance, scalability, and data integrity through well-defined relationships (Foreign Keys).

## **System Architecture and Workflow**

The system operates as a continuous cycle using several parallel threads.

1.  **Collection Stage (`Collector`):**
    * The main loop in `main.py` calls `fetch_articles()` to get articles from the API.
    * `filter_new_articles()` filters for new articles by comparing them against the `content` table.
    * New articles are saved to the `content` table.

2.  **Processing Stage (`Collector`):**
    * `chunk_articles_and_store()` splits the article texts into chunks and saves them to the `embeddings` table.
    * `embed_chunks()` calculates the vector embeddings and updates the `embeddings` table.
    * `run_ner_on_articles()` performs NER analysis, saves the results to the `ner_results` table, and adds new entities to the `entities` table.

3.  **Analysis and Ranking Stage (`Ranker`):**
    * Average embeddings are calculated, and the thematic and frequency classifiers update the `parameters` table.
    * `rank_news()`, based on all factors, calculates a final score and populates the `ranks` table.
    * The logic from `top25.py` selects the best, non-similar candidates, populates the `top` table, and sends them to OpenAI for AI-based scoring.

4.  **Content Generation Stage (`Composer`):**
    * `get_next_unprocessed_top_id()` selects the highest-scoring but not-yet-processed article from the `top` table.
    * `prompt_gen_request` and `prompt_gen_request_ru` functions prepare a prompt for OpenAI by gathering the main article and context from similar articles.
    * `generate_content_with_openai` and `generate_content_with_openai_ru` receive the generated text.
    * `save_processed` and `save_processed_ru` save the final result in the `processed` table.

5.  **Publishing Stage (`Spreader`):**
    * The `spreader_block`, running in a separate thread, uses the `select_to_publish()` function to choose the best candidate for publication based on urgency and other rules.
    * `publishing_cycle` prepares and sends the message to the corresponding Telegram channel using the `publish_to_telegram` function.

## **Technology Stack**

* **Language:** Python 3.10+
* **Database:** PostgreSQL
* **ORM:** SQLAlchemy
* **AI/ML:**
    * `sentence-transformers` (using the `Metric-AI/armenian-text-embeddings-1` model)
    * `transformers` (using the `daviddallakyan2005/armenian-ner` model)
    * OpenAI API (`gpt-4o`, `gpt-4.1`)
* **Core Libraries:** `psycopg2-binary`, `numpy`, `requests`, `python-dotenv`, `python-telegram-bot`, `threading`.

## **Setup and Installation**

### **1. Prerequisites**

* Python 3.10+
* A running PostgreSQL server (local or remote)

### **2. Installation Steps**

1.  **Clone the repository:**
    ```bash
    git clone [your-repository-url]
    cd [your-repository-name]
    ```

2.  **Create a virtual environment and activate it:**
    ```bash
    python -m venv .venv
    # Windows
    .\.venv\Scripts\activate
    # macOS/Linux
    source .venv/bin/activate
    ```

3.  **Create a PostgreSQL database:**
    * Using pgAdmin or another tool, create a new, empty database (e.g., `Dpir_database`).
    * Ensure you have a user with the necessary privileges for this database.

4.  **Install the required libraries:**
    Create a `requirements.txt` file with the following content and run the command `pip install -r requirements.txt`.

    ```
    # requirements.txt
    sqlalchemy
    psycopg2-binary
    requests
    python-dotenv
    numpy
    sentence-transformers
    transformers
    torch
    python-telegram-bot
    openai
    ```

5.  **Configure environment variables:**
    Create a `.env` file by copying `.env.example` (if it exists) or by creating a new file. Fill in the required values.

    ```
    # .env
    # API Keys
    TOKEN_APP_KEY="your_secret_api_key_for_fetching_articles"
    OPENAI_API_KEY="your_openai_api_key"

    # Telegram Tokens
    TELEGRAM_BOT_TOKEN="your_armenian_channel_bot_token"
    TELEGRAM_BOT_TOKEN_RU="your_russian_channel_bot_token"

    # PostgreSQL Connection Details
    DB_USER="postgres"
    DB_PASSWORD="your_postgres_password"
    DB_HOST="localhost"
    DB_PORT="5432"
    DB_NAME="Dpir_database"
    ```

6.  **Create the tables in the database:**
    * Take the content of your `full_schema_dump.sql` file.
    * Using pgAdmin's Query Tool, execute that SQL script on your newly created empty database to create all tables and relationships.

### **3. Running the Application**

After ensuring everything is configured correctly, run the main script.

```bash
python main.py
```

You will begin to see logs indicating the various stages of the system's operation.

### **Project Structure**

/
├── collector/          # Modules for article collection, processing, embedding, and NER
│   ├── get_api.py
│   ├── chunker.py
│   ├── embedding.py
│   └── ner.py
│   └── utils.py
├── ranker/             # Modules for ranking algorithms
│   ├── frequency_classifier.py
│   ├── thematic_classifier.py
│   ├── ranking.py
│   ├── top25.py
│   └── ner_importance.py
├── composer/           # Modules for AI-powered content generation
│   ├── composing.py
│   ├── composing_ru.py
│   └── selector.py
├── spreader/           # Modules for publishing to Telegram
│   ├── publishing.py
│   ├── selector.py
│   └── telegram_message.py
├── db.py               # SQLAlchemy configuration and all model definitions
├── main.py             # Application entry point that runs the main cycle
├── .env                # (Must be created) File for secret keys and configurations
└── README.md           # This file


# **Հայերեն**

## AI-Powered News Pipeline - Նորությունների հավաքագրման և բովանդակության ստեղծման համակարգ
Սա բազմաթրեդային Python հավելված է, որը նախատեսված է հայկական լրատվական աղբյուրներից նորությունների ավտոմատ հավաքագրման, մշակման, վերլուծության, վարկանիշավորման և դրանց հիման վրա եզակի բովանդակության (հայերեն և ռուսերեն) գեներացման համար՝ հետագայում Telegram ալիքներում հրապարակելու նպատակով։

## Հիմնական հնարավորություններ
###Ավտոմատ հավաքագրում: Պարբերաբար ստանում է նոր հոդվածներ տարբեր լրատվական կայքերից՝ արտաքին API-ի միջոցով։

Խելացի մշակում:

Տեքստը բաժանում է տրամաբանական մասերի (chunks)։

Յուրաքանչյուր մասի համար ստեղծում է վեկտորային ներկայացում (embedding)՝ sentence-transformers-ի միջոցով։

Կատարում է Անվանական էակների ճանաչում (Named Entity Recognition - NER)՝ տեքստից առանցքային անձանց, տեղանունները և կազմակերպությունները դուրս բերելու համար։

Բազմաշերտ վարկանիշավորում: Հոդվածները գնահատվում են մի քանի գործոնների հիման վրա՝ թեմատիկ համապատասխանություն, հաճախականություն, NER-երի կարևորություն, աղբյուրի հեղինակություն։

AI-ի միջոցով գնահատում և բովանդակության ստեղծում:

Լավագույն հոդվածներն ուղարկվում են OpenAI-ին (GPT-4o/4.1)՝ լրացուցիչ գնահատման (կարևորություն, հրատապություն, տրամադրություն)։

Ամենաբարձր վարկանիշ ունեցող նյութերի հիման վրա ստեղծվում են նոր, համառոտագրված վերլուծական տեքստեր՝ հայերեն և ռուսերեն լեզուներով։

Ավտոմատ հրապարակում: Գեներացված բովանդակությունը, ըստ հրատապության և այլ կանոնների, հրապարակվում է երկու առանձին Telegram ալիքներում։

Հզոր տվյալների բազա: Համակարգն օգտագործում է PostgreSQL տվյալների բազա՝ SQLAlchemy ORM-ի միջոցով, որն ապահովում է բարձր արտադրողականություն, մասշտաբայնություն և տվյալների ամբողջականություն՝ շնորհիվ հստակ սահմանված կապերի (Foreign Keys)։

## Համակարգի ճարտարապետություն և աշխատանքի հոսք
Համակարգն աշխատում է որպես անընդհատ ցիկլ՝ մի քանի զուգահեռ թրեդների միջոցով։

Հավաքագրման փուլ (Collector):

main.py-ի հիմնական ցիկլը կանչում է fetch_articles()՝ API-ից հոդվածներ ստանալու համար։

filter_new_articles()-ը զտում է միայն նոր հոդվածները՝ համեմատելով դրանք content աղյուսակի հետ։

Նոր հոդվածները պահպանվում են content աղյուսակում։

Մշակման փուլ (Collector):

chunk_articles_and_store()-ը բաժանում է հոդվածների տեքստերը մասերի և պահպանում embeddings աղյուսակում։

embed_chunks()-ը հաշվարկում է վեկտորային embedding-ները և թարմացնում embeddings աղյուսակը։

run_ner_on_articles()-ը կատարում է NER վերլուծություն, պահպանում արդյունքները ner_results աղյուսակում և ավելացնում նոր էնթիթիները entities աղյուսակում։

Վերլուծության և վարկանիշավորման փուլ (Ranker):

Հաշվարկվում են միջին embedding-ները, թեմատիկ և հաճախականության դասակարգիչները թարմացնում են parameters աղյուսակը։

rank_news()-ը, հիմնվելով բոլոր գործոնների վրա, հաշվարկում է վերջնական գնահատականը և լրացնում ranks աղյուսակը։

top25.py-ի տրամաբանությունը ընտրում է լավագույն, իրար ոչ նման թեկնածուներին, լրացնում top աղյուսակը և ուղարկում OpenAI-ին՝ AI-ի կողմից գնահատման համար։

Բովանդակության ստեղծման փուլ (Composer):

get_next_unprocessed_top_id()-ը top աղյուսակից ընտրում է ամենաբարձր վարկանիշով, բայց դեռ չմշակված հոդվածը։

prompt_gen_request և prompt_gen_request_ru ֆունկցիաները, հավաքելով հիմնական նյութը և նմանատիպ նյութերից կոնտեքստ, պատրաստում են հարցում (prompt) OpenAI-ի համար։

generate_content_with_openai և generate_content_with_openai_ru ֆունկցիաները ստանում են գեներացված տեքստը։

save_processed և save_processed_ru ֆունկցիաները պահպանում են վերջնական արդյունքը processed աղյուսակում։

Հրապարակման փուլ (Spreader):

Առանձին թրեդով աշխատող spreader_block-ը select_to_publish() ֆունկցիայի միջոցով ընտրում է հրապարակման ենթակա լավագույն թեկնածուին՝ հիմնվելով հրատապության և այլ կանոնների վրա։

publishing_cycle-ը նախապատրաստում և publish_to_telegram ֆունկցիայի միջոցով ուղարկում է հաղորդագրությունը համապատասխան Telegram ալիք։

## Տեխնոլոգիական բազա (Tech Stack)
Լեզու: Python 3.10+

Տվյալների բազա: PostgreSQL

ORM: SQLAlchemy

AI/ML:

sentence-transformers (Metric-AI/armenian-text-embeddings-1 մոդել)

transformers (daviddallakyan2005/armenian-ner մոդել)

OpenAI API (gpt-4o, gpt-4.1)

Հիմնական գրադարաններ: psycopg2-binary, numpy, requests, python-dotenv, python-telegram-bot, threading։

## Տեղադրում և գործարկում
1. Նախապայմաններ
Python 3.10+

PostgreSQL սերվեր (լոկալ կամ հեռակա)

2. Տեղադրման քայլեր
Կլոնավորեք ռեպոզիտորիան:

Bash

git clone [your-repository-url]
cd [your-repository-name]
Ստեղծեք վիրտուալ միջավայր և ակտիվացրեք այն:

Bash

python -m venv .venv
# Windows
.\.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
Ստեղծեք PostgreSQL տվյալների բազա:

pgAdmin-ի կամ այլ գործիքի միջոցով ստեղծեք նոր, դատարկ տվյալների բազա (օրինակ՝ Dpir_database)։

Համոզվեք, որ ունեք օգտատեր՝ համապատասխան իրավունքներով։

Տեղադրեք անհրաժեշտ գրադարանները:
Ստեղծեք requirements.txt ֆայլ հետևյալ պարունակությամբ և գործարկեք pip install -r requirements.txt հրամանը։

# requirements.txt
sqlalchemy
psycopg2-binary
requests
python-dotenv
numpy
sentence-transformers
transformers
torch
python-telegram-bot
openai
Կարգավորեք միջավայրի փոփոխականները:
Ստեղծեք .env ֆայլ՝ պատճենելով .env.example-ը (եթե այն կա) կամ ստեղծելով նորը։ Լրացրեք անհրաժեშտ արժեքները։

# .env
# API-ի բանալիներ
TOKEN_APP_KEY="your_secret_api_key_for_fetching_articles"
OPENAI_API_KEY="your_openai_api_key"

# Telegram-ի բանալիներ
TELEGRAM_BOT_TOKEN="your_armenian_channel_bot_token"
TELEGRAM_BOT_TOKEN_RU="your_russian_channel_bot_token"

# PostgreSQL-ի միացման տվյալներ
DB_USER="postgres"
DB_PASSWORD="your_postgres_password"
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="Dpir_database"
Ստեղծեք աղյուսակները բազայում:

Վերցրեք ձեր full_schema_dump.sql ֆայլի պարունակությունը։

pgAdmin-ի Query Tool-ի միջոցով գործարկեք այդ SQL սկրիպտը ձեր ստեղծած դատարկ բազայի վրա՝ բոլոր աղյուսակները և կապերը ստեղծելու համար։

3. Հավելվածի գործարկում
Համոզվելուց հետո, որ ամեն ինչ ճիշտ է կարգավորված, գործարկեք հիմնական սկրիպտը։

Bash

python main.py
Դուք կսկսեք տեսնել լոգեր, որոնք ցույց են տալիս համակարգի աշխատանքի տարբեր փուլերը։

Նախագծի կառուցվածք
/
├── collector/          # Հոդվածների հավաքագրման, մշակման, embedding-ի և NER-ի մոդուլներ
│   ├── get_api.py
│   ├── chunker.py
│   ├── embedding.py
│   └── ner.py
│   └── utils.py
├── ranker/             # Վարկանիշավորման ալգորիթմների մոդուլներ
│   ├── frequency_classifier.py
│   ├── thematic_classifier.py
│   ├── ranking.py
│   ├── top25.py
│   └── ner_importance.py
├── composer/           # AI-ի միջոցով բովանդակության գեներացման մոդուլներ
│   ├── composing.py
│   ├── composing_ru.py
│   └── selector.py
├── spreader/           # Telegram-ում հրապարակման մոդուլներ
│   ├── publishing.py
│   ├── selector.py
│   └── telegram_message.py
├── db.py               # SQLAlchemy-ի կարգավորումներ և բոլոր մոդելների սահմանում
├── main.py             # Հավելվածի մուտքի կետ, որը գործարկում է հիմնական ցիկլը
├── .env                # (Պետք է ստեղծվի) Գաղտնի բանալիների և կարգավորումների ֆայլ
└── README.md           # Այս ֆայլը