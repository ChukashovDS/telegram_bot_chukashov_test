from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, LabeledPrice
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Text
import sqlite3 as sq
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import wikipedia
import requests
from bs4 import BeautifulSoup as BS
from aiogram.types.message import ContentTypes
from datetime import date, time, datetime, timedelta
import asyncio

YOOTOKEN = '381764678:TEST:37619'
wikipedia.set_lang("ru")
TOKEN = '5143782601:AAFIIz_-6s409uza66NRObmWb47kNBw_8E0'
# Для машины состояний
storage = MemoryStorage()
# -----------------------
# Паралельный процесс, который рабоает вместе с ботом
loop = asyncio.get_event_loop()

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=storage, loop = loop)


# Функция запуска бота
async def on_startup(_):
    print('Бот вышел в онлайн')
    sql_start()
    sql_start_zak()
    dp.loop.create_task(chack_date())




# База данных
# ------------------------------------------------
# Создание и Запись
# База данных где хранится МЕНЮ
def sql_start():
    global base, cur
    base = sq.connect('pizza_cool.db')
    cur = base.cursor()
    if base:
        print('Data base connected OK!')
    base.execute('CREATE TABLE IF NOT EXISTS menu(img TEXT, name TEXT PRIMARY KEY, description TEXT, price TEXT)')
    base.commit()
    base.execute('CREATE TABLE IF NOT EXISTS roli(img TEXT, name TEXT PRIMARY KEY, description TEXT, price TEXT)')
    base.commit()
    base.execute('CREATE TABLE IF NOT EXISTS napitky(img TEXT, name TEXT PRIMARY KEY, description TEXT, price TEXT)')
    base.commit()
    base.execute('CREATE TABLE IF NOT EXISTS alkhohol(img TEXT, name TEXT PRIMARY KEY, description TEXT, price TEXT)')
    base.commit()
    base.execute('CREATE TABLE IF NOT EXISTS klienty(id TEXT PRIMARY KEY, actyv TEXT)')
    base.commit()
    base.execute('CREATE TABLE IF NOT EXISTS napominanie(id TEXT , data TEXT, time TEXT, text TEXT)')
    base.commit()
    base.execute('CREATE TABLE IF NOT EXISTS izmenit_data(id TEXT , time TEXT, text TEXT)')
    base.commit()
    base.execute('CREATE TABLE IF NOT EXISTS izmenit_time(id TEXT , data TEXT, text TEXT)')
    base.commit()
    base.execute('CREATE TABLE IF NOT EXISTS izmenit_text(id TEXT , data TEXT, time TEXT)')
    base.commit()


async def sql_users_write(uid):
    cur.execute('INSERT INTO klienty VALUES(?, ?)', (uid, 1))
    base.commit()

async def sql_izmenit_data_write(uid, time, text):
    cur.execute('INSERT INTO izmenit_data VALUES(?, ?, ?)', (uid, time, text))
    base.commit()

async def sql_izmenit_time_write(uid, data, text):
    cur.execute('INSERT INTO izmenit_time VALUES(?, ?, ?)', (uid, data, text))
    base.commit()

async def sql_izmenit_text_write(uid, data, time):
    cur.execute('INSERT INTO izmenit_text VALUES(?, ?, ?)', (uid, data, time))
    base.commit()

# Запись в базу данных напоминания
async def sql_napominanie_wrtite(state):
    async with state.proxy() as data:
        cur.execute('INSERT INTO napominanie VALUES(?, ?, ?, ?)', tuple(data.values()))
        base.commit()


# Запись в базу данных где хранится пицца
async def sql_add_command(state):
    async with state.proxy() as data:
        cur.execute('INSERT INTO menu VALUES(?, ?, ?, ?)', tuple(data.values()))
        base.commit()


# Запись в базу данных где хранится роллы
async def sql_add_command_roli(state):
    async with state.proxy() as data:
        cur.execute('INSERT INTO roli VALUES(?, ?, ?, ?)', tuple(data.values()))
        base.commit()

# Запись в базу данных где хранится напитки
async def sql_add_command_napitky(state):
    async with state.proxy() as data:
        cur.execute('INSERT INTO napitky VALUES(?, ?, ?, ?)', tuple(data.values()))
        base.commit()

async def sql_add_command_alkhohol(state):
    async with state.proxy() as data:
        cur.execute('INSERT INTO alkhohol VALUES(?, ?, ?, ?)', tuple(data.values()))
        base.commit()




# Вторая база данных где таблицы с заказом,оформлением и вспомогательная таблица для записи
# промежуточных результатов для изменения количества заказанного
def sql_start_zak():
    global base_zak, cur_zak
    base_zak = sq.connect('pizza_cool_zakaz.db')
    cur_zak = base_zak.cursor()
    if base_zak:
        print('Data base_zakaz connected OK!')
    base_zak.execute('CREATE TABLE IF NOT EXISTS zak(id TEXT, menu TEXT, price TEXT, kol_vo TEXT)')
    base_zak.commit()
    base_zak.execute('CREATE TABLE IF NOT EXISTS ofr(id TEXT, name TEXT, location TEXT, number TEXT, pay TEXT)')
    base_zak.commit()
    base_zak.execute('CREATE TABLE IF NOT EXISTS location(id TEXT, latitude TEXT, longitude TEXT)')
    base_zak.commit()
    base_zak.execute('CREATE TABLE IF NOT EXISTS message(id TEXT, id_message TEXT)')
    base_zak.commit()



# ------------------------------------------------
async def sql_massage_id(uid, message_id):
    cur_zak.execute('INSERT INTO message VALUES(?, ?)', (uid, message_id))
    base_zak.commit()

async def sql_massage_id_update(uid, message_id):
    cur_zak.execute(f'UPDATE message set id_message == ? WHERE id = {uid}', (message_id,))
    base_zak.commit()

async def sql_delete_message(uid):
    cur_zak.execute(f'DELETE FROM message WHERE id = {uid}')
    base_zak.commit()

async def sql_read_message(uid):
    return cur_zak.execute(f'SELECT id_message FROM message WHERE id == ?',(uid,)).fetchone()










# Запись заказа в таблицу location
async def location_zapis(uid, latitude, longitude):
    cur_zak.execute('INSERT INTO location VALUES(?, ?, ?)', (uid, latitude, longitude))
    base_zak.commit()

# Запись заказа в таблицу zak
async def sql_add_command_zak(state):
    async with state.proxy() as data:
        cur_zak.execute('INSERT INTO zak VALUES(?, ?, ?, ?)', tuple(data.values()))
        base_zak.commit()

# Запись данных для оформления в таблицу ofr
async def sql_add_command_zak_ofr(state):
    async with state.proxy() as data:
        cur_zak.execute('INSERT INTO ofr VALUES(?, ?, ?, ?, ?)', tuple(data.values()))
        base_zak.commit()

# Обновление данных в таблице zak после изменения количества заказанного
async def sql_update_kol_dop(kol_vo_new, uid, N):
        cur_zak.execute('UPDATE zak SET kol_vo ==? WHERE id == ? AND menu == ?',(kol_vo_new, uid, N))
        base_zak.commit()

async def sql_users_update(uid,k):
    cur.execute(f'UPDATE klienty set actyv==? WHERE id = {uid}', (k,))
    base.commit()

async def sql_update_napominanie_data(data, uid, time, text):
    cur.execute('UPDATE napominanie SET data ==? WHERE id == ? AND time == ? AND text == ?', (data, uid, time, text))
    base.commit()

async def sql_update_napominanie_time(time, uid, data, text):
    cur.execute('UPDATE napominanie SET time ==? WHERE id == ? AND data == ? AND text == ?', (time, uid, data, text))
    base.commit()

async def sql_update_napominanie_text(text, uid, data, time):
    cur.execute('UPDATE napominanie SET text ==? WHERE id == ? AND data == ? AND time == ?', (text, uid, data, time))
    base.commit()
# ------------------------------------------------
# Чтение
# Считывание всех напоминаний
async def sql_napominanie_read():
    return cur.execute(f'SELECT * FROM napominanie').fetchall()

async def sql_napominanie_read_2():
    return cur.execute(f'SELECT * FROM napominanie').fetchone()

async def sql_napominanie_read_odin(uid):
    return cur.execute(f'SELECT data, time, text FROM napominanie WHERE id == ?',(uid,)).fetchall()

async def sql_napominanie_read_text(uid, data, time):
    return cur.execute(f'SELECT text FROM napominanie WHERE id == ? AND data == ? AND time == ?',(uid, data, time)).fetchone()

async def sql_izmenit_data(uid):
    return cur.execute(f'SELECT time, text FROM izmenit_data WHERE id == ?',(uid,)).fetchall()

async def sql_izmenit_time(uid):
    return cur.execute(f'SELECT data, text FROM izmenit_time WHERE id == ?',(uid,)).fetchall()

async def sql_izmenit_text(uid):
    return cur.execute(f'SELECT data, time FROM izmenit_text WHERE id == ?',(uid,)).fetchall()

async def sql_napominanie_read_emoty(uid):
    return cur.execute(f'SELECT  data FROM napominanie WHERE id = {uid}').fetchone()

async def sql_location_read(uid):
    return cur_zak.execute(f'SELECT latitude,longitude FROM location WHERE id == ?',(uid,)).fetchone()

# Считывание цены на заказанный продукт
async def sql_read_price(p):
    return cur.execute(f'SELECT price FROM menu WHERE name == ?',(p,)).fetchone()

async def sql_read_VSE_1(p):
    return cur.execute(f'SELECT img, description, price FROM menu WHERE name == ?',(p,)).fetchone()

async def sql_read_VSE_2(p):
    return cur.execute(f'SELECT img, description, price FROM roli WHERE name == ?',(p,)).fetchone()

async def sql_read_VSE_3(p):
    return cur.execute(f'SELECT img, description, price FROM napitky WHERE name == ?',(p,)).fetchone()

async def sql_read_VSE_4(p):
    return cur.execute(f'SELECT img, description, price FROM alkhohol WHERE name == ?',(p,)).fetchone()

async def sql_read_price_roli(p):
    return cur.execute(f'SELECT price FROM roli WHERE name == ?',(p,)).fetchone()

async def sql_read_price_napitky(p):
    return cur.execute(f'SELECT price FROM napitky WHERE name == ?',(p,)).fetchone()

async def sql_read_price_alkhohol(p):
    return cur.execute(f'SELECT price FROM alkhohol WHERE name == ?',(p,)).fetchone()

async def sql_read_drugie_tovary():
    return cur.execute('SELECT * FROM alkhohol').fetchall()



# Вызов меню для пиццы
async def sql_read(message):
    for ret in cur.execute('SELECT * FROM menu').fetchall():
        await bot.send_photo(message.from_user.id, ret[0], f'{ret[1]}\nОписание: {ret[2]}\n Цена {ret[-1]}Руб\n',
                             reply_markup=InlineKeyboardMarkup(). \
                             add(InlineKeyboardButton(f'Добавить в корзину 🛒 {ret[1]}', callback_data=f'zak {ret[1]}')))

# Вызов меню  для ролов
async def sql_read_roli(message):
    for ret in cur.execute('SELECT * FROM roli').fetchall():
        await bot.send_photo(message.from_user.id, ret[0], f'{ret[1]}\nОписание: {ret[2]}\n Цена {ret[-1]}Руб\n',
                             reply_markup=InlineKeyboardMarkup(). \
                             add(InlineKeyboardButton(f'Добавить в корзину 🛒 {ret[1]}', callback_data=f'zak {ret[1]}')))

# Вызов меню  для напитков
async def sql_read_napitky(message):
    for ret in cur.execute('SELECT * FROM napitky').fetchall():
        await bot.send_photo(message.from_user.id, ret[0], f'{ret[1]}\nОписание: {ret[2]}\n Цена {ret[-1]}Руб\n',
                             reply_markup=InlineKeyboardMarkup(). \
                             add(InlineKeyboardButton(f'Добавить в корзину 🛒 {ret[1]}', callback_data=f'zak {ret[1]}')))


# Считывание меню пиццы для редактирования в режиме админ
async def sql_read2():
    return cur.execute('SELECT * FROM menu').fetchall()

# Считывание меню роллы для редактирования в режиме админ
async def sql_read2_roli():
    return cur.execute('SELECT * FROM roli').fetchall()


# Считывание меню роллы для редактирования в режиме админ
async def sql_read2_napitky():
    return cur.execute('SELECT * FROM napitky').fetchall()

async def sql_read2_alkhohol():
    return cur.execute('SELECT * FROM alkhohol').fetchall()


async def sql_users_read_1(uid):
    return cur.execute(f'SELECT actyv FROM klienty WHERE id={uid}').fetchone()


async def sql_users_read_2():
    return cur.execute(f'SELECT * FROM klienty').fetchall()



# Считывание заказанного для отображения  в корзине
async def sql_read_zak(uid):
    return cur_zak.execute(f'SELECT menu, price, kol_vo FROM zak WHERE id = {uid}').fetchall()

# Считывание количества для проверки есть ли такая пицца в закзе
async def sql_read_zak_prov(uid, p):
    return cur_zak.execute(f'SELECT kol_vo FROM zak WHERE id = {uid} AND menu == ?',(p,)).fetchone()

