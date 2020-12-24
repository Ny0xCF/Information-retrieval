from elasticsearch import Elasticsearch
from beautifultable import BeautifulTable
from wiki_ru_wordnet import WikiWordnet
import time
import json
import scrapy_parse


class Robot:
    def __init__(self):
        self.es = Elasticsearch()
        self.ww = WikiWordnet()
        self.json_path = scrapy_parse.start_parse()
        self.index_name = 'news'

    def create_index(self):
        self.es.indices.create(
            index=self.index_name,
            body={
                'settings': {
                    'number_of_shards': 1,
                    'number_of_replicas': 0,
                    'analysis': {
                        'filter': {
                            'ru_stop': {
                                'type': 'stop',
                                'stopwords': '_russian_'
                            }
                        },
                        'analyzer': {
                            'default': {
                                'char_filter': ['html_strip'],
                                'tokenizer': 'standard',
                                'filter': ['lowercase', 'ru_stop']
                            }
                        }
                    }
                }
            },
            ignore=400
        )

    def add_to_index(self):
        with open(self.json_path, 'r') as input_stream:
            data = json.loads(input_stream.read())
            k = 1
            for item in data:
                self.es.index(index=self.index_name, id=k, body=item)
                time.sleep(0.2)
                k += 1

    def add_synonyms(self, query):
        tmp_list = list()
        result_tokens = self.es.indices.analyze(index=self.index_name, body={
            'analyzer': 'default',
            'text': [query]
        })
        for token in result_tokens['tokens']:
            tmp_list.append(token['token'])
            syn_sets = self.ww.get_synsets(token['token'])
            if syn_sets:
                for synonym in syn_sets[0].get_words():
                    word = synonym.lemma()
                    if tmp_list.count(word) == 0:
                        tmp_list.append(word)
        return ' '.join(tmp_list)

    def find_by(self, find_option, query):
        fields_list = ['title']
        if find_option == '2':
            fields_list = ['body']
        elif find_option == '3':
            fields_list = ['title', 'body']

        query_body = {
            'query': {
                'bool': {
                    'should': [
                        {
                            'multi_match': {
                                'query': query,
                                'analyzer': 'default',
                                'fields': fields_list,
                            }
                        },
                    ],
                }
            }
        }
        return self.es.search(index='news', body=query_body)

    def delete_indices(self):
        for key in self.es.indices.get_alias().keys():
            self.es.indices.delete(index=key)


if __name__ == '__main__':
    print('411 группа. Шепелев Денис')
    print('www.saratov24.tv/newstags/zhkkh/ - "Саратов 24", раздел "ЖКХ"')

    print('\nПодготавливаюсь к построению индекса...')

    my_robot = Robot()
    my_robot.create_index()
    my_robot.add_to_index()

    option = '-1'
    while option != '0':
        option = input('\nВыполнить поиск по:'
                       '\n1 - заголовку'
                       '\n2 - основному тексту'
                       '\n3 - заголовку и основному тексту'
                       '\n0 - завершить работу'
                       '\nВаш выбор: ')
        if option == '0':
            my_robot.delete_indices()
            exit(0)
        elif option in ['1', '2', '3']:
            new_query = my_robot.add_synonyms(input('\nВведите фразу или предложение: '))
            print(f'\nВыполняю поиск по словам: {new_query}')
            result = my_robot.find_by(option, new_query)

            hits_len = len(result['hits']['hits'])
            print('Всего совпадений:', hits_len)
            if hits_len > 0:
                table = BeautifulTable(maxwidth=1000)
                table.set_style(BeautifulTable.STYLE_BOX)

                for i in range(hits_len):
                    table.rows.append([i + 1,
                                       result['hits']['hits'][i]['_score'],
                                       result['hits']['hits'][i]['_source']['url']])
                table.columns.header = ["№", "Score", "URL"]
                print(table)
        else:
            print('\nОшибка: нераспознанный символ!')
