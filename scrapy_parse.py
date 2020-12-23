import os


def start_parse():
    json_path = open('json_path_settings.txt').read()
    # # Очистка файла от результатов предыдущего парсинга
    # with open(json_path, 'r+') as input_stream:
    #     input_stream.truncate(0)
    #
    # # Запуск паука из терминала
    # os.system("scrapy crawl saratov24 -o output.json")
    return json_path


if __name__ == '__main__':
    pass