# Считывание для проверки если что то в корзине соответствующее id ользователя
async def sql_read_zak_korz_empty(uid):
    return cur_zak.execute(f'SELECT menu FROM zak WHERE id = {uid}').fetchone()

# Считывание данных пользователя для отправки модератору
async def sql_read_zak_ofr(uid):
    return cur_zak.execute(f'SELECT name, location, number, pay FROM ofr WHERE id = {uid}').fetchall()

# Считывание количества заказанного для дальнейшегно изменения
async def sql_read_zak_kol_vo(uid, l):
    return cur_zak.execute(f'SELECT kol_vo FROM zak WHERE id = {uid} AND menu == ?',(l,)).fetchone()




# Удаление таблиц и баз
async def sql_delete_napominanie(uid,  data, time):
    cur.execute(f'DELETE FROM napominanie WHERE id ==? AND data == ? AND time == ?', (uid, data, time))
    base.commit()

async def sql_delete_izmenit_data(uid,  time, text):
    cur.execute(f'DELETE FROM izmenit_data WHERE id ==? AND time == ? AND text == ?', (uid, time, text))
    base.commit()

async def sql_delete_izmenit_time(uid,  data, text):
    cur.execute(f'DELETE FROM izmenit_time WHERE id ==? AND data == ? AND text == ?', (uid, data, text))
    base.commit()

async def sql_delete_izmenit_text(uid,  data, time):
    cur.execute(f'DELETE FROM izmenit_text WHERE id ==? AND data == ? AND time == ?', (uid, data, time))
    base.commit()

async def sql_delete(data):
    cur.execute('DELETE FROM menu WHERE name == ?', (data,))
    base.commit()

async def sql_delete_roli(data):
    cur.execute('DELETE FROM roli WHERE name == ?', (data,))
    base.commit()

async def sql_delete_napitky(data):
    cur.execute('DELETE FROM napitky WHERE name == ?', (data,))
    base.commit()

async def sql_delete_alkhohol(data):
    cur.execute('DELETE FROM alkhohol WHERE name == ?', (data,))
    base.commit()

# Удаление из таблицы zak заказанного пользователем
async def sql_delete_zak(uid):
    cur_zak.execute(f'DELETE FROM zak WHERE id = {uid}')
    base_zak.commit()

# Удаление из таблицы ofr данных пользователя после отправки модератору
async def sql_delete_zak_ofr(uid):
    cur_zak.execute(f'DELETE FROM ofr WHERE id = {uid}')
    base_zak.commit()

# Удаление из таблицы zak заказанного пользователем после отправки модератору
async def sql_delete_zakaz(data, uid):
    cur_zak.execute(f'DELETE FROM zak WHERE id ={uid} AND menu == ?', (data,))
    base_zak.commit()


async def sql_delete_location(uid):
    base_zak.execute(f'DELETE FROM location WHERE id = {uid}')
    base_zak.commit()



# Клавиатура клиент
start = KeyboardButton('/start')
b1 = KeyboardButton('Режим_работы 🔑')
b2 = KeyboardButton('Где мы находимся и наши контакты 🏠')
b3 = KeyboardButton('Меню 🍽')
pizza = KeyboardButton('Пицца🍕')
rolli = KeyboardButton('Роллы🍱')
napitky = KeyboardButton('Напитки🥤')
b4 = KeyboardButton('Поделиться номером ☎️', request_contact=True)
b5 = KeyboardButton('Отправить где я 📍', request_location=True)
ofrmit = KeyboardButton('Перейти к оформлению заказа 🗒✅')
zak_esche = KeyboardButton('Заказать ещё')
otmenit_zakaz = KeyboardButton('Назад 🔙')
otmenit_oformlenie = KeyboardButton('Отменить оформление ❌')
korzina = KeyboardButton('Корзина 🛒')
otmenit = KeyboardButton('Отменить❌')
nazad = KeyboardButton('Назад🔙')
otmenia = KeyboardButton('Отмена❌')
wiki = KeyboardButton('Поиск в Википедии 📚')
valuti = KeyboardButton('Курсы валют 💶')
napominanie = KeyboardButton('Поставить напоминание 📋')
posmotret_moi_napominania = KeyboardButton('Посмотреть мои напоминания 🗒')
drugie_tovary = KeyboardButton('Алкогольные напитки 🍷')


kb_otmenit = ReplyKeyboardMarkup(resize_keyboard=True)

kb_otmenia = ReplyKeyboardMarkup(resize_keyboard=True)

kb_otmenit_oformlenie = ReplyKeyboardMarkup(resize_keyboard=True)

kb_otmenit_zakaz = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

kb_client_of_zak = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

kb_client = ReplyKeyboardMarkup(resize_keyboard=True)

kb_client_number = ReplyKeyboardMarkup(resize_keyboard=True)

kb_client_location = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

kb_client_korzina= ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

kb_start = ReplyKeyboardMarkup(resize_keyboard=True)

kb_client_plus = ReplyKeyboardMarkup(resize_keyboard=True)

kb_razdel_menu = ReplyKeyboardMarkup(resize_keyboard=True)





kb_otmenia.add(otmenia)

kb_razdel_menu.row(pizza, rolli).row(napitky, drugie_tovary).add(nazad)

kb_start.add(start)

kb_client_korzina.row(korzina, zak_esche)

kb_client.row(b1, b2).add(b3)

kb_client_plus.row(b1, b2).row(b3, korzina).row(wiki, valuti).row(napominanie, posmotret_moi_napominania)

kb_client_of_zak.row(ofrmit).add(zak_esche)

kb_client_number.add(b4).add(otmenit_oformlenie)

kb_otmenit_zakaz.add(otmenit_zakaz).row(zak_esche, korzina)

kb_otmenit_oformlenie.add(otmenit_oformlenie)

kb_otmenit.add(otmenit)

kb_client_location.add(b5).add(otmenit_oformlenie)


# Клавиатура админ
a1 = KeyboardButton('/Загрузить')
a2 = KeyboardButton('/Удалить')
a3 = KeyboardButton('/Отмена')
vernytsia = KeyboardButton('/Назад')
pizza_adm = KeyboardButton('/пицца')
roli_adm = KeyboardButton('/роллы')
napitky_adm = KeyboardButton('/напитки')
alhohol_adm = KeyboardButton('/алкоголь')
rassylka =  KeyboardButton('/rassylka')
napominania_polzovatelei = KeyboardButton('/Посмотреть_напоминания_пользователей')

kb_admin = ReplyKeyboardMarkup(resize_keyboard=True)

kb_admin_vibor = ReplyKeyboardMarkup(resize_keyboard=True)

kb_admin_state = ReplyKeyboardMarkup(resize_keyboard=True)

kb_admin_vernytsia = ReplyKeyboardMarkup(resize_keyboard=True)

kb_admin_otmenit_rassylky = ReplyKeyboardMarkup(resize_keyboard=True)

kb_admin.add(a1).insert(a2).add(a3).insert(vernytsia).add(start)

kb_admin_vibor.row(pizza_adm, roli_adm, napitky_adm, alhohol_adm).row(rassylka, napominania_polzovatelei).add(start)

kb_admin_state.add(a1).insert(a2).add(a3)

kb_admin_vernytsia.add(vernytsia)

kb_admin_otmenit_rassylky.add(a3)


# Машина состояний - админ часть
class FSMAdmin(StatesGroup):
    photo = State()
    name = State()
    description = State()
    price = State()


ID = 687994353



