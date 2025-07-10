# Priority of Operational Urgency
OPERATIONAL_HIGH = """
Generate content emphasizing maximum speed, minimal detail, and immediate reporting based solely on the provided information.
"""

OPERATIONAL_BALANCED = """
Generate content quickly while including essential facts and key contextual details based solely on the provided information.
"""

# Objectivity Spectrum
OBJECTIVITY_NEUTRAL = """
Provide neutral, objective, and professional reporting without any bias or evaluation, strictly based on the provided information.
"""

OBJECTIVITY_PRO_GOVERNMENT = """
Generate content clearly favoring governmental positions and perspectives based solely on the provided information.
"""

OBJECTIVITY_OPPOSITION = """
Generate content clearly favoring opposition positions and perspectives based solely on the provided information.
"""

OBJECTIVITY_OTHER_BIAS = """
Generate content explicitly supporting the perspective of a specified group, organization, or individual based solely on the provided information.
"""

OBJECTIVITY_TOPIC_ADJUSTED = """
Adjust the level of objectivity according to the nature of the topic presented in the provided information. 
Պետք է նյութը ներկայացնել Հայաստանի հետաքրքրությունների տեսանկյունից։  
""" #խմբագրել

# Priority of Topics
TOPIC_MAIN_ISSUES = """
Prioritize political, economic, security-related, and publicly significant main issues based solely on the provided information.
"""

TOPIC_INDIVIDUALS = """
Prioritize individuals, their actions, statements, and relevance based solely on the provided information.
"""

TOPIC_EVENTS = """
Focus primarily on specific events, developments, and occurrences based solely on the provided information.
"""

# Text Format
FORMAT_BRIEF = """
Summarize the provided information concisely, using one or two sentences containing only essential facts.
"""

FORMAT_SUMMARY = """
Provide a brief summary including primary information without detailed analysis or extensive background based solely on the provided information.
"""

FORMAT_DETAILED = """
Generate detailed content incorporating comprehensive facts, context, and analytical depth based solely on the provided information.
"""

# Reporting Style
STYLE_DIRECT = """
Directly present facts clearly and straightforwardly without any commentary or analysis based solely on the provided information.
"""

STYLE_REPHRASED = """
Rephrase the provided source materials and content in new, original wording without adding extra details.
"""

STYLE_EVALUATIVE = """
Include explicit assessments, evaluations, or opinions based solely on the provided information.
"""

STYLE_ANALYTICAL = """
Analyze provided information by revealing causal relationships, context, and implications.
"""

STYLE_PROPAGANDA = """
Present information aimed explicitly at persuading or influencing the audience towards a particular viewpoint based solely on the provided information.
"""

STYLE_SARCASTIC = """
Present information sarcastically or humorously to convey criticism or irony based solely on the provided information.
"""

# Language
LANGUAGE_ARMENIAN = """
Generate the provided content in Armenian.
"""

LANGUAGE_ENGLISH = """
Generate the provided content in English.
"""

LANGUAGE_RUSSIAN = """
Generate the provided content in Russian.
"""

LANGUAGE_AZERI = """
Generate the provided content in Azerbaijani.
"""

LANGUAGE_TURKISH = """
Generate the provided content in Turkish.
"""

LANGUAGE_OTHER = """
Generate the provided content in the specified language.
"""

# Media Generation
MEDIA_AUDIO = """
Convert the provided textual content into an audio message.
"""

MEDIA_REPUBLISH = """
Include and republish media content (images, videos, audio) sourced directly from external sources provided.
"""

MEDIA_GENERATE_NEW = """
Generate original media content (such as images, videos, infographics) based solely on the provided textual information.
"""

# Additional Settings
TITLE_WEBSITE_ARTICLE = """
Generate a clear, engaging, and descriptive title suitable for a website article based solely on the provided information.
"""

TITLE_TELEGRAM_CHANNEL = """
Generate a short, impactful headline suitable for Telegram channel publication consisting of only a few words based solely on the provided information.
"""

TELEGRAM_POST = """
Create a concise, engaging, and informative Telegram channel post optimized for rapid reading and audience engagement based solely on the provided information.
Return clear and concise content without any additional explanations, comments, or descriptions.
"""