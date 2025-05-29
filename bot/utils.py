import codecs
import json
import os

def load_answers(filename='bot_answers.json'):
    """
    Загружает вычисленные ответы про свободные аудитории из JSON-файла.
    :param filename: имя файла с ответами
    :return: словарь с ответами
    """
    shared_dir = os.path.join(os.path.dirname(__file__), 'shared')
    filepath = os.path.join(shared_dir, filename)
    with codecs.open(filepath, 'r', encoding='utf-8') as file:
        return json.load(file)
