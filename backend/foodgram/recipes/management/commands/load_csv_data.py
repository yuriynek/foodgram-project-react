import csv
import os

from django.core.management.base import BaseCommand

from recipes import models

# TODO: доделать

DIR_NAME = os.path.dirname(__file__)
CSV_DATA_PATH = os.path.join(DIR_NAME, '../../../../../data/')

FILE_MODEL_DICT = {
    'ingredients.csv': models.Ingredient,
}

TABLES_FOREIGN_KEYS = {
    # EXAMPLE:
    # 'comments.csv': {
    #     'author': lambda pk: models.User.objects.get(pk=pk),
    #     'review': lambda pk: models.Review.objects.get(pk=pk)},
}

LOADING_ORDER = ['ingredients.csv']


def load_csv_through_dict_reader(
        data_path=CSV_DATA_PATH,
        file_model_dict=FILE_MODEL_DICT,
        foreign_keys_table=TABLES_FOREIGN_KEYS,
        file=None):
    with open(''.join([data_path, file]),
              encoding='UTF-8', newline='') as csv_file:
        # Считываем данные из csv в виде словаря
        reader = csv.DictReader(csv_file)
        # Формируем данные.
        # Если поле является ForeignKey,
        # то берем из связанной модели конкретный экземпляр
        # с помощью TABLES_FOREIGN_KEYS
        for row in reader:
            data = {}
            for k, v in row.items():
                if (foreign_keys_table.get(file)
                        and k in foreign_keys_table.get(file)):
                    data[k] = foreign_keys_table[file][k](int(v))
                else:
                    data[k] = v
            # записываем подготовленные данные в БД
            file_model_dict[file].objects.create(**data)


def load_csv_through_reader(
        data_path=CSV_DATA_PATH,
        file_model_dict=FILE_MODEL_DICT,
        file=None,):
    with open(''.join([data_path, file])) as f:
        reader = csv.reader(f)
        for row in reader:
            file_model_dict[file].objects.get_or_create(
                name=row[0],
                measurement_unit=row[1]
            )


class Command(BaseCommand):
    help = 'Load data from .csv file into database'

    def handle(self, *args, **options):
        """Загружаем файлы из csv в БД."""
        files = LOADING_ORDER

        #  Проходим каждый файл
        for file in files:
            try:
                load_csv_through_reader(file=file)
            except Exception as error:
                self.stdout.write('ПРОИЗОШЛА ОШИБКА:')
                self.stdout.write(error)
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'...Данные успешно загружены из файла {file}...'))
