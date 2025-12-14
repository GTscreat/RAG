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
    channel_name = "@newsarmaipowerd"
    # "Ավելին" հիպերհղումը լինում է բոլդ
    more_bold_link = f"*[Ավելին]({url_escaped})*"
    message = f"*{title_escaped}*\n\n{content_escaped}\n\n{more_bold_link}\n\n{channel_name}"
    return message

def format_telegram_message_ru(title, content, url):
    # Escape all special characters for MarkdownV2
    title_escaped_ru = escape_markdown_v2(title or "")
    content_escaped_ru = escape_markdown_v2(content or "")
    url_escaped_ru = escape_markdown_v2(url or "")
    channel_name_ru = "@newsrusaipowerd"
    # "Ավելին" հիպերհղումը լինում է բոլդ
    more_bold_link_ru = f"*[Подробности]({url_escaped_ru})*"
    message_ru = f"*{title_escaped_ru}*\n\n{content_escaped_ru}\n\n{more_bold_link_ru}\n\n{channel_name_ru}"
    return message_ru