@dp.message_handler(state="*", commands='отмена')
@dp.message_handler(Text(equals='отмена', ignore_case=True), state="*")
async def cancel_handler(messadge: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    else:
        await state.finish()
        await messadge.reply('Ок', reply_markup=kb_admin_vibor)


@dp.message_handler(commands='moderator', state=None)
async def moder_opred(messadge: types.Message):
    if messadge.from_user.id == ID:
        await bot.send_message(messadge.from_user.id, 'Здравствуй хозяин!!! Выбери нужный раздел',
                               reply_markup=kb_admin_vibor)
    else:
        await messadge.reply('Вы не модератор')

@dp.message_handler(commands='Посмотреть_напоминания_пользователей', state=None)
async def moder_opred(message: types.Message):
    if message.from_user.id == ID:
        k = await sql_napominanie_read_2()
        if k is None:
            await bot.send_message(message.from_user.id, f'Нет напоминаний')
        else:
            napominanie_read = await sql_napominanie_read()
            for ret in napominanie_read:
                uid = ret[0]
                kont_teleg = InlineKeyboardMarkup()
                btn = InlineKeyboardButton(
                    text=f'telegram того, кто поставил напоминание',
                    url=f"tg://user?id={uid}")
                btn2 = InlineKeyboardButton(f'Удалить напоминание ❌',
                                     callback_data=f'Delete_napominanie {ret[1]} {ret[2]}')
                kont_teleg.add(btn).add(btn2)
                await bot.send_message(message.from_user.id, f'Напоминание: {ret[1]} {ret[2]}\n'
                                                             f'{ret[3]}\n', reply_markup=kont_teleg)
    else:
        await message.reply('Вы не модератор')


@dp.message_handler(commands='Назад', state=None)
async def moder_opred(messadge: types.Message):
    if messadge.from_user.id == ID:
        await bot.send_message(messadge.from_user.id, 'Ок',
                               reply_markup=kb_admin_vibor)
    else:
        await messadge.reply('Вы не модератор')


@dp.message_handler(commands='пицца', state=None)
async def moder_opred(messadge: types.Message):
    if messadge.from_user.id == ID:
        global K
        K = 1
        await bot.send_message(messadge.from_user.id, 'Выбери действие',
                               reply_markup=kb_admin)
    else:
        await messadge.reply('Вы не модератор')


@dp.message_handler(commands='роллы', state=None)
async def moder_opred(messadge: types.Message):
    if messadge.from_user.id == ID:
        global K
        K = 2
        await bot.send_message(messadge.from_user.id, 'Выбери действие',
                               reply_markup=kb_admin)
    else:
        await messadge.reply('Вы не модератор')

@dp.message_handler(commands='напитки', state=None)
async def moder_opred(messadge: types.Message):
    if messadge.from_user.id == ID:
        global K
        K = 3
        await bot.send_message(messadge.from_user.id, 'Выбери действие',
                               reply_markup=kb_admin)
    else:
        await messadge.reply('Вы не модератор')


@dp.message_handler(commands='алкоголь', state=None)
async def moder_opred(messadge: types.Message):
    if messadge.from_user.id == ID:
        global K
        K = 4
        await bot.send_message(messadge.from_user.id, 'Выбери действие',
                               reply_markup=kb_admin)
    else:
        await messadge.reply('Вы не модератор')


@dp.message_handler(commands='Загрузить', state=None)
async def cm_start(messadge: types.Message):
    if messadge.from_user.id == ID:
        await FSMAdmin.photo.set()
        await messadge.reply('Загрузи фото', reply_markup=kb_admin_state)
    else:
        await messadge.reply('Вы не модератор')


@dp.message_handler(content_types=['photo'], state=FSMAdmin.photo)
async def load_photo(messadge: types.Message, state: FSMContext):
    if messadge.from_user.id == ID:
        async with state.proxy() as data:
            data['photo'] = messadge.photo[0].file_id
        await FSMAdmin.next()
        await messadge.reply('Теперь введите название')


@dp.message_handler(state=FSMAdmin.name)
async def load_name(messadge: types.Message, state: FSMContext):
    if messadge.from_user.id == ID:
        async with state.proxy() as data:
            data['name'] = messadge.text
        await FSMAdmin.next()
        await messadge.reply('Ведите описание')


@dp.message_handler(state=FSMAdmin.description)
async def load_description(messadge: types.Message, state: FSMContext):
    if messadge.from_user.id == ID:
        async with state.proxy() as data:
            data['description'] = messadge.text
        await FSMAdmin.next()
        await messadge.reply('Ведите цену')


@dp.message_handler(state=FSMAdmin.price)
async def load_price(messadge: types.Message, state: FSMContext):
    if messadge.from_user.id == ID:
        async with state.proxy() as data:
            data['price'] = float(messadge.text)
        if K == 1:
            await sql_add_command(state)
        elif K == 2:
            await sql_add_command_roli(state)
        elif K == 3:
            await sql_add_command_napitky(state)
        elif  K == 4:
            await sql_add_command_alkhohol(state)
    await bot.send_message(messadge.from_user.id, 'Спасибо, данные обновлены', reply_markup=kb_admin_vibor)
    await state.finish()


@dp.callback_query_handler(Text(startswith="del "))
async def del_colback(call: types.CallbackQuery):
    if K == 1:
        await sql_delete(call.data.replace('del ', ''))
        await call.answer(text=f'{(call.data.replace("del ", ""))} удалена.', show_alert=True)
    elif K==2:
        await sql_delete_roli(call.data.replace('del ', ''))
        await call.answer(text=f'{(call.data.replace("del ", ""))} удалены.', show_alert=True)
    elif K==3:
        await sql_delete_napitky(call.data.replace('del ', ''))
        await call.answer(text=f'{(call.data.replace("del ", ""))} удалены.', show_alert=True)
    elif K==4:
        await sql_delete_alkhohol(call.data.replace('del ', ''))
        await call.answer(text=f'{(call.data.replace("del ", ""))} удалено.', show_alert=True)
    await bot.send_message(call.from_user.id, 'Спасибо, данные обновлены', reply_markup=kb_admin_vibor)


@dp.message_handler(commands='Удалить')
async def delete_item(message: types.Message):
    await bot.send_message(message.from_user.id, 'Выбери, что нужно удалить', reply_markup=kb_admin_vernytsia)
    if message.from_user.id == ID:
        if K==1:
            read = await sql_read2()
            for ret in read:
                await bot.send_photo(message.from_user.id, ret[0],
                                     f'{ret[1]}\nОписание: {ret[2]}\n Цена {ret[-1]}Руб\n',
                                     reply_markup=InlineKeyboardMarkup(). \
                                     add(InlineKeyboardButton(f'Удалить {ret[1]}', callback_data=f'del {ret[1]}')))
        elif K==2:
            read = await sql_read2_roli()
            for ret in read:
                await bot.send_photo(message.from_user.id, ret[0],
                                     f'{ret[1]}\nОписание: {ret[2]}\n Цена {ret[-1]}Руб\n',
                                     reply_markup=InlineKeyboardMarkup(). \
                                     add(InlineKeyboardButton(f'Удалить {ret[1]}', callback_data=f'del {ret[1]}')))
        elif K==3:
            read = await sql_read2_napitky()
            for ret in read:
                await bot.send_photo(message.from_user.id, ret[0],
                                     f'{ret[1]}\nОписание: {ret[2]}\n Цена {ret[-1]}Руб\n',
                                     reply_markup=InlineKeyboardMarkup(). \
                                     add(InlineKeyboardButton(f'Удалить {ret[1]}', callback_data=f'del {ret[1]}')))
        elif K == 4:
            read = await sql_read2_alkhohol()
            for ret in read:
                await bot.send_photo(message.from_user.id, ret[0],
                                     f'{ret[1]}\nОписание: {ret[2]}\n Цена {ret[-1]}Руб\n',
                                     reply_markup=InlineKeyboardMarkup(). \
                                     add(InlineKeyboardButton(f'Удалить {ret[1]}', callback_data=f'del {ret[1]}')))


# Рассылка

class FSMrassylka(StatesGroup):
    Text = State()

@dp.message_handler(commands='rassylka', state=None)
async def rassylka (message: types.Message):
    if message.from_user.id == ID:
        await FSMrassylka.Text.set()
        await bot.send_message(message.from_user.id, 'Введи текст рассылки', reply_markup = kb_admin_otmenit_rassylky)
    else:
        await message.reply('Вы не модератор')


@dp.message_handler(content_types=['photo'], state=FSMrassylka.Text)
async def rassylka_otpr(message: types.Message, state: FSMContext):
    text = message.caption
    photo =message.photo[0].file_id
    users = await sql_users_read_2()
    for i in users:
        try:
            await bot.send_photo(i[0], photo, caption=text)
            if i[1] != 1:
                await sql_users_update(i[0], 1)
        except:
            await sql_users_update(i[0], 0)
    await bot.send_message(message.from_user.id, 'Сообщение успешно разослано',reply_markup = kb_admin_vibor)
    await state.finish()


@dp.message_handler(content_types=['text'], state=FSMrassylka.Text)
async def rassylka_otpr_text(message: types.Message, state: FSMContext):
    text = message.text
    users = await sql_users_read_2()
    for i in users:
        try:
            await bot.send_message(i[0], text)
            if i[1] != 1:
                await sql_users_update(i[0], 1)
        except:
            await sql_users_update(i[0], 0)
    await bot.send_message(message.from_user.id, 'Сообщение успешно разослано', reply_markup=kb_admin_vibor)
    await state.finish()




# Клиентская часть

class FSMnapominanie(StatesGroup):
    data = State()
    time = State()
    text = State()

# Парсинг из википедии

@dp.message_handler(state="*", content_types=['Отмена❌'])
@dp.message_handler(Text(equals='Отмена❌', ignore_case=True), state="*")
async def otmenia(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    else:
        await state.finish()
        await message.reply('Ок', reply_markup=kb_client_plus)


class FSMwikipedia(StatesGroup):
    text = State()

@dp.message_handler(state=FSMwikipedia.text)
async def wiki(message: types.Message, state: FSMContext):
    Text = message.text
    try:
        await bot.send_message(message.from_user.id, wikipedia.summary(f'{Text}'), reply_markup=kb_client_plus)
        await state.finish()
    except:
        await bot.send_message(message.from_user.id, 'По товоему запросу ничего не найдено, попробуй ещё раз')
        await state.finish()
        await FSMwikipedia.text.set()




@dp.message_handler(commands=['start', 'help'])
async def comand_start_help(message: types.Message):
    uid = message.from_user.id
    users_read = await sql_users_read_1(uid)
    if users_read is None:
        await sql_users_write(uid)
    await bot.send_message(message.from_user.id, 'Привет если хочешь вкусно поесть нажми меню 🍽', reply_markup=kb_client_plus)




@dp.message_handler(state="*", content_types=['Отменить оформление ❌'])
@dp.message_handler(Text(equals='Отменить оформление ❌', ignore_case=True), state="*")
async def otmenit_oformlenie(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    else:
        await state.finish()
        await message.reply('Ок', reply_markup=kb_client_korzina)


# Команда меню

@dp.message_handler(content_types=['text'], state=None)
async def REG_RAB_RASP(message: types.Message):
    if message.text == "Режим_работы 🔑":
        await bot.send_message(message.from_user.id, 'Вс-Чт с 9:00 до 20:00, Пт-Сб с 10:00 до 23:00')
    elif message.text == "Привет":
        await bot.send_message(message.from_user.id, 'Привет🤝 если хочешь вкусно поесть нажми меню 🍽', reply_markup=kb_client_plus)
    elif message.text == "id":
        await bot.send_message(message.from_user.id,
                               f"{message.from_user.first_name} {message.from_user.last_name}, твой ID:{message.from_user.id}")
    elif message.text == "Где мы находимся и наши контакты 🏠":
        keyboart_kont = InlineKeyboardMarkup()
        kont_btn_telegramm = InlineKeyboardButton(text = "Связь с нами telegram", url = "https://t.me/ChukashovD")
        kont_btn_vk = InlineKeyboardButton(text="Связь с нами VK", url="https://vk.com/d.chukashov")
        kont_btn_pochitat_mems = InlineKeyboardButton(text="Посмотреть мемасы", url="https://t.me/videos_dolboyoba")
        latitude = 55.771711
        longitude = 38.671478
        btn_local = InlineKeyboardButton(text='Локация', url=f"http://maps.google.com/?q={latitude},{longitude}")
        keyboart_kont.row(kont_btn_telegramm, kont_btn_vk).add(btn_local).add(kont_btn_pochitat_mems)
        await bot.send_message(message.from_user.id, 'Наш адрес: ул.Колбасная 15 \n'
                                                     'Почта: Pofig@gmail.com\n'
                                                     'Телефон: +79546238133', reply_markup=keyboart_kont)
    elif message.text == "Меню 🍽":
        await bot.send_message(message.from_user.id, 'Выбери раздел', reply_markup=kb_razdel_menu)
    elif message.text == 'Пицца🍕':
        await bot.send_message(message.from_user.id, 'Выбери пиццу', reply_markup=kb_otmenit_zakaz)
        await sql_read(message)
    elif message.text == 'Роллы🍱':
        await bot.send_message(message.from_user.id, 'Выбери роллы', reply_markup=kb_otmenit_zakaz)
        await sql_read_roli(message)
    elif message.text == 'Напитки🥤':
        await bot.send_message(message.from_user.id, 'Выбери нопиток', reply_markup=kb_otmenit_zakaz)
        await sql_read_napitky(message)
    elif message.text == 'Алкогольные напитки 🍷':
        k = 0
        await bot.send_message(message.from_user.id, 'Выбери товар', reply_markup=kb_otmenit_zakaz)
        drugie_tovary = await sql_read_drugie_tovary()
        drugie_tovary = drugie_tovary[k]
        await bot.send_photo(message.from_user.id, drugie_tovary[0], f'{drugie_tovary[1]}\nОписание: {drugie_tovary[2]}\n Цена {drugie_tovary[-1]}Руб\n',
                             reply_markup=InlineKeyboardMarkup(row = 2). \
                            add(InlineKeyboardButton('Следующее➡', callback_data=f'sled {k}')). \
                            add(InlineKeyboardButton(f'Добавить в корзину 🛒 {drugie_tovary[1]}',
                                                      callback_data=f'zakk {k}')))
    elif message.text == 'Назад🔙':
        await message.reply('Ок', reply_markup=kb_client_plus)
    elif message.text == 'Назад 🔙':
        await message.reply('Ок', reply_markup=kb_razdel_menu)
    elif message.text == "Заказать ещё":
        await bot.send_message(message.from_user.id, 'Выбери раздел', reply_markup=kb_razdel_menu)
    elif message.text == "Перейти к оформлению заказа 🗒✅":
        uid = message.from_user.id
        await sql_delete_message(uid)
        read_zak = await sql_read_zak(uid)
        def read_zak_str():
            read_zak_list = ''
            for r in read_zak:
                read_zak_list += f' Название: {r[0]}\n Количество: {r[2]}\n Цена:{r[1]} руб\n'
            return read_zak_list

        def podschet():
            sum = 0
            for r in read_zak:
                a = float(r[1])
                b = float(r[2])
                sum += a * b
            return sum

        await bot.send_message(message.from_user.id,f' Твой заказ 😋\n{read_zak_str()}\n '
                                                    f'--------------------------------------\n'
                                                    f' ИТОГ: {podschet()} руб')
        await FSMklient_ofr.namee.set()
        await message.reply('Напиши своё имя', reply_markup=kb_otmenit_oformlenie)
    elif message.text == "Корзина 🛒":
        uid = message.from_user.id
        read_zak_korz_empty = await sql_read_zak_korz_empty(uid)
        if read_zak_korz_empty is None:
            await bot.send_message(message.from_user.id, 'Корзина пуста', reply_markup=kb_client_plus)
        else:
            await bot.send_message(message.from_user.id, 'Твой заказ 😋', reply_markup=kb_client_of_zak)
            uid = message.from_user.id
            sum = 0
            read_zak = await sql_read_zak(uid)
            for ret in read_zak:
                a = float(ret[1])
                b = float(ret[2])
                sum += a * b
                await bot.send_message(message.from_user.id,
                                       f'{ret[0]}\n Цена: {ret[1]} руб\n Количество штук {ret[2]}',
                                       reply_markup=InlineKeyboardMarkup(row=2). \
                                       add(InlineKeyboardButton(f'Удалить из корзины {ret[0]} ❌',
                                                                callback_data=f'del_zak {ret[0]}')). \
                                       row(InlineKeyboardButton('Добавить ➕', callback_data=f'dobavit{ret[0]}'),
                                           InlineKeyboardButton('Убрать ➖', callback_data=f'ubrat{ret[0]}')))
            message_id_id = await bot.send_message(message.from_user.id, f'Итог:{sum} руб')

            message_id = message_id_id.message_id
            k = await sql_read_message(uid)
            if k is None:
                await sql_massage_id(uid, message_id)
            else:
                await sql_massage_id_update(uid, message_id)


    elif message.text == "Википедия":
        await FSMwikipedia.text.set()
        await bot.send_message(message.from_user.id,'Введи что хочешь найти', reply_markup=kb_otmenia)
    elif message.text == "Поиск в Википедии 📚":
        await FSMwikipedia.text.set()
        await bot.send_message(message.from_user.id, 'Введи что хочешь найти', reply_markup=kb_otmenia)
    elif message.text == "Курсы валют 💶":
         # Парсинг валюты курсов валюты с сайта ЦБ и rbc.ru
         # url = 'https://cbr.ru/'
         # r = requests.get(url)
         # html = BS(r.content,'html.parser')
         # pars_kurs = html.find_all("div", class_="col-md-2 col-xs-9 _right mono-num")
         # pars_data = html.find_all("div", class_="col-md-2 col-xs-7 _right")
         #
         # data = pars_data[1].text
         # dollar = pars_kurs[1].text
         # euro = pars_kurs[3].text

         url_dollar_rbk = 'https://quote.rbc.ru/ticker/59111'
         r_dollar_rbk = requests.get(url_dollar_rbk)
         html_dollar_rbk = BS(r_dollar_rbk.content, 'html.parser')

         pars_dollar_rbk = html_dollar_rbk.find_all("span", {"class": "chart__info__sum"})
         pars_dollar_rbk = pars_dollar_rbk[0].text


         url_euro_rbk = 'https://quote.rbc.ru/ticker/59090'
         r_euro_rbk = requests.get(url_euro_rbk)
         html_euro_rbk = BS(r_euro_rbk.content, 'html.parser')

         pars_euro_rbk = html_euro_rbk.find_all("span", {"class": "chart__info__sum"})
         pars_euro_rbk = pars_euro_rbk[0].text



         url_neft_brent_rbk = 'https://quote.rbc.ru/ticker/181206'
         r_neft_brent_rbk = requests.get(url_neft_brent_rbk)
         html_neft_brent_rbk = BS(r_neft_brent_rbk.content, 'html.parser')

         pars_neft_brent_rbk = html_neft_brent_rbk.find_all("span", {"class": "chart__info__sum"})
         pars_neft_brent_rbk = pars_neft_brent_rbk[0].text



         url_btk_rbk = 'https://www.rbc.ru/crypto/?utm_source=topline'
         r_btk_rbk = requests.get(url_btk_rbk)
         html_btk_rbk = BS(r_btk_rbk.content, 'html.parser')

         pars_btk_rbk = html_btk_rbk.find_all("span", {"class": "currencies__td__inner"})
         pars_btk_rbk_1 = pars_btk_rbk[0].text
         pars_btk_rbk_2 = pars_btk_rbk[1].text


         url_time = 'https://time100.ru/'
         r_time = requests.get(url_time)
         html_time = BS(r_time.content, 'html.parser')

         pars_time = html_time.find_all("span", {"class": "time"})
         pars_time_vrem = pars_time[0].text
         pars_time_data = pars_time[1].text
         pars_time_data = pars_time_data.replace('сегодня:','')



         # await bot.send_message(message.from_user.id, f'Официальные курсы валют от ЦБ РФ на {data}\n'
         #                                              f'USD {dollar}\n'
         #                                              f'EUR {euro}\n'
         #                                              f'Биржевые курсы с сайта rbk.ru на {pars_time_vrem} {pars_time_data} \n'
         #                                              f'USD = {pars_dollar_rbk}\n'
         #                                              f'EUR = {pars_euro_rbk}\n'
         #                                              f'Нефть Brent = {pars_neft_brent_rbk}\n'
         #                                              f'Курс биткоина {pars_btk_rbk_1} = ${pars_btk_rbk_2}', reply_markup=kb_client_plus)

         await bot.send_message(message.from_user.id, f'Биржевые курсы с сайта rbk.ru на {pars_time_vrem} {pars_time_data} \n'
                                                      f'USD = {pars_dollar_rbk}\n'
                                                      f'EUR = {pars_euro_rbk}\n'
                                                      f'Нефть Brent = {pars_neft_brent_rbk}\n'
                                                      f'Курс биткоина {pars_btk_rbk_1} = ${pars_btk_rbk_2}',
                                reply_markup=kb_client_plus)

    elif message.text == "Опрос":
        await bot.send_poll(message.from_user.id, 'вопрос', options=['1', '2', '3'])
    elif message.text == "Поставить напоминание 📋":
        await bot.send_message(message.from_user.id, 'Введите дату напоминания\n'
                                                     'Пример:\n'
                                                     '2022-06-11', reply_markup=kb_otmenia)
        await FSMnapominanie.data.set()
    elif message.text == "Посмотреть мои напоминания 🗒":
        # Просмотр поставленных напоминаний
        uid = message.from_user.id
        read_napominanie = await sql_napominanie_read_odin(uid)
        emoty_napominanie = await sql_napominanie_read_emoty(uid)
        if emoty_napominanie is None:
            await bot.send_message(message.from_user.id, f'У вас нет напоминаний')
        else:
            for ret in read_napominanie:
                await bot.send_message(message.from_user.id, f'Напоминание: {ret[0]} {ret[1]}\n '
                                                             f'{ret[2]}', reply_markup=InlineKeyboardMarkup(row=1). \
                                       add(InlineKeyboardButton(f'Удалить напоминание ❌',
                                                                callback_data=f'Delete_napominanie {ret[0]} {ret[1]}')). \
                                       add(InlineKeyboardButton(f'Изменить напоминание 📆',callback_data= f'Izmenit_napominanie {ret[0]} {ret[1]}')))
    else:
        await message.reply('Ты можешь написать Привет 🤝 или нажать start для заказа\n' +message.text, reply_markup = kb_start)
        await message.reply('Нажми обновить и текст обновится\n',
                            reply_markup=InlineKeyboardMarkup(row=1). \
                            add(InlineKeyboardButton(f'Обновить текст',
                                                     callback_data=f'Obnovit_text')))







@dp.message_handler(state=FSMnapominanie.data)
async def napominanie_data(message: types.Message, state: FSMContext):
    d = datetime.today()
    d1 = d.strftime("%Y-%m-%d")
    s = message.text
    s1 = s.replace("-", "")
    if s1.isdigit():
        v = 0
        for k in s1:
            v = v + 1
        if v == 8:
            if message.text >= d1:
                async with state.proxy() as data:
                    data['id'] = message.from_user.id
                    data['data'] = message.text
                await FSMnapominanie.time.set()
                await bot.send_message(message.from_user.id, 'Введите время напоминания\n'
                                                             'Пример:\n'
                                                             '18:12', reply_markup=kb_otmenia)
            else:
                await bot.send_message(message.from_user.id, 'Вы ввели не правильно дату или дату которая уже прошла\n')
                await bot.send_message(message.from_user.id, 'Введите дату напоминания\n'
                                                             'Пример:\n'
                                                             '2022-06-11', reply_markup=kb_otmenia)
                await state.finish()
                await FSMnapominanie.data.set()
        else:
            await bot.send_message(message.from_user.id, 'Вы ввели не дату\n')
            await bot.send_message(message.from_user.id, 'Введите дату напоминания\n'
                                                         'Пример:\n'
                                                         '2022-06-11', reply_markup=kb_otmenia)
            await state.finish()
            await FSMnapominanie.data.set()

    else:
        await bot.send_message(message.from_user.id, 'Вы ввели не дату\n')
        await bot.send_message(message.from_user.id, 'Введите дату напоминания\n'
                                                     'Пример:\n'
                                                     '2022-06-11', reply_markup=kb_otmenia)
        await state.finish()
        await FSMnapominanie.data.set()




@dp.message_handler(state=FSMnapominanie.time)
async def napominanie_time(message: types.Message, state: FSMContext):
        d = datetime.today()
        d1 = d.strftime("%Y-%m-%d")
        t1 = d.strftime("%H:%M")
        s = message.text
        s1 = s.replace(":", "")
        data = await state.get_data()
        dd = data.get('data')
        if s1.isdigit():
            v = 0
            for k in s1:
                v = v + 1
            if v == 4:
                if dd == d1:
                    if message.text >= t1:
                        async with state.proxy() as data:
                            data['time'] = message.text
                        await FSMnapominanie.text.set()
                        await bot.send_message(message.from_user.id, 'Введите текст напоминания',
                                               reply_markup=kb_otmenia)
                    else:
                        await bot.send_message(message.from_user.id,
                                               'Вы не верно ввели время или время, которое уже прошло\n')
                        await bot.send_message(message.from_user.id, 'Введите время напоминания\n'
                                                                     'Пример:\n'
                                                                     '18:12', reply_markup=kb_otmenia)
                else:
                    async with state.proxy() as data:
                        data['time'] = message.text
                    await FSMnapominanie.text.set()
                    await bot.send_message(message.from_user.id, 'Введите текст напоминания',
                                           reply_markup=kb_otmenia)
            else:
                await bot.send_message(message.from_user.id, 'Вы не верно ввели время\n')
                await bot.send_message(message.from_user.id, 'Введите время напоминания\n'
                                                             'Пример:\n'
                                                             '18:12', reply_markup=kb_otmenia)
                await FSMnapominanie.time.set()
        else:
            await bot.send_message(message.from_user.id, 'Вы не верно ввели время\n')
            await bot.send_message(message.from_user.id, 'Введите время напоминания\n'
                                                         'Пример:\n'
                                                         '18:12', reply_markup=kb_otmenia)
            await FSMnapominanie.time.set()




@dp.message_handler(state=FSMnapominanie.text)
async def napominanie_text(message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            data['text'] = message.text
        await  sql_napominanie_wrtite(state)
        await state.finish()
        await bot.send_message(message.from_user.id, 'Спасибо, напоминание поставленно', reply_markup = kb_client_plus)



# Ответ на кнопку удалить напоминание
@dp.callback_query_handler(Text(startswith="Delete_napominanie "))
async def Delete_napominanie(call: types.CallbackQuery):
    uid = call.from_user.id
    k = call.data.replace('Delete_napominanie ', '')
    # Разделяем переменну по пробелам и получаем кортеж
    k = k.split(' ')
    data = k[0]
    time = k[1]
    await sql_delete_napominanie(uid, data, time)
    await call.answer(text=f'Напоминание удалено')
    empty_napominanie = await sql_napominanie_read_emoty(uid)
    if empty_napominanie is None:
        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                    text="У вас нет напоминаний")
    else:
        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)


# Ответ на кнопку изменить напоминание
@dp.callback_query_handler(Text(startswith="Izmenit_napominanie "))
async def Izmenoit_napominanie(call: types.CallbackQuery):
    uid = call.from_user.id
    k = call.data.replace('Izmenit_napominanie ', '')
    # Разделяем переменну по пробелам и получаем кортеж
    k = k.split(' ')
    data = k[0]
    time = k[1]
    text = await sql_napominanie_read_text(uid, data, time)
    text = text[0]
    await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                text=f"Напоминание: {data} {time}\n{text}",
                                reply_markup=InlineKeyboardMarkup(row=2). \
                                add(InlineKeyboardButton(f'Удалить напоминание ❌',
                                                                callback_data=f'Delete_napominanie {data} {time}')). \
                                row(InlineKeyboardButton('Изменить дату 📅', callback_data=f'Izmenit_data {data} {time}'),
                                    InlineKeyboardButton('Изменить время ⏰', callback_data=f'Izmenit_time {data} {time}')). \
                                add(InlineKeyboardButton('Изменить текст напоминания🧾', callback_data=f'Izmenit_text {data} {time}')))

class FSMnapominanie_izmenit(StatesGroup):
    izmenenie_data = State()
    izmenenie_time = State()
    izmenenie_text = State()

@dp.callback_query_handler(Text(startswith="Izmenit_data "))
async def Izmenit_data(call: types.CallbackQuery ):
    await call.answer(text=f'Изменение даты')
    uid = call.from_user.id
    k = call.data.replace('Izmenit_data ', '')
    # Разделяем переменну по пробелам и получаем кортеж
    k = k.split(' ')
    data = k[0]
    time = k[1]
    text = await sql_napominanie_read_text(uid, data, time)
    text = text[0]
    await bot.send_message(call.message.chat.id, 'Введи новую дату\n'
                                                 'Пример:\n'
                                                 '2022-06-11', reply_markup=kb_otmenia)
    await sql_izmenit_data_write(uid, time, text)
    await FSMnapominanie_izmenit.izmenenie_data.set()

@dp.callback_query_handler(Text(startswith="Izmenit_time "))
async def Izmenit_time(call: types.CallbackQuery ):
    await call.answer(text=f'Изменение времени')
    uid = call.from_user.id
    k = call.data.replace('Izmenit_time ', '')
    # Разделяем переменну по пробелам и получаем кортеж
    k = k.split(' ')
    data = k[0]
    time = k[1]
    text = await sql_napominanie_read_text(uid, data, time)
    text = text[0]
    await bot.send_message(call.message.chat.id, 'Введи новое время'
                                                 'Пример:\n'
                                                 '18:12', reply_markup=kb_otmenia)
    await sql_izmenit_time_write(uid, data, text)
    await FSMnapominanie_izmenit.izmenenie_time.set()

@dp.callback_query_handler(Text(startswith="Izmenit_text "))
async def Izmenit_time(call: types.CallbackQuery ):
    await call.answer(text=f'Изменение текста напоминания')
    uid = call.from_user.id
    k = call.data.replace('Izmenit_text ', '')
    # Разделяем переменну по пробелам и получаем кортеж
    k = k.split(' ')
    data = k[0]
    time = k[1]
    text = await sql_napominanie_read_text(uid, data, time)
    text = text[0]
    await bot.send_message(call.message.chat.id, 'Введи новй текст', reply_markup=kb_otmenia)
    await sql_izmenit_text_write(uid, data, time)
    await FSMnapominanie_izmenit.izmenenie_text.set()


@dp.message_handler(state=FSMnapominanie_izmenit.izmenenie_data)
async def Izmenit_data_znachenie(message: types.Message, state: FSMContext):
    uid = message.from_user.id
    d = datetime.today()
    d1 = d.strftime("%Y-%m-%d")
    s = message.text
    s1 = s.replace("-", "")
    if s1.isdigit():
        v = 0
        for k in s1:
            v = v + 1
        if v == 8:
            if message.text >= d1:
                data = message.text
                read_izmenit_dataa = await sql_izmenit_data(uid)
                izmenit_dataa = read_izmenit_dataa[0]
                time = izmenit_dataa[0]
                text = izmenit_dataa[1]
                await sql_update_napominanie_data(data, uid, time, text)
                await sql_delete_izmenit_data(uid, time, text)
                await bot.send_message(message.chat.id, 'Данные успешно обновлены', reply_markup=kb_client_plus)
                await state.finish()
            else:
                await bot.send_message(message.from_user.id, 'Вы ввели дату которая уже прошла\n')
                await bot.send_message(message.from_user.id, 'Введите дату напоминания\n'
                                                             'Пример:\n'
                                                             '2022-06-11', reply_markup=kb_otmenia)
                await state.finish()
                await FSMnapominanie_izmenit.izmenenie_data.set()

        else:
            await bot.send_message(message.from_user.id, 'Вы ввели не дату\n')
            await bot.send_message(message.from_user.id, 'Введите дату напоминания\n'
                                                         'Пример:\n'
                                                         '2022-06-11', reply_markup=kb_otmenia)
            await state.finish()
            await FSMnapominanie_izmenit.izmenenie_data.set()

    else:
        await bot.send_message(message.from_user.id, 'Вы ввели не дату\n')
        await bot.send_message(message.from_user.id, 'Введите дату напоминания\n'
                                                     'Пример:\n'
                                                     '2022-06-11', reply_markup=kb_otmenia)
        await state.finish()
        await FSMnapominanie_izmenit.izmenenie_data.set()



@dp.message_handler(state=FSMnapominanie_izmenit.izmenenie_time)
async def Izmenit_time_znachenie(message: types.Message, state: FSMContext):
    uid = message.from_user.id
    d = datetime.today()
    d1 = d.strftime("%Y-%m-%d")
    t1 = d.strftime("%H:%M")
    s = message.text
    s1 = s.replace(":", "")
    read_izmenit_time = await sql_izmenit_time(uid)
    izmenit_time = read_izmenit_time[0]
    data = izmenit_time[0]
    dd = data
    if s1.isdigit():
        v = 0
        for k in s1:
            v = v + 1
        if v == 4:
            if dd == d1:
                if message.text >= t1:
                    time = message.text
                    read_izmenit_time = await sql_izmenit_time(uid)
                    izmenit_time = read_izmenit_time[0]
                    data = izmenit_time[0]
                    text = izmenit_time[1]
                    await sql_update_napominanie_time(time, uid, data, text)
                    await sql_delete_izmenit_time(uid, data, text)
                    await bot.send_message(message.chat.id, 'Данные успешно обновлены', reply_markup=kb_client_plus)
                    await state.finish()
                else:
                    await bot.send_message(message.from_user.id,
                                           'Вы не верно ввели время или время, которое уже прошло\n')
                    await bot.send_message(message.from_user.id, 'Введите время напоминания\n'
                                                                 'Пример:\n'
                                                                 '18:12', reply_markup=kb_otmenia)
            else:
                time = message.text
                read_izmenit_time = await sql_izmenit_time(uid)
                izmenit_time = read_izmenit_time[0]
                data = izmenit_time[0]
                text = izmenit_time[1]
                await sql_update_napominanie_time(time, uid, data, text)
                await sql_delete_izmenit_time(uid, data, text)
                await bot.send_message(message.chat.id, 'Данные успешно обновлены', reply_markup=kb_client_plus)
                await state.finish()
        else:
            await bot.send_message(message.from_user.id, 'Вы не верно ввели время\n')
            await bot.send_message(message.from_user.id, 'Введите время напоминания\n'
                                                         'Пример:\n'
                                                         '18:12', reply_markup=kb_otmenia)
    else:
        await bot.send_message(message.from_user.id, 'Вы не верно ввели время\n')
        await bot.send_message(message.from_user.id, 'Введите время напоминания\n'
                                                     'Пример:\n'
                                                     '18:12', reply_markup=kb_otmenia)

@dp.message_handler(state=FSMnapominanie_izmenit.izmenenie_text)
async def Izmenit_text_znachenie(message: types.Message, state: FSMContext):
    uid = message.from_user.id
    text = message.text
    read_izmenit_text = await sql_izmenit_text(uid)
    izmenit_text = read_izmenit_text[0]
    data = izmenit_text[0]
    time = izmenit_text[1]
    await sql_update_napominanie_text(text, uid, data, time)
    await sql_delete_izmenit_text(uid, data, time)
    await bot.send_message(message.chat.id, 'Данные успешно обновлены', reply_markup=kb_client_plus)
    await state.finish()



@dp.callback_query_handler(Text(startswith="Obnovit_text"))
async def obnov_text(call: types.CallbackQuery):
    await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Отлично работает")




@dp.callback_query_handler(Text(startswith="del_zak "))
async def del_zak_colback(call: types.CallbackQuery):
    uid = call.from_user.id
    await sql_delete_zakaz(call.data.replace('del_zak ', ''), uid)
    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    await call.answer(text=f'{(call.data.replace("del_zak", ""))} удалено из корзины.', show_alert=True)
    read_zak_korz_empty = await sql_read_zak_korz_empty(uid)
    read_zak = await sql_read_zak(uid)
    if read_zak_korz_empty is None:
        k = await sql_read_message(uid)
        k = int(k[0])
        message_id = k
        await bot.delete_message(chat_id=call.message.chat.id, message_id=message_id)
        await bot.send_message(call.message.chat.id, 'Корзина пуста', reply_markup=kb_client_plus)
    else:
        sum = 0
        for ret in read_zak:
            a = float(ret[1])
            b = float(ret[2])
            sum += a * b
        k = await sql_read_message(uid)
        k = int(k[0])
        message_id = k
        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=message_id,
                                    text=f"Итог:{sum} руб")




