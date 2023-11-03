import telebot
import requests
from bs4 import BeautifulSoup


# токен Телеграм бота - введите токен Вашего бота
TOKEN = 'INPUT YOUR TOKEN'
# подключение к боту
bot = telebot.TeleBot(TOKEN)
# Текст для модулей в разработке
under_construction_text = 'Модуль находится в разработке!'


# Класс для создания кнопок меню /start
class Button:
    # Создаём словарь кнопок
    start_buttons_dictionary = {
        '1': {'button_description': 'Достопримечательности', 'url': 'https://www.citywalls.ru/sights.html'},
        '2': {'button_description': 'Улицы', 'url': 'https://www.citywalls.ru/street_index.html'},
        '3': {'button_description': 'Архитектурные стили', 'url': 'https://www.citywalls.ru/select_archstyle.html'},
        '4': {'button_description': 'Исторические периоды в архитектуре',
              'url': 'https://www.citywalls.ru/select_year.html'},
        '5': {'button_description': 'Архитекторы', 'url': 'https://www.citywalls.ru/architect_index.html'},
        '6': {'button_description': 'Категории', 'url': 'None'}}

    class_button_instances = []
    class_button_list = []

    def __init__(self, number, name, url):
        self.number = number
        self.name = name
        self.url = url
        self.button = telebot.types.InlineKeyboardButton(name, callback_data=f'С_{number}')
        self.soup = None
        self.__class__.class_button_instances.append(self)
        self.__class__.class_button_list.append(self.button)
        self.db = None
        self.markup = None

    def __str__(self):
        return f'\n{self.number} - {self.name} - {self.url} - {self.button}'


# Функция создания кнопок из словаря start_buttons_dictionary
def create_button_items() -> list:
    return [Button(
        str(x + 1), Button.start_buttons_dictionary[str(x + 1)]['button_description'],
        Button.start_buttons_dictionary[str(x + 1)]['url'],
    ) for x in range(len(Button.start_buttons_dictionary))]


# Запуск функции создания кнопок
create_button_items()


# Функция создания разметки кнопок меню /start
def gen_markup():
    # создаём изначальную разметку кнопок
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    # Добавляем кнопки в разметку из классового списка кнопок
    markup.add(*Button.class_button_list)

    return markup


'''
Достопримечательности
'''
# Создём глобальную переменную - порядковый номер ссылки на сайт достопримечательности
sight_page = 0


