import re
from urllib.parse import unquote


def format_room_name(url):
    """
    Форматирует название аудитории из URL.
    :param url: ссылка на расписание аудитории
    :return: строка с номером аудитории
    """
    room_num = re.sub(r'[+_.]', ' ', unquote(url.split('/')[-1]))
    return room_num