@dp.callback_query_handler(Text(startswith="dobavit "))
async def kol_vo_zak_dop(call: types.CallbackQuery):
    await call.answer(text=f'добавленно')
    uid = call.from_user.id
    l = call.data.replace("dobavit", "")
    p = call.data.replace("dobavit ", "")
    read_zak_kol_vo = await sql_read_zak_kol_vo(uid,l)
    a = int(read_zak_kol_vo[0])
    a = a+1
    read_price = await sql_read_price(p)
    if read_price is None:
        read_price = await sql_read_price_roli(p)
    if read_price is None:
        read_price = await sql_read_price_napitky(p)
    if read_price is None:
        read_price = await sql_read_price_alkhohol(p)


    await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                text=f"{l}\n Цена: {read_price[0]} руб\n Количество штук {a}",reply_markup=InlineKeyboardMarkup(row=2). \
                                   add(InlineKeyboardButton(f'Удалить из корзины {l} ❌',
                                                            callback_data=f'del_zak {l}')). \
                                   row(InlineKeyboardButton('Добавить ➕', callback_data=f'dobavit{l}'),
                                       InlineKeyboardButton('Убрать ➖', callback_data=f'ubrat{l}')))

    await sql_update_kol_dop(a, uid, l)
    read_zak = await sql_read_zak(uid)
    sum = 0
    for ret in read_zak:
        a = float(ret[1])
        b = float(ret[2])
        sum += a * b
    k = await sql_read_message(uid)
    k = int(k[0])
    message_id = k
    await bot.edit_message_text(chat_id=call.message.chat.id, message_id = message_id,
                           text=f"Итог:{sum} руб")