# Функия создания словаря с обработанными извлечёнными данными
def sights(url_first):
    # Вычисляем последний(правый) "/" знак в веб ссылке, чтобы вычислить имя домена
    url_end = url_first.rfind('/')
    # Вычисляем имя домена
    domain = url_first[0:url_end]
    # Вычисляем путь страницы
    url_suffix = url_first[url_end:]
    # Составляем url
    url = domain + url_suffix
    # Запрашиваем данные с url
    response = requests.get(url)
    # Записываем извлечённые данные в класс
    Button.class_button_instances[0].soup = BeautifulSoup(response.text, 'html.parser')
    # Присуждаем записанные переменные в класс переменной
    soup = Button.class_button_instances[0].soup
    # парсим страницу на предмет адресных путей пагинаций
    sights_pages_index = soup.select('div[class="cssPager"] a')

    # создаём список с адресными путями пагинаций добавляемых к домену
    sights_pages_list = [url_suffix]
    # Циклом проходим по результатам парсинга и записваем в список все адресные пути пагинаций
    for page in sights_pages_index:
        # находим ссылку
        sights_index_href = page.get('href')
        # если ссылки нет в списке - заносим
        if sights_index_href not in sights_pages_list:
            sights_pages_list.append(sights_index_href)

    # Создаём словарь
    sights_db = {}
    # Создаём словарь для адресов (отдельный, так как вынуть адреса сразу в общий не удаётся)
    address_db = {}
    # Циклом проходим по результатам парсинга
    for page in sights_pages_list:
        # Создаём ссылку для следующей страницы сайта
        interim_url = domain + page
        # Запрашиваем данные с созданной ссылки
        interim_response = requests.get(interim_url)
        # Записываем извлечённые данные в переменную
        soup = BeautifulSoup(interim_response.text, 'html.parser')

        # достаём из soup строки с достопримечательностями
        sights_index = soup.select('a[title]')
        # достаём из soup строки с адресом достопримечательности
        sights_address_index = soup.select('[class="address"]', href=True)
        # Циклом проходим по данным с адресами достопримечательностей
        for address in sights_address_index:
            # Обрезаем пробелы в адресе
            address_name = address.get_text().strip()
            # Извлекаем ссылку на страницу
            address_index_href = address.contents[0].get('href')
            # Записываем в словарь для адресов: ключ - ссылка, занчение - адрес
            address_db[address_index_href] = address_name

        # Циклом идём по извлечённым строкам с достопримечательностями
        for sight in sights_index:
            # идентифицируем текст
            sights_index_title = sight.get('title').strip()
            # идентифицируем гиперссылку
            sights_index_href = sight.get('href')
            # идентифицируем ссылку на фото
            # индекс начачла ссылки
            sight_photo_url_first_char_index = str(sight).rfind('url(')
            # индекс окончания ссылки
            sight_photo_url_last_char_index = str(sight).rfind(')"></div>')
            sight_photo_url = str(sight)[sight_photo_url_first_char_index + 5:sight_photo_url_last_char_index - 1]
            sight_photo_url_crop = sight_photo_url.rfind('?')
            sight_photo_url = sight_photo_url[0:sight_photo_url_crop]
            # Если ссылка содержит 'citywalls.ru/house'
            if 'citywalls.ru/house' in sights_index_href:
                # Если есть уже намиенование достопримечательности среди ключей словаря sights_db
                if sights_index_title in list(sights_db.keys()):
                    # Но значение [ссылка, ссылка на фото, адрес] не совпадает,
                    if [sights_index_href, sight_photo_url, address_db[sights_index_href]] not in sights_db[
                        sights_index_title]:
                        # то добавляем новое значение [ссылка, ссылка на фото, адрес]
                        sights_db[sights_index_title] += [
                            [sights_index_href, sight_photo_url, address_db[sights_index_href]]]
                # Иначе создаёи новую запись в словаре
                else:
                    sights_db[sights_index_title] = [
                        [sights_index_href, sight_photo_url, address_db[sights_index_href]]]

    # Записываем в класс словарь с данными
    Button.class_button_instances[0].db = sights_db

    return


# Функция создания разметки кнопок
def sights_buttons(sights_db):
    # Создаём разматку кнопок
    sights_buttons_markup = telebot.types.InlineKeyboardMarkup()
    # будем оперировать глобальной переменной порядкового номера ссылки достопримечательности
    global sight_page

    # Вычисляем общее количество уникальных записей [ссылка, ссылка на фото, адрес]
    sight_pages_count = sum([len(sights_db[x]) for x in sights_db if isinstance(sights_db[x], list)])

    # Создаём переменную "влево" с условием, если значение порядкового номера ссылки достопримечательности не равно нулю,
    # то оно уменьшается на единицу, в противном случае берётся порядкый номер последней записи
    # нумерация в списке начинаеися с нуля, соотвественно порядкый номер последней записи  =  общее количесво записей
    # минус единица
    left = sight_page - 1 if sight_page != 0 else sight_pages_count - 1
    # Создаём переменную "вправо" с условием, если значение порядкового номера ссылки достопримечательности не равно
    # порядковуму номеру последней записи, то оно увеличивается на единицу, в противном случае ноль
    right = sight_page + 1 if sight_page != sight_pages_count - 1 else 0

    # Создаём кнопку "влево" с возвращаемой (при нажатии) информацией: "to " + значение переменной left
    left_button = telebot.types.InlineKeyboardButton("⟸", callback_data=f'to {left}')
    # Создаём информационную кнопку с указанием порядкового номера текущей достопримечательности
    # и общее количество всех достопримечательностей, с возвращаемой (при нажатии) информацией: "_"
    page_button = telebot.types.InlineKeyboardButton(f"{str(sight_page + 1)}/{str(sight_pages_count)}",
                                                     callback_data='_')
    # Создаём кнопку "вправо" с возвращаемой (при нажатии) информацией: "to " + значение переменной right
    right_button = telebot.types.InlineKeyboardButton("⟹", callback_data=f'to {right}')
    # добавляем созданные кнопки в разметку
    sights_buttons_markup.add(left_button, page_button, right_button)

    # Записываем в класс разметку кнопок
    Button.class_button_instances[0].markup = sights_buttons_markup

    return


