import re

def escape_markdown_v2(text):
    """
    Escape characters for Telegram MarkdownV2.
    """
    # All MarkdownV2 special characters
    to_escape = r'([_*\[\]()~`>#+\-=|{}.!])'
    return re.sub(to_escape, r'\\\1', text)


def format_telegram_message(title, content, url):
    # Escape all special characters for MarkdownV2
    title_escaped = escape_markdown_v2(title or "")
    content_escaped = escape_markdown_v2(content or "")
    url_escaped = escape_markdown_v2(url or "")
    # channel_name = "@testingai_iprc"
    # "Ավելին" հիպերհղումը լինում է բոլդ
    more_bold_link = f"*[Ավելին]({url_escaped})*"
    message = f"*{title_escaped}*\n\n{content_escaped}\n\n{more_bold_link}"
    return message