# Продуктовый помощник - учебный дипломный проект
Продуктовый помощник - это сайт, на котором пользователи могут публиковать рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов.
Также реализован функционал сервиса "Список покупок", позволяющий пользователям скачивать список продуктов и их количество, которое нужно купить для приготовления выбранных блюд.

## Применяемый стек:
Весь проект реализован за счет взаимодействия фронтенда, заранее подготовленного для дипломного задания на фреймворке React, и бэкенда.
Бэкенд реализует функционал REST API (регистрация пользователей, выдача токенов доступа, контроль доступа, смена паролей, подписки, списки избранного и покупок и т.д.), задействуя следующие технологии:
+ Python 3.8;
+ Django 4.0.1;
+ Django Rest Framework 3.13.1;
+ Django Filter 21.1;
+ Djoser 2.1.0;
+ PostgreSQL;
+ nginx;
+ Docker.

**Реализован функционал API, а также деплой на удаленный сервер Яндекс.Облако в Docker-контейнерах**

## Как развернуть проект на локальной машине
Рекомендуется разворачивать проект в dcoker-контейнерах. Для этого у вас должны быть установлены:
+ Docker;
+ Docker-compose.
На машине с Linux проект можно развернуть следуя шагам ниже (все команды выполнять в терминале):
1. Склонировать репозиторий, создать виртуальное окружение:
```commandline
$ git clone git@github.com:yuriynek/foodgram-project-react.git
```
2. Добавить файл **.env** с переменными среды в директорию **backend/**. Указать следующие переменные:
+ SECRET_KEY=<ваш секретный ключ Django>
+ DB_ENGINE=django.db.backends.postgresql
+ POSTGRES_DB=<ваше название БД Postgres>
+ POSTGRES_USER=<имя пользователя БД>
+ POSTGRES_PASSWORD=<пароль пользователя БД>
+ DB_HOST=db
+ DB_PORT=5432

3. Запустить docker-контейнеры через docker-compose в директории **infra/**:
```commandline
$ sudo docker-compose up -d --build
```
4. В контейнере **backend** выполнить миграции, создать суперпользователя для админки, собрать статику:
```commandline
$ sudo docker-compose exec backend python manage.py makemigrations
$ sudo docker-compose exec backend python manage.py migrate
$ sudo docker-compose exec backend python manage.py createsuperuser
$ sudo docker-compose exec backend python manage.py collectstatic
```

5. После выполненных шагов проект с админкой будет готов к работе:
* http://localhost/ - Главная страница
* http://localhost/api/ - API
* http://localhost/api/docs/ - Документация к API
* http://localhost/admin/ - админка

[Главная страница]: <http://51.250.78.82/>
[Админка]: <http://51.250.78.82/admin/>
[Документация к API]: <http://51.250.78.82/api/docs/>