'''
Улицы
'''


def streets(url):
    response = requests.get(url)

    Button.class_button_instances[1].soup = BeautifulSoup(response.text, 'html.parser')
    soup = Button.class_button_instances[1].soup

    streets_index = soup.find_all('a', onmouseout="return index_hide_count()")

    # Создаём словарь
    streets_db = {}

    for street in streets_index:
        # идентифицируем текст
        streets_index_text = street.text
        # идентифицируем гиперссылку
        streets_index_href = street.get('href')
        # идентифицируем количество спроектированых зданий
        street_projects = int(
            street.get('onmouseover')[street.get('onmouseover').rfind(' ') + 1:len(street.get('onmouseover')) - 1])
        # идентифицируем первую букву архитектора
        street_first_letter = streets_index_text[0]
        # проверяем есть ли уже ключ в словаре architect_db идентичный первой букве архитектора
        if street_first_letter in streets_db.keys():
            # добавляем значение к имеющемуся ключу
            streets_db[street_first_letter] += [[streets_index_text, streets_index_href, street_projects]]
        else:
            # создаём новую пару ключ-значение
            streets_db[street_first_letter] = [[streets_index_text, streets_index_href, street_projects]]

    Button.class_button_instances[1].db = streets_db

    return


def streets_buttons(streets_db):
    streets_buttons_markup = telebot.types.InlineKeyboardMarkup(row_width=8)

    streets_buttons_list = []
    for key, value in streets_db.items():
        streets_buttons_list.append(telebot.types.InlineKeyboardButton(key, callback_data=f'У_{key}'))

    streets_buttons_markup.add(*streets_buttons_list)

    Button.class_button_instances[1].markup = streets_buttons_markup

    return


'''
Архитектурные стили
'''


def styles(url):
    response = requests.get(url)

    Button.class_button_instances[2].soup = BeautifulSoup(response.text, 'html.parser')
    soup = Button.class_button_instances[2].soup

    styles_index = soup.find('div', class_="m_content3").find_all('a')

    # Создаём словарь
    styles_db = {}

    for i in styles_index:
        # идентифицируем текст
        styles_index_text = i.text
        # идентифицируем гиперссылку
        styles_index_href = i.get('href')
        # Записываем в словарь
        if styles_index_text in styles_db.keys():
            # добавляем значение к имеющемуся ключу
            styles_db[styles_index_text] += styles_index_href
        else:
            # создаём новую пару ключ-значение
            styles_db[styles_index_text] = styles_index_href

    Button.class_button_instances[2].db = styles_db

    return


def styles_buttons(styles_db):
    styles_buttons_markup = telebot.types.InlineKeyboardMarkup(row_width=3)

    styles_buttons_list = []
    for key, value in styles_db.items():
        styles_buttons_list.append(telebot.types.InlineKeyboardButton(key, callback_data=f'S_{key}'))

    styles_buttons_markup.add(*styles_buttons_list)

    Button.class_button_instances[2].markup = styles_buttons_markup

    return


'''
Исторические периоды
'''


def periods(url):
    response = requests.get(url)

    Button.class_button_instances[3].soup = BeautifulSoup(response.text, 'html.parser')
    soup = Button.class_button_instances[3].soup

    period_index = soup.find('ul', class_="cssSelectYear").find_all('a')

    # Создаём словарь
    period_db = {}

    for i in period_index:
        # идентифицируем текст
        period_index_text = i.text
        # идентифицируем гиперссылку
        period_index_href = i.get('href')
        # Для определения диапазона лет из гиперссылки (пример: https://www.citywalls.ru/search-year1700_1734.html)
        # Определяем индекс начала
        my_year = period_index_href.find('year') + 4
        # И индекс окончания
        link_end = period_index_href.find('.html')
        # идентифицируем диапазон лет с заменой нижнего подчёркивания на тире
        period_years = period_index_href[my_year:link_end].replace('_', '-')
        # из диапазона лет высчитываем век
        century = int(period_years[0:2]) + 1
        # Записываем в словарь
        if century in period_db.keys():
            # добавляем значение к имеющемуся ключу
            period_db[century] += [[period_index_text, period_years, period_index_href]]
        else:
            # создаём новую пару ключ-значение
            period_db[century] = [[period_index_text, period_years, period_index_href]]

    Button.class_button_instances[3].db = period_db

    return