@dp.callback_query_handler(Text(startswith="ubrat "))
async def kol_vo_zak_dop_minus(call: types.CallbackQuery):
    uid = call.from_user.id
    l = call.data.replace("ubrat", "")
    p = call.data.replace("ubrat ", "")
    read_zak_kol_vo = await sql_read_zak_kol_vo(uid,l)
    a = int(read_zak_kol_vo[0])
    a = a-1
    if a > 0:
        await call.answer(text=f'убранно')
        read_price = await sql_read_price(p)
        if read_price is None:
            read_price = await sql_read_price_roli(p)
        if read_price is None:
            read_price = await sql_read_price_napitky(p)
        if read_price is None:
            read_price = await sql_read_price_alkhohol(p)

        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                    text=f"{l}\n Цена: {read_price[0]} руб\n Количество штук {a}",
                                    reply_markup=InlineKeyboardMarkup(row=2). \
                                    add(InlineKeyboardButton(f'Удалить из корзины {l} ❌',
                                                             callback_data=f'del_zak {l}')). \
                                    row(InlineKeyboardButton('Добавить ➕', callback_data=f'dobavit{l}'),
                                        InlineKeyboardButton('Убрать ➖', callback_data=f'ubrat{l}')))

        await sql_update_kol_dop(a, uid, l)
        read_zak = await sql_read_zak(uid)
        sum = 0
        for ret in read_zak:
            a = float(ret[1])
            b = float(ret[2])
            sum += a * b
        k = await sql_read_message(uid)
        k = int(k[0])
        message_id = k
        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=message_id,
                                    text=f"Итог:{sum} руб")
    else:
        await call.answer(text=f'Данной позиции в корзине больше нет')
        await sql_delete_zakaz(l, uid)
        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        read_zak = await sql_read_zak(uid)
        read_zak_korz_empty = await sql_read_zak_korz_empty(uid)
        if read_zak_korz_empty is None:
            k = await sql_read_message(uid)
            k = int(k[0])
            message_id = k
            await bot.delete_message(chat_id=call.message.chat.id, message_id=message_id)
            await bot.send_message( call.message.chat.id, 'Корзина пуста', reply_markup = kb_client_plus)
        else:
            sum = 0
            for ret in read_zak:
                a = float(ret[1])
                b = float(ret[2])
                sum += a * b
            k = await sql_read_message(uid)
            k = int(k[0])
            message_id = k
            await bot.edit_message_text(chat_id=call.message.chat.id, message_id=message_id,
                                        text=f"Итог:{sum} руб")


# Другая форма меню(ответ на кнопку следующий)
@dp.callback_query_handler(Text(startswith="sled "))
async def zak_drugie_tovary_sled(call: types.CallbackQuery):
    uid = call.from_user.id
    k = call.data.replace("sled ", "")
    k = int(k)
    k = k + 1
    drugie_tovary = await sql_read_drugie_tovary()
    v = len(drugie_tovary)
    drugie_tovary = drugie_tovary[k]
    l = drugie_tovary[1]
    l = ' ' + l
    yest = await sql_read_zak_prov(uid, l)
    if yest is None:
        if k >= v-1:
            await call.answer(text=f'следующий товар')
            k = v-1
            await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            await bot.send_photo(call.from_user.id, drugie_tovary[0],
                                 f'{drugie_tovary[1]}\nОписание: {drugie_tovary[2]}\n Цена {drugie_tovary[-1]}Руб\n',
                                 reply_markup=InlineKeyboardMarkup(row=2). \
                                 add(InlineKeyboardButton('⬅Предыдущее', callback_data=f'pred {k}')). \
                                 add(InlineKeyboardButton(f'Добавить в корзину 🛒 {drugie_tovary[1]}',
                                                          callback_data=f'zakk {k}')))
        else:
            await call.answer(text=f'следующий товар')
            await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            await bot.send_photo(call.from_user.id, drugie_tovary[0],
                                 f'{drugie_tovary[1]}\nОписание: {drugie_tovary[2]}\n Цена {drugie_tovary[-1]}Руб\n',
                                 reply_markup=InlineKeyboardMarkup(row=2). \
                                 row(InlineKeyboardButton('⬅Предыдущее', callback_data=f'pred {k}'),
                                     InlineKeyboardButton('Следующее➡', callback_data=f'sled {k}')). \
                                 add(InlineKeyboardButton(f'Добавить в корзину 🛒 {drugie_tovary[1]}',
                                                          callback_data=f'zakk {k}')))
    else:
        read_zak_kol_vo = await sql_read_zak_kol_vo(uid, l)
        a = read_zak_kol_vo[0]
        a = int(a)
        if k == 0:
            await call.answer(text=f'следующий товар')
            await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            await bot.send_photo(call.from_user.id, drugie_tovary[0],
                                 f'{drugie_tovary[1]}\nОписание: {drugie_tovary[2]}\n Цена {drugie_tovary[-1]}Руб\n Количество: {a}',
                                 reply_markup=InlineKeyboardMarkup(row=2). \
                                 add(InlineKeyboardButton('Следующее➡', callback_data=f'sled {k}')). \
                                 add(InlineKeyboardButton(f'Удалить из корзины {drugie_tovary[1]} ❌',
                                                          callback_data=f'delete_zakk {k}')). \
                                 row(InlineKeyboardButton('Добавить ➕', callback_data=f'dobavittt {k}'),
                                     InlineKeyboardButton('Убрать ➖', callback_data=f'ubrattt {k}')))
        elif k == v-1:
            await call.answer(text=f'следующий товар')
            await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            await bot.send_photo(call.from_user.id, drugie_tovary[0],
                                 f'{drugie_tovary[1]}\nОписание: {drugie_tovary[2]}\n Цена {drugie_tovary[-1]}Руб\n Количество: {a}',
                                 reply_markup=InlineKeyboardMarkup(row=2). \
                                 add(InlineKeyboardButton('⬅Предыдущее', callback_data=f'pred {k}')). \
                                 add(InlineKeyboardButton(f'Удалить из корзины {drugie_tovary[1]} ❌',
                                                          callback_data=f'delete_zakk {k}')). \
                                 row(InlineKeyboardButton('Добавить ➕', callback_data=f'dobavittt {k}'),
                                     InlineKeyboardButton('Убрать ➖', callback_data=f'ubrattt {k}')))
        else:
            await call.answer(text=f'следующий товар')
            await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            await bot.send_photo(call.from_user.id, drugie_tovary[0],
                                 f'{drugie_tovary[1]}\nОписание: {drugie_tovary[2]}\n Цена {drugie_tovary[-1]}Руб\n Количество: {a}',
                                 reply_markup=InlineKeyboardMarkup(row=2). \
                                 row(InlineKeyboardButton('⬅Предыдущее', callback_data=f'pred {k}'),
                                     InlineKeyboardButton('Следующее➡', callback_data=f'sled {k}')). \
                                 add(InlineKeyboardButton(f'Удалить из корзины {drugie_tovary[1]} ❌',
                                                          callback_data=f'delete_zakk {k}')). \
                                 row(InlineKeyboardButton('Добавить ➕', callback_data=f'dobavittt {k}'),
                                     InlineKeyboardButton('Убрать ➖', callback_data=f'ubrattt {k}')))



