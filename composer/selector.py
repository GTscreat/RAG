from db import SessionLocal, Top, Processed

def get_next_unprocessed_top_id():
    """
    Արդյունավետ կերպով գտնում է ամենաբարձր վարկանիշով չմշակված 
    հոդվածի ID-ն՝ օգտագործելով մեկ բազային հարցում։
    """
    # 'with' բլոկ՝ սեսիայի անվտանգ կառավարման համար
    with SessionLocal() as session:
        try:
            # Ենթահարցում (subquery), որը ստանում է արդեն մշակված բոլոր ID-ները։
            # Այս գործողությունը կատարվում է բազայի կողմից, ոչ թե Python-ի հիշողության մեջ։
            processed_ids_subquery = session.query(Processed.base_id)

            # Հիմնական հարցում.
            # Գտի՛ր Top աղյուսակից ամենաբարձր վարկանիշով ID-ն,
            # որը ՉԻ ԳՏՆՎՈՒՄ (NOT IN) մշակված ID-ների ցուցակում։
            result = session.query(Top.id) \
                .filter(Top.id.notin_(processed_ids_subquery)) \
                .order_by(Top.total_score.desc()) \
                .first()

            # .first()-ը վերադարձնում է կամ տվյալ (օրինակ՝ (123,)), կամ None
            return result[0] if result else None

        except Exception as e:
            print(f"❌ Սխալ՝ հաջորդ չմշակված ID-ն ստանալիս: {e}")
            return None