def period_buttons(period_db):
    period_buttons_markup = telebot.types.InlineKeyboardMarkup(row_width=2)

    period_buttons_list = []
    for key, value in period_db.items():
        period_buttons_list.append(telebot.types.InlineKeyboardButton(key, callback_data=f'П_{key}'))

    period_buttons_markup.add(*period_buttons_list)

    Button.class_button_instances[3].markup = period_buttons_markup

    return


'''
Архитекторы
'''


def architects(url):
    response = requests.get(url)

    Button.class_button_instances[4].soup = BeautifulSoup(response.text, 'html.parser')
    soup = Button.class_button_instances[4].soup

    # создаём выборку с необходимыми данными
    architect_a = soup.find_all('a', onmouseout="return index_hide_count()")

    # pprint.pprint(architect_a)

    # Создаём словарь
    architect_db = {}

    # Циклом проходим по выборке
    for architect in architect_a:
        # идентифицируем текст
        architect_text = architect.text
        # идентифицируем гиперссылку
        architect_href = architect.get('href')
        # идентифицируем количество спроектированых зданий
        architect_projects = int(architect.get('onmouseover')[
                                 architect.get('onmouseover').rfind(' ') + 1:len(architect.get('onmouseover')) - 1])
        # идентифицируем первую букву архитектора
        architect_first_letter = architect_text[0]
        # проверяем есть ли уже ключ в словаре architect_db идентичный первой букве архитектора
        if architect_first_letter in architect_db.keys():
            # добавляем значение к имеющемуся ключу
            architect_db[architect_first_letter] += [[architect_text, architect_href, architect_projects]]
        else:
            # создаём новую пару ключ-значение
            architect_db[architect_first_letter] = [[architect_text, architect_href, architect_projects]]

    Button.class_button_instances[4].db = architect_db

    return


def architect_buttons(architect_db):
    architect_buttons_markup = telebot.types.InlineKeyboardMarkup(row_width=8)

    architect_buttons_list = []
    for key, value in architect_db.items():
        architect_buttons_list.append(telebot.types.InlineKeyboardButton(key, callback_data=f'А_{key}'))

    architect_buttons_markup.add(*architect_buttons_list)

    Button.class_button_instances[4].markup = architect_buttons_markup

    return


'''
Категории
'''


def categories(url):
    response = requests.get(url)

    Button.class_button_instances[5].soup = BeautifulSoup(response.text, 'html.parser')
    soup = Button.class_button_instances[5].soup

    categories_index = soup.find('ul', class_="cssSelectYear").find_all('a')

    # Создаём словарь
    categories_db = {}

    Button.class_button_instances[5].db = categories_db

    return


def categories_buttons(categories_db):
    categories_buttons_markup = telebot.types.InlineKeyboardMarkup(row_width=2)

    # categories_buttons_list = []
    # for key, value in categories_db.items():
    # 	categories_buttons_list.append(telebot.types.InlineKeyboardButton(key, callback_data=f'П_{key}'))
    #
    # categories_buttons_markup.add(*categories_buttons_list)

    Button.class_button_instances[5].markup = categories_buttons_markup

    return


'''
Bot Handlers
'''