# Другая форма меню(ответ на кнопку предидущий)
@dp.callback_query_handler(Text(startswith="pred "))
async def zak_drugie_tovary_pred(call: types.CallbackQuery):
    uid = call.from_user.id
    k = call.data.replace("pred ", "")
    k = int(k)
    k = k - 1
    drugie_tovary = await sql_read_drugie_tovary()
    v = len(drugie_tovary)
    drugie_tovary = drugie_tovary[k]
    l = drugie_tovary[1]
    l = ' ' + l
    yest = await sql_read_zak_prov(uid, l)
    if yest is None:
        if k <= 0:
            await call.answer(text=f'предидущий товар')
            k = 0
            await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            await bot.send_photo(call.from_user.id, drugie_tovary[0],
                                 f'{drugie_tovary[1]}\nОписание: {drugie_tovary[2]}\n Цена {drugie_tovary[-1]}Руб\n',
                                 reply_markup=InlineKeyboardMarkup(row=2). \
                                 add(InlineKeyboardButton('Следующее➡', callback_data=f'sled {k}')). \
                                 add(InlineKeyboardButton(f'Добавить в корзину 🛒 {drugie_tovary[1]}',
                                                          callback_data=f'zakk {k}')))
        else:
            await call.answer(text=f'предидущий товар')
            await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            await bot.send_photo(call.from_user.id, drugie_tovary[0],
                                 f'{drugie_tovary[1]}\nОписание: {drugie_tovary[2]}\n Цена {drugie_tovary[-1]}Руб\n',
                                 reply_markup=InlineKeyboardMarkup(row=2). \
                                 row(InlineKeyboardButton('⬅Предыдущее', callback_data=f'pred {k}'),
                                     InlineKeyboardButton('Следующее➡', callback_data=f'sled {k}')). \
                                 add(InlineKeyboardButton(f'Добавить в корзину 🛒 {drugie_tovary[1]}',
                                                          callback_data=f'zakk {k}')))
    else:
        read_zak_kol_vo = await sql_read_zak_kol_vo(uid, l)
        a = read_zak_kol_vo[0]
        a = int(a)
        if k == 0:
            await call.answer(text=f'предидущий товар')
            await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            await bot.send_photo(call.from_user.id, drugie_tovary[0],
                                 f'{drugie_tovary[1]}\nОписание: {drugie_tovary[2]}\n Цена {drugie_tovary[-1]}Руб\n Количество: {a}',
                                 reply_markup=InlineKeyboardMarkup(row=2). \
                                 add(InlineKeyboardButton('Следующее➡', callback_data=f'sled {k}')). \
                                 add(InlineKeyboardButton(f'Удалить из корзины {drugie_tovary[1]} ❌',
                                                          callback_data=f'delete_zakk {k}')). \
                                 row(InlineKeyboardButton('Добавить ➕', callback_data=f'dobavittt {k}'),
                                     InlineKeyboardButton('Убрать ➖', callback_data=f'ubrattt {k}')))
        elif k == v - 1:
            await call.answer(text=f'предидущий товар')
            await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            await bot.send_photo(call.from_user.id, drugie_tovary[0],
                                 f'{drugie_tovary[1]}\nОписание: {drugie_tovary[2]}\n Цена {drugie_tovary[-1]}Руб\n Количество: {a}',
                                 reply_markup=InlineKeyboardMarkup(row=2). \
                                 add(InlineKeyboardButton('⬅Предыдущее', callback_data=f'pred {k}')). \
                                 add(InlineKeyboardButton(f'Удалить из корзины {drugie_tovary[1]} ❌',
                                                          callback_data=f'delete_zakk {k}')). \
                                 row(InlineKeyboardButton('Добавить ➕', callback_data=f'dobavittt {k}'),
                                     InlineKeyboardButton('Убрать ➖', callback_data=f'ubrattt {k}')))
        else:
            await call.answer(text=f'предидущий товар')
            await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            await bot.send_photo(call.from_user.id, drugie_tovary[0],
                                 f'{drugie_tovary[1]}\nОписание: {drugie_tovary[2]}\n Цена {drugie_tovary[-1]}Руб\n Количество: {a}',
                                 reply_markup=InlineKeyboardMarkup(row=2). \
                                 row(InlineKeyboardButton('⬅Предыдущее', callback_data=f'pred {k}'),
                                     InlineKeyboardButton('Следующее➡', callback_data=f'sled {k}')). \
                                 add(InlineKeyboardButton(f'Удалить из корзины {drugie_tovary[1]} ❌',
                                                          callback_data=f'delete_zakk {k}')). \
                                 row(InlineKeyboardButton('Добавить ➕', callback_data=f'dobavittt {k}'),
                                     InlineKeyboardButton('Убрать ➖', callback_data=f'ubrattt {k}')))



@dp.callback_query_handler(Text(startswith="zakk "))
async def zakk_colback(call: types.CallbackQuery, state: FSMContext):
    await call.answer(text=f'Добавленно в корзину')
    uid = call.from_user.id
    k=call.data.replace("zakk ", "")
    k = int(k)
    drugie_tovary = await sql_read_drugie_tovary()
    v = len(drugie_tovary)
    drugie_tovary = drugie_tovary[k]
    p = drugie_tovary[1]
    l = drugie_tovary[1]
    l = ' ' + l
    read_price = await sql_read_price(p)
    if read_price is None:
        read_price = await sql_read_price_roli(p)
    if read_price is None:
        read_price = await sql_read_price_napitky(p)
    if read_price is None:
        read_price = await sql_read_price_alkhohol(p)
    read_price_base = read_price[0]
    yest = await sql_read_zak_prov(uid,l)
    if yest is None:
        async with state.proxy() as data:
            data['id'] = call.from_user.id
            data['menu'] = l
            data['price'] = read_price_base
            data['kol_vo'] = '1'
        await sql_add_command_zak(state)
        await state.finish()
        read_zak_VSE = await sql_read_VSE_1(p)
        if read_zak_VSE is None:
            read_zak_VSE = await sql_read_VSE_2(p)
        if read_zak_VSE is None:
            read_zak_VSE = await sql_read_VSE_3(p)
        if k == 0:
            await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                           caption=f"{l}\n Цена: {read_price[0]} руб\n Количество: 1",
                                           reply_markup=InlineKeyboardMarkup(row=2). \
                                           row(InlineKeyboardButton('Следующее➡', callback_data=f'sled {k}')). \
                                           add(InlineKeyboardButton(f'Удалить из корзины {l} ❌',
                                                                    callback_data=f'delete_zakk {k}')). \
                                           row(InlineKeyboardButton('Добавить ➕', callback_data=f'dobavittt {k}'),
                                               InlineKeyboardButton('Убрать ➖', callback_data=f'ubrattt {k}')))
        elif k == v-1:
            await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                           caption=f"{l}\n Цена: {read_price[0]} руб\n Количество: 1",
                                           reply_markup=InlineKeyboardMarkup(row=2). \
                                           row(InlineKeyboardButton('⬅Предыдущее', callback_data=f'pred {k}')). \
                                           add(InlineKeyboardButton(f'Удалить из корзины {l} ❌',
                                                                    callback_data=f'delete_zakk {k}')). \
                                           row(InlineKeyboardButton('Добавить ➕', callback_data=f'dobavittt {k}'),
                                               InlineKeyboardButton('Убрать ➖', callback_data=f'ubrattt {k}')))
        else:
            await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                           caption=f"{l}\n Цена: {read_price[0]} руб\n Количество: 1",
                                           reply_markup=InlineKeyboardMarkup(row=2). \
                                           row(InlineKeyboardButton('⬅Предыдущее', callback_data=f'pred {k}'),
                                               InlineKeyboardButton('Следующее➡', callback_data=f'sled {k}')). \
                                           add(InlineKeyboardButton(f'Удалить из корзины {l} ❌',
                                                                    callback_data=f'delete_zakk {k}')). \
                                           row(InlineKeyboardButton('Добавить ➕', callback_data=f'dobavittt {k}'),
                                               InlineKeyboardButton('Убрать ➖', callback_data=f'ubrattt {k}')))

    else:
        read_zak_kol_vo = await sql_read_zak_kol_vo(uid, l)
        a = read_zak_kol_vo[0]
        a = int(a)
        await state.finish()
        read_zak_VSE = await sql_read_VSE_1(p)
        if read_zak_VSE is None:
            read_zak_VSE = await sql_read_VSE_2(p)
        if read_zak_VSE is None:
            read_zak_VSE = await sql_read_VSE_3(p)
        if k == 0:
            await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                           caption=f"{l}\n Цена: {read_price[0]} руб\n Количество: {a}",
                                           reply_markup=InlineKeyboardMarkup(row=2). \
                                           add(InlineKeyboardButton('Следующее➡', callback_data=f'sled {k}')). \
                                           add(InlineKeyboardButton(f'Удалить из корзины {l} ❌',
                                                                    callback_data=f'delete_zakk {k}')). \
                                           row(InlineKeyboardButton('Добавить ➕', callback_data=f'dobavittt {k}'),
                                               InlineKeyboardButton('Убрать ➖', callback_data=f'ubrattt {k}')))
        elif k == v-1:
            await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                           caption=f"{l}\n Цена: {read_price[0]} руб\n Количество: {a}",
                                           reply_markup=InlineKeyboardMarkup(row=2). \
                                           add(InlineKeyboardButton('⬅Предыдущее', callback_data=f'pred {k}')). \
                                           add(InlineKeyboardButton(f'Удалить из корзины {l} ❌',
                                                                    callback_data=f'delete_zakk {k}')). \
                                           row(InlineKeyboardButton('Добавить ➕', callback_data=f'dobavittt {k}'),
                                               InlineKeyboardButton('Убрать ➖', callback_data=f'ubrattt {k}')))
        else:
            await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                           caption=f"{l}\n Цена: {read_price[0]} руб\n Количество: {a}",
                                           reply_markup=InlineKeyboardMarkup(row=2). \
                                           row(InlineKeyboardButton('⬅Предыдущее', callback_data=f'pred {k}'),
                                               InlineKeyboardButton('Следующее➡', callback_data=f'sled {k}')). \
                                           add(InlineKeyboardButton(f'Удалить из корзины {l} ❌',
                                                                    callback_data=f'delete_zakk {k}')). \
                                           row(InlineKeyboardButton('Добавить ➕', callback_data=f'dobavittt {k}'),
                                               InlineKeyboardButton('Убрать ➖', callback_data=f'ubrattt {k}')))
        await call.answer(text=f'Добавленно в корзину')


@dp.callback_query_handler(Text(startswith="dobavittt "))
async def kol_vo_zak_new_DR(call: types.CallbackQuery):
    await call.answer(text=f'добавленно')
    uid = call.from_user.id
    k = call.data.replace("dobavittt ", "")
    k = int(k)
    drugie_tovary = await sql_read_drugie_tovary()
    v = len(drugie_tovary)
    drugie_tovary = drugie_tovary[k]
    p = drugie_tovary[1]
    l = drugie_tovary[1]
    l = ' ' + l
    read_zak_kol_vo = await sql_read_zak_kol_vo(uid,l)
    a = int(read_zak_kol_vo[0])
    a = a+1
    read_price = await sql_read_price(p)
    if read_price is None:
        read_price = await sql_read_price_roli(p)
    if read_price is None:
        read_price = await sql_read_price_napitky(p)
    if read_price is None:
        read_price = await sql_read_price_alkhohol(p)
    if k == 0:
        await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                       caption=f"{l}\n Цена: {read_price[0]} руб\n Количество: {a}",
                                       reply_markup=InlineKeyboardMarkup(row=2). \
                                       row(InlineKeyboardButton('Следующее➡', callback_data=f'sled {k}')). \
                                       add(InlineKeyboardButton(f'Удалить из корзины {l} ❌',
                                                                callback_data=f'delete_zakk {k}')). \
                                       row(InlineKeyboardButton('Добавить ➕', callback_data=f'dobavittt {k}'),
                                           InlineKeyboardButton('Убрать ➖', callback_data=f'ubrattt {k}')))
    elif k == v-1 :
        await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                       caption=f"{l}\n Цена: {read_price[0]} руб\n Количество: {a}",
                                       reply_markup=InlineKeyboardMarkup(row=2). \
                                       row(InlineKeyboardButton('⬅Предыдущее', callback_data=f'pred {k}')). \
                                       add(InlineKeyboardButton(f'Удалить из корзины {l} ❌',
                                                                callback_data=f'delete_zakk {k}')). \
                                       row(InlineKeyboardButton('Добавить ➕', callback_data=f'dobavittt {k}'),
                                           InlineKeyboardButton('Убрать ➖', callback_data=f'ubrattt {k}')))

    else:
        await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                       caption=f"{l}\n Цена: {read_price[0]} руб\n Количество: {a}",
                                       reply_markup=InlineKeyboardMarkup(row=2). \
                                       row(InlineKeyboardButton('⬅Предыдущее', callback_data=f'pred {k}'),
                                          InlineKeyboardButton('Следующее➡', callback_data=f'sled {k}')). \
                                       add(InlineKeyboardButton(f'Удалить из корзины {l} ❌',
                                                                callback_data=f'delete_zakk {k}')). \
                                       row(InlineKeyboardButton('Добавить ➕', callback_data=f'dobavittt {k}'),
                                           InlineKeyboardButton('Убрать ➖', callback_data=f'ubrattt {k}')))

    await sql_update_kol_dop(a, uid, l)