@bot.message_handler(commands=['start'])
def send_welcome(message):
    sender_username = message.from_user.username
    bot.reply_to(message, f"Добро пожаловать, {sender_username}, в мир Санкт-Петербурга!", reply_markup=gen_markup())


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    global sight_page
    global under_construction_text
    if call.message:
        if call.data[0] == "С":
            button_index = Button.class_button_instances[int(call.data[-1]) - 1]
            if call.data[-1] == '1':
                sight_page = 0
                sights(button_index.url)
                sights_buttons(button_index.db)
                interim_reply_markup = button_index.markup
                text = button_index.name

                sight_name = list(button_index.db)[sight_page]
                sight_link = button_index.db[list(button_index.db)[sight_page]][0][0]
                photo_path = button_index.db[list(button_index.db)[sight_page]][0][1]
                sight_address = button_index.db[list(button_index.db)[sight_page]][0][2]
                sight_description = f'_{text}_:\n\n*{sight_name}*\n\n{sight_address}\n\n{sight_link}'

                bot.send_photo(call.message.chat.id, photo=photo_path, caption=sight_description,
                               parse_mode='Markdown', reply_markup=interim_reply_markup)

            elif call.data[-1] == '2':
                streets(button_index.url)
                streets_buttons(button_index.db)
                interim_reply_markup = button_index.markup
                text = button_index.name
                bot.answer_callback_query(call.id, show_alert=True, text=text)
                bot.send_message(call.message.chat.id, f'{text} Санкт-Петербурга и пригородов\nАлфавитнй указатель:',
                                 reply_markup=interim_reply_markup)

            elif call.data[-1] == '3':
                styles(button_index.url)
                styles_buttons(button_index.db)
                interim_reply_markup = button_index.markup
                text = button_index.name
                bot.answer_callback_query(call.id, show_alert=True, text=text)
                bot.send_message(call.message.chat.id, f'{text}\nВыберите архитектурный стиль:',
                                 reply_markup=interim_reply_markup)

            elif call.data[-1] == '4':
                periods(button_index.url)
                period_buttons(button_index.db)
                interim_reply_markup = button_index.markup
                text = button_index.name
                bot.answer_callback_query(call.id, show_alert=True, text=text)
                bot.send_message(call.message.chat.id, f'{text}\nВыберите век:', reply_markup=interim_reply_markup)

            elif call.data[-1] == '5':
                architects(button_index.url)
                architect_buttons(button_index.db)
                interim_reply_markup = button_index.markup
                text = button_index.name
                bot.answer_callback_query(call.id, show_alert=True, text=text)
                bot.send_message(call.message.chat.id, f'{text}\nАлфавитнй указатель:',
                                 reply_markup=interim_reply_markup)

            elif call.data[-1] == '6':
                # categories(button_index.url)
                # categories_buttons(button_index.db)
                # interim_reply_markup = button_index.markup
                text = under_construction_text
                bot.answer_callback_query(call.id, show_alert=True, text=text)
            # bot.send_message(call.message.chat.id, f'{text}')

        elif call.data[0] == "A":
            pass
        elif 'to' in call.data:
            sight_page = int(call.data.split(' ')[1])
            button_index = Button.class_button_instances[0]
            sights_buttons(button_index.db)
            interim_reply_markup = button_index.markup
            text = button_index.name

            # Разворачиваем вложенные списки в значениях словаря в один список
            dict_values_list = [item for sublist in button_index.db.values() for item in sublist]

            # находим значение в списке значений по индексу
            interim_var = dict_values_list[sight_page]

            value_index, key_index = None, None

            for k, v in button_index.db.items():
                if interim_var in v:
                    value_index = v.index(interim_var)
                    key_index = list(button_index.db).index(k)

            sight_name = list(button_index.db)[key_index]
            sight_link = button_index.db[list(button_index.db)[key_index]][value_index][0]
            photo_path = button_index.db[list(button_index.db)[key_index]][value_index][1]
            sight_address = button_index.db[list(button_index.db)[key_index]][value_index][2]
            sight_description = f'_{text}_:\n\n*{sight_name}*\n\n{sight_address}\n\n{sight_link}'
            bot.send_photo(call.message.chat.id, photo=photo_path, caption=sight_description,
                           parse_mode='Markdown', reply_markup=interim_reply_markup)
        elif '_' == call.data:
            text = 'Информационная кнопка'
            bot.answer_callback_query(call.id, show_alert=True, text=text)
        else:
            text = under_construction_text
            bot.answer_callback_query(call.id, show_alert=True, text=text)


@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, f"Бот для знакомства с архитектурой Санкт-Петербурга посредством ресурсов портала "
                          f"https://www.citywalls.ru/!"

                          f"\n\n_Легенда:_"
                          f"\n  ✅ - _готов к использованию_"
                          f"\n  🚧 - _в разработке_"
                          f"\n\n*Список действующих команд:*"
                          f"\n\n/help - текущий раздел"
                          f"\n/start - выводит следующие разделы:"
                          f"\n   -  *Достопримечательности* - ✅"
                          f"\n   -  *Улицы* - 🚧(есть первичное меню)"
                          f"\n   -  *Архитектурные стили* - 🚧(есть первичное меню)"
                          f"\n   -  *Исторические периоды в архитектуре* - 🚧(есть первичное меню)"
                          f"\n   -  *Архитекторы* - 🚧(есть первичное меню)"
                          f"\n   -  *Категории* - 🚧",
                 parse_mode='Markdown')

# Запуск бота
bot.polling()