@dp.callback_query_handler(Text(startswith="ubrattt "))
async def kol_vo_zak_new_DR_ubr(call: types.CallbackQuery):
    await call.answer(text=f'Убрано')
    uid = call.from_user.id
    k = call.data.replace("ubrattt ", "")
    k = int(k)
    drugie_tovary = await sql_read_drugie_tovary()
    v = len(drugie_tovary)
    drugie_tovary = drugie_tovary[k]
    p = drugie_tovary[1]
    l = drugie_tovary[1]
    l = ' ' + l
    read_zak_kol_vo = await sql_read_zak_kol_vo(uid,l)
    a = int(read_zak_kol_vo[0])
    a = a-1
    if a > 0:
        read_price = await sql_read_price(p)
        if read_price is None:
            read_price = await sql_read_price_roli(p)
        if read_price is None:
            read_price = await sql_read_price_napitky(p)
        if read_price is None:
            read_price = await sql_read_price_alkhohol(p)
        if k == 0:
            await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                           caption=f"{l}\n Цена: {read_price[0]} руб\n Количество: {a}",
                                           reply_markup=InlineKeyboardMarkup(row=2). \
                                           add(InlineKeyboardButton('Следующее➡', callback_data=f'sled {k}')). \
                                           add(InlineKeyboardButton(f'Удалить из корзины {l} ❌',
                                                                    callback_data=f'delete_zakk {k}')). \
                                           row(InlineKeyboardButton('Добавить ➕', callback_data=f'dobavittt {k}'),
                                               InlineKeyboardButton('Убрать ➖', callback_data=f'ubrattt {k}')))
        elif  k == v-1:
            await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                           caption=f"{l}\n Цена: {read_price[0]} руб\n Количество: {a}",
                                           reply_markup=InlineKeyboardMarkup(row=2). \
                                           add(InlineKeyboardButton('⬅Предыдущее', callback_data=f'pred {k}')). \
                                           add(InlineKeyboardButton(f'Удалить из корзины {l} ❌',
                                                                    callback_data=f'delete_zakk {k}')). \
                                           row(InlineKeyboardButton('Добавить ➕', callback_data=f'dobavittt {k}'),
                                               InlineKeyboardButton('Убрать ➖', callback_data=f'ubrattt {k}')))
        else:
            await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                           caption=f"{l}\n Цена: {read_price[0]} руб\n Количество: {a}",
                                           reply_markup=InlineKeyboardMarkup(row=2). \
                                           row(InlineKeyboardButton('⬅Предыдущее', callback_data=f'pred {k}'),
                                               InlineKeyboardButton('Следующее➡', callback_data=f'sled {k}')). \
                                           add(InlineKeyboardButton(f'Удалить из корзины {l} ❌',
                                                                    callback_data=f'delete_zakk {k}')). \
                                           row(InlineKeyboardButton('Добавить ➕', callback_data=f'dobavittt {k}'),
                                               InlineKeyboardButton('Убрать ➖', callback_data=f'ubrattt {k}')))

        await sql_update_kol_dop(a, uid, l)
    else:
        read_zak_VSE = await sql_read_VSE_1(p)
        if read_zak_VSE is None:
            read_zak_VSE = await sql_read_VSE_2(p)
        if read_zak_VSE is None:
            read_zak_VSE = await sql_read_VSE_3(p)
        if read_zak_VSE is None:
            read_zak_VSE = await sql_read_VSE_4(p)

        if k == 0:
            await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                           caption=f"{l}\n Описание: {read_zak_VSE[1]}\n Цена: {read_zak_VSE[2]} руб",
                                           reply_markup=InlineKeyboardMarkup(row=2). \
                                           add(InlineKeyboardButton('Следующее➡', callback_data=f'sled {k}')). \
                                           add(InlineKeyboardButton(f'Добавить в корзину 🛒 {drugie_tovary[1]}',
                                                                    callback_data=f'zakk {k}')))
        elif k == v-1:
            await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                           caption=f"{l}\n Описание: {read_zak_VSE[1]}\n Цена: {read_zak_VSE[2]} руб",
                                           reply_markup=InlineKeyboardMarkup(row=2). \
                                           add(InlineKeyboardButton('Предыдущее⬅', callback_data=f'pred {k}')). \
                                           add(InlineKeyboardButton(f'Добавить в корзину 🛒 {drugie_tovary[1]}',
                                                                    callback_data=f'zakk {k}')))
        else:
            await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                           caption=f"{l}\n Описание: {read_zak_VSE[1]}\n Цена: {read_zak_VSE[2]} руб",
                                           reply_markup=InlineKeyboardMarkup(row=2). \
                                           row(InlineKeyboardButton('Предыдущее⬅', callback_data=f'pred {k}'),
                                               InlineKeyboardButton('Следующее➡', callback_data=f'sled {k}')). \
                                           add(InlineKeyboardButton(f'Добавить в корзину 🛒 {drugie_tovary[1]}',
                                                                    callback_data=f'zakk {k}')))
        await sql_delete_zakaz(l, uid)



@dp.callback_query_handler(Text(startswith="delete_zakk "))
async def delete_zakk(call: types.CallbackQuery):
    uid = call.from_user.id
    k = call.data.replace("delete_zakk ", "")
    k = int(k)
    drugie_tovary = await sql_read_drugie_tovary()
    v = len(drugie_tovary)
    drugie_tovary = drugie_tovary[k]
    p = drugie_tovary[1]
    l = drugie_tovary[1]
    l = ' ' + l
    await sql_delete_zakaz(p, uid)
    await call.answer(text=f'{p} удалено из корзины.', show_alert=True)
    read_zak_VSE = await sql_read_VSE_1(p)
    if read_zak_VSE is None:
        read_zak_VSE = await sql_read_VSE_2(p)
    if read_zak_VSE is None:
        read_zak_VSE = await sql_read_VSE_3(p)
    if read_zak_VSE is None:
        read_zak_VSE = await sql_read_VSE_4(p)

    if k == 0:
        await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                       caption=f"{p}\n Описание: {read_zak_VSE[1]}\n Цена: {read_zak_VSE[2]} руб",
                                       reply_markup=InlineKeyboardMarkup(row=2). \
                                       add(InlineKeyboardButton('Следующее➡', callback_data=f'sled {k}')). \
                                       add(InlineKeyboardButton(f'Добавить в корзину 🛒 {drugie_tovary[1]}',
                                                                callback_data=f'zakk {k}')))
    elif k == v-1:
        await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                       caption=f"{p}\n Описание: {read_zak_VSE[1]}\n Цена: {read_zak_VSE[2]} руб",
                                       reply_markup=InlineKeyboardMarkup(row=2). \
                                       row(InlineKeyboardButton('⬅Предыдущее', callback_data=f'pred {k}')). \
                                       add(InlineKeyboardButton(f'Добавить в корзину 🛒 {drugie_tovary[1]}',
                                                                callback_data=f'zakk {k}')))
    else:
        await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                       caption=f"{p}\n Описание: {read_zak_VSE[1]}\n Цена: {read_zak_VSE[2]} руб",
                                       reply_markup=InlineKeyboardMarkup(row=2). \
                                       row(InlineKeyboardButton('Предыдущее⬅', callback_data=f'pred {k}'),
                                           InlineKeyboardButton('Следующее➡', callback_data=f'sled {k}')). \
                                       add(InlineKeyboardButton(f'Добавить в корзину 🛒 {drugie_tovary[1]}',
                                                                callback_data=f'zakk {k}')))
    await sql_delete_zakaz(l, uid)






# Ответ на кнопку заказать
@dp.callback_query_handler(Text(startswith="zak "))
async def zak_colback(call: types.CallbackQuery, state: FSMContext):
    await call.answer(text=f'Добавленно в корзину')
    uid = call.from_user.id
    p=call.data.replace("zak ", "")
    read_price = await sql_read_price(p)
    if read_price is None:
        read_price = await sql_read_price_roli(p)
    if read_price is None:
        read_price = await sql_read_price_napitky(p)
    read_price_base = read_price[0]
    l = call.data.replace("zak", "")
    yest = await sql_read_zak_prov(uid,l)
    if yest is None:
        async with state.proxy() as data:
            data['id'] = call.from_user.id
            data['menu'] = call.data.replace("zak", "")
            data['price'] = read_price_base
            data['kol_vo'] = '1'
        await sql_add_command_zak(state)
        await state.finish()
        read_zak_VSE = await sql_read_VSE_1(p)
        if read_zak_VSE is None:
            read_zak_VSE = await sql_read_VSE_2(p)
        if read_zak_VSE is None:
            read_zak_VSE = await sql_read_VSE_3(p)
        if read_zak_VSE is None:
            read_zak_VSE = await sql_read_VSE_4(p)

        await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                       caption=f"{l}\n Цена: {read_price[0]} руб\n Количество: 1",
                                       reply_markup=InlineKeyboardMarkup(row=2). \
                                       add(InlineKeyboardButton(f'Удалить из корзины {l} ❌',
                                                                callback_data=f'delete_zak{l}')). \
                                       row(InlineKeyboardButton('Добавить ➕', callback_data=f'dobavitt{l}'),
                                           InlineKeyboardButton('Убрать ➖', callback_data=f'ubratt{l}')))
    else:
        read_zak_kol_vo = await sql_read_zak_kol_vo(uid, l)
        a = read_zak_kol_vo[0]
        a = int(a)
        await state.finish()
        read_zak_VSE = await sql_read_VSE_1(p)
        if read_zak_VSE is None:
            read_zak_VSE = await sql_read_VSE_2(p)
        if read_zak_VSE is None:
            read_zak_VSE = await sql_read_VSE_3(p)
        if read_zak_VSE is None:
            read_zak_VSE = await sql_read_VSE_4(p)
        await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                       caption=f"{l}\n Цена: {read_price[0]} руб\n Количество: {a}",
                                       reply_markup=InlineKeyboardMarkup(row=2). \
                                       add(InlineKeyboardButton(f'Удалить из корзины {l} ❌',
                                                                callback_data=f'delete_zak{l}')). \
                                       row(InlineKeyboardButton('Добавить ➕', callback_data=f'dobavitt{l}'),
                                           InlineKeyboardButton('Убрать ➖', callback_data=f'ubratt{l}')))
        await call.answer(text=f'Добавленно в корзину')




@dp.callback_query_handler(Text(startswith="ubratt "))
async def kol_vo_zak_new(call: types.CallbackQuery):
    await call.answer(text=f'Убрано')
    uid = call.from_user.id
    l = call.data.replace("ubratt", "")
    p = call.data.replace("ubratt ", "")
    read_zak_kol_vo = await sql_read_zak_kol_vo(uid,l)
    a = int(read_zak_kol_vo[0])
    a = a-1
    if a > 0:
        read_price = await sql_read_price(p)
        if read_price is None:
            read_price = await sql_read_price_roli(p)
        if read_price is None:
            read_price = await sql_read_price_napitky(p)
        await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                       caption=f"{l}\n Цена: {read_price[0]} руб\n Количество: {a}",
                                       reply_markup=InlineKeyboardMarkup(row=2). \
                                       add(InlineKeyboardButton(f'Удалить из корзины {l} ❌',
                                                                callback_data=f'delete_zak{l}')). \
                                       row(InlineKeyboardButton('Добавить ➕', callback_data=f'dobavitt{l}'),
                                           InlineKeyboardButton('Убрать ➖', callback_data=f'ubratt{l}')))

        await sql_update_kol_dop(a, uid, l)
    else:
        read_zak_VSE = await sql_read_VSE_1(p)
        if read_zak_VSE is None:
            read_zak_VSE = await sql_read_VSE_2(p)
        if read_zak_VSE is None:
            read_zak_VSE = await sql_read_VSE_3(p)


        await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                       caption=f"{l}\n Описание: {read_zak_VSE[1]}\n Цена: {read_zak_VSE[2]} руб",
                                       reply_markup=InlineKeyboardMarkup(row=2). \
                                       add(InlineKeyboardButton(f'Добавить в корзину 🛒 {l}',
                                                                callback_data=f'zak{l}')))
        await sql_delete_zakaz(l, uid)




@dp.callback_query_handler(Text(startswith="dobavitt "))
async def kol_vo_zak_new(call: types.CallbackQuery):
    await call.answer(text=f'добавленно')
    uid = call.from_user.id
    l = call.data.replace("dobavitt", "")
    p = call.data.replace("dobavitt ", "")
    read_zak_kol_vo = await sql_read_zak_kol_vo(uid,l)
    a = int(read_zak_kol_vo[0])
    a = a+1
    read_price = await sql_read_price(p)
    if read_price is None:
        read_price = await sql_read_price_roli(p)
    if read_price is None:
        read_price = await sql_read_price_napitky(p)

    await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                   caption=f"{l}\n Цена: {read_price[0]} руб\n Количество: {a}",
                                   reply_markup=InlineKeyboardMarkup(row=2). \
                                   add(InlineKeyboardButton(f'Удалить из корзины {l} ❌',
                                                                callback_data=f'delete_zak{l}')). \
                                       row(InlineKeyboardButton('Добавить ➕', callback_data=f'dobavitt{l}'),
                                           InlineKeyboardButton('Убрать ➖', callback_data=f'ubratt{l}')))

    await sql_update_kol_dop(a, uid, l)


@dp.callback_query_handler(Text(startswith="delete_zak "))
async def delete_zak(call: types.CallbackQuery):
    uid = call.from_user.id
    l = call.data.replace("delete_zak", "")
    p = call.data.replace("delete_zak ", "")
    await sql_delete_zakaz(p, uid)
    await call.answer(text=f'{p} удалено из корзины.', show_alert=True)
    read_zak_VSE = await sql_read_VSE_1(p)
    if read_zak_VSE is None:
        read_zak_VSE = await sql_read_VSE_2(p)
    if read_zak_VSE is None:
        read_zak_VSE = await sql_read_VSE_3(p)

    await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                   caption=f"{p}\n Описание: {read_zak_VSE[1]}\n Цена: {read_zak_VSE[2]} руб",
                                   reply_markup=InlineKeyboardMarkup(row=2). \
                                   add(InlineKeyboardButton(f'Добавить в корзину 🛒 {l}',
                                                            callback_data=f'zak{l}')))
    await sql_delete_zakaz(l, uid)


class FSMklient_ofr(StatesGroup):
    namee = State()
    dost = State()
    local = State()
    number = State()
    pay = State()
    chekout = State()
    pay_posl_vibor = State()


@dp.message_handler(state=FSMklient_ofr.namee)
async def load_namee(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['id'] = message.from_user.id
        data['namee'] = message.text
    await FSMklient_ofr.dost.set()
    await message.reply('Выбери способ доставки', reply_markup=InlineKeyboardMarkup(row=1). \
                                    add(InlineKeyboardButton('Самовывоз 📦', callback_data=f'Samovivoz')). \
                                    add(InlineKeyboardButton('Доставка по адресу 📬', callback_data=f'Dost_po_adr')))



@dp.callback_query_handler(Text(startswith="Samovivoz"), state=FSMklient_ofr.dost)
async def dost(call: types.CallbackQuery, state: FSMContext):
    await call.answer(text=f'Ок')
    async with state.proxy() as data:
        data['local'] = 'Самовывоз'
    await FSMklient_ofr.number.set()
    await bot.send_message(call.message.chat.id, 'Введите свой номер телефона 📱\n'
                        'Пример ввода: +7 999 999 99 99', reply_markup=kb_client_number)




@dp.callback_query_handler(Text(startswith="Dost_po_adr"), state=FSMklient_ofr.dost)
async def dost_1(call: types.CallbackQuery):
    await call.answer(text=f'Ок')
    await FSMklient_ofr.local.set()
    await bot.send_message(call.message.chat.id, 'Теперь введи свой адрес🏕 или отправь локацию 📍', reply_markup=kb_client_location)




@dp.message_handler(state=FSMklient_ofr.local)
async def load_local(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['local'] = message.text
    await FSMklient_ofr.number.set()
    await message.reply('Введите свой номер телефона 📱\n'
                        'Пример ввода: +7 999 999 99 99', reply_markup=kb_client_number)



@dp.message_handler(content_types=['location'],state=FSMklient_ofr.local)
async def load_local(message: types.Message, state: FSMContext):
    uid = message.from_user.id
    latitude = message.location.latitude
    longitude = message.location.longitude
    await location_zapis(uid, latitude, longitude)
    async with state.proxy() as data:
        data['local'] = 'Локация отправленна геопозицией'
    await FSMklient_ofr.number.set()
    await message.reply('Введите свой номер телефона 📱\n'
                        'Пример ввода: +7 999 999 99 99', reply_markup=kb_client_number)



@dp.message_handler(content_types=['contact'], state=FSMklient_ofr.number)
async def load_number(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['number'] = message.contact.phone_number
    await FSMklient_ofr.pay.set()
    await message.reply(text='Выберите способ оплаты 💰', reply_markup=InlineKeyboardMarkup(row_width=2).\
                        add(InlineKeyboardButton(f'Оплатить заказ онлайн 💳', callback_data=f'oplat_1 ')).add(
        InlineKeyboardButton(f'Оплатить заказ при получении 💵', callback_data=f'oplat_2 ')))


@dp.message_handler(state=FSMklient_ofr.number)
async def load_number(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['number'] = message.text
    await FSMklient_ofr.pay.set()
    await message.reply(text='Выберите способ оплаты 💰', reply_markup=InlineKeyboardMarkup(row_width=2). \
                        add(InlineKeyboardButton(f'Оплатить заказ онлайн 💳', callback_data=f'oplat_1 ')).add(
        InlineKeyboardButton(f'Оплатить заказ при получении 💵', callback_data=f'oplat_2 ')))


# при нажатии на "оплатить онлайн" высылается счет на оплату
@dp.callback_query_handler(Text(startswith="oplat_1 "), state=FSMklient_ofr.pay)
async def oplat_colback_oplat_1(call: types.CallbackQuery, state: FSMContext):
    await call.answer(text=f'Оплаите онлайн')
    uid = call.from_user.id
    read_zak = await sql_read_zak(uid)

    def read_zak_str():
        read_zak_list = ''
        for r in read_zak:
            read_zak_list += f' Название: {r[0]}\n Количество: {r[2]}\n Цена:{r[1]} руб\n'
        return read_zak_list

    def podschet():
        sum = 0
        for r in read_zak:
            a = float(r[1])
            b = float(r[2])
            sum += a * b
            sum = int(sum)
        sum = int(str(sum) + "00")
        if sum > 100000:
            sum = 50000
        return sum

    k = podschet()
    ss = k
    await bot.send_invoice(chat_id = call.from_user.id,
                           title= 'Заказ',
                           description= f'Заказ: {read_zak_str()} ',
                           payload='sub_zak',
                           provider_token=YOOTOKEN,
                           currency="RUB",
                           start_parameter='zak',
                           prices = [LabeledPrice(label = "Руб", amount = ss)])
    async with state.proxy() as data:
        data['pay'] = 'Оплачено онлайн '
    await FSMklient_ofr.chekout.set()

# подтверждение наличия товара
@dp.pre_checkout_query_handler(state=FSMklient_ofr.chekout)
async def chekout(pre_checkout_query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok = True)
    await FSMklient_ofr.pay_posl_vibor.set()

# подтверждение оплаты и Отправка записанного в чат
@dp.message_handler(content_types=ContentTypes.SUCCESSFUL_PAYMENT, state=FSMklient_ofr.pay_posl_vibor)
async def porses_pay(message: types.Message, state: FSMContext):
    if message.successful_payment.invoice_payload == 'sub_zak':
        await bot.send_message(message.from_user.id, 'Заказ оплачен и будет доставлен', reply_markup=kb_client_plus)
        await sql_add_command_zak_ofr(state)
        chat_id = ID
        uid = message.from_user.id
        read_zak_ofr = await sql_read_zak_ofr(uid)
        read_zak = await sql_read_zak(uid)

        def read_zak_str():
            read_zak_list = ''
            for r in read_zak:
                read_zak_list += f'Название: {r[0]}\nКоличество {r[2]}\n'
            return read_zak_list

        def podschet():
            sum = 0
            for r in read_zak:
                a = float(r[1])
                b = float(r[2])
                sum += a * b
            return sum

        location = await sql_location_read(uid)
        if location is None:
            await sql_delete_zak(uid)
            await sql_delete_zak_ofr(uid)
            kont_teleg = InlineKeyboardMarkup()
            btn = InlineKeyboardButton(
                text=f'telegram заказчика {message.from_user.first_name} {message.from_user.last_name}',
                url=f"tg://user?id={uid}")
            kont_teleg.add(btn)
            for ret in read_zak_ofr:
                await bot.send_message(chat_id, f'Новый заказ:\n'
                                                f'{read_zak_str()}\n'
                                                f'Имя: {ret[0]}\nАдрес доставки: {ret[1]}\n'
                                                f'Номер телефона:{ret[2]}\nОплата: {ret[3]}\n'
                                                f'Итоговая сумма: {podschet()} руб', reply_markup=kont_teleg)
            await state.finish()
        else:
            latitude = location[0]
            longitude = location[1]
            await sql_delete_zak(uid)
            await sql_delete_location(uid)
            await sql_delete_zak_ofr(uid)
            kont_teleg = InlineKeyboardMarkup()
            btn = InlineKeyboardButton(
                text=f'telegram заказчика {message.from_user.first_name} {message.from_user.last_name}',
                url=f"tg://user?id={uid}")
            btn_locl_zak = InlineKeyboardButton(text=f'Локация заказчика',
                                                url=f"http://maps.google.com/?q={latitude},{longitude}")
            kont_teleg.add(btn).add(btn_locl_zak)
            for ret in read_zak_ofr:
                await bot.send_message(chat_id, f'Новый заказ:\n'
                                                f'{read_zak_str()}\n'
                                                f'Имя: {ret[0]}\nАдрес доставки: {ret[1]}\n'
                                                f'Номер телефона:{ret[2]}\nОплата: {ret[3]}\n'
                                                f'Итоговая сумма: {podschet()} руб', reply_markup=kont_teleg)

            await state.finish()
    else:
        await bot.send_message(message.from_user.id, 'Заказ  не оплачен')



# Отправка записанного в чат
@dp.callback_query_handler(Text(startswith="oplat_2 "), state=FSMklient_ofr.pay)
async def oplat_colback_oplat_1(call: types.CallbackQuery, state: FSMContext):
    await call.answer(text=f'Оплата будет произведена при получении заказа', show_alert=True)
    await bot.send_message(call.message.chat.id, 'Спасибо, заказ будет доставлен', reply_markup=kb_client_plus)
    async with state.proxy() as data:
        data['pay'] = 'Оплата будет произведена при получении заказа'
    await sql_add_command_zak_ofr(state)
    chat_id = ID
    uid = call.from_user.id
    read_zak_ofr = await sql_read_zak_ofr(uid)
    read_zak = await sql_read_zak(uid)
    def read_zak_str():
        read_zak_list = ''
        for r in read_zak:
            read_zak_list += f'Название: {r[0]}\nКоличество {r[2]}\n'
        return read_zak_list
    def podschet():
        sum = 0
        for r in read_zak:
            a = float(r[1])
            b = float(r[2])
            sum += a * b
        return sum

    location = await sql_location_read(uid)
    if location is None:
        await sql_delete_zak(uid)
        await sql_delete_zak_ofr(uid)
        kont_teleg = InlineKeyboardMarkup()
        btn = InlineKeyboardButton(text=f'telegram заказчика {call.from_user.first_name} {call.from_user.last_name}', url=f"tg://user?id={uid}")
        kont_teleg.add(btn)
        for ret in read_zak_ofr:
                await bot.send_message(chat_id, f'Новый заказ:\n'
                                            f'{read_zak_str()}\n'
                                            f'Имя: {ret[0]}\nАдрес доставки: {ret[1]}\n'
                                            f'Номер телефона:{ret[2]}\nОплата: {ret[3]}\n'
                                            f'Итоговая сумма: {podschet()} руб', reply_markup=kont_teleg)
        await state.finish()
    else:
        latitude = location[0]
        longitude = location[1]
        await sql_delete_zak(uid)
        await sql_delete_location(uid)
        await sql_delete_zak_ofr(uid)
        kont_teleg = InlineKeyboardMarkup()
        btn = InlineKeyboardButton(text=f'telegram заказчика {call.from_user.first_name} {call.from_user.last_name}',
                                   url=f"tg://user?id={uid}")
        btn_locl_zak = InlineKeyboardButton(text=f'Локация заказчика',
                                   url=f"http://maps.google.com/?q={latitude},{longitude}")
        kont_teleg.add(btn).add(btn_locl_zak)
        for ret in read_zak_ofr:
            await bot.send_message(chat_id, f'Новый заказ:\n'
                                            f'{read_zak_str()}\n'
                                            f'Имя: {ret[0]}\nАдрес доставки: {ret[1]}\n'
                                            f'Номер телефона:{ret[2]}\nОплата: {ret[3]}\n'
                                            f'Итоговая сумма: {podschet()} руб', reply_markup=kont_teleg)

        await state.finish()


async def chack_date():

    while True:
        d = datetime.today()
        d1 = d.strftime("%Y-%m-%d")
        t1 = d.strftime("%H:%M")

        napominanie_read = await sql_napominanie_read()
        if napominanie_read is None:
            await asyncio.sleep(60)
        else:
            for r in napominanie_read:
                chat_id = r[0]
                tmdal = r[2].replace(":", "")
                tmdal =  tuple(tmdal)
                tmm1 = (tmdal[0:2])
                tmd1= f'{tmm1[0]}{tmm1[1]}'
                tmd1 = int(tmd1)
                tmd1 = tmd1- 3
                tmm2 = (tmdal[2:4])
                tmd2 = f'{tmm2[0]}{tmm2[1]}'
                tmd2 = int(tmd2)
                da1 = datetime(2023, 6, 8, tmd1, tmd2)
                tm = da1.strftime("%H:%M")
                if r[1] <= d1 and tm <= t1:
                    await bot.send_message(chat_id, f'Напоминание: {d1} {r[2]}\n '
                                                    f'{r[3]}')
                    uid = r[0]
                    data = r[1]
                    time = r[2]
                    await sql_delete_napominanie(uid,  data, time)
                else:
                    print('not')
            await asyncio.sleep(60)







executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
