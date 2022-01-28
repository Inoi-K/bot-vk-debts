import vk_api, random, sqlite3
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

# region CONSTANTS
vk_session = vk_api.VkApi(token='TOKEN')
longpoll = VkBotLongPoll(vk_session, SESSION)
vk = vk_session.get_api()
names, db, n = [], '', 0
who, whom, act, cell, sign, value = '', '', 0, None, None, None
KIS = 2000000001
KAV = 2000000002
TEST = 2000000003
TEST2 = 2000000004
# endregion

# TABLE
# c.execute("CREATE TABLE users (who text, whom text, debt int)")
# for i in range(n):
#     for j in range(n):
#         c.execute("INSERT INTO users VALUES ('{}', 'to {}', 0)".format(names[i], names[j]))
# conn.commit()


def random_id():
    return random.randint(0, 1e6)


def keyboard_purchase():
    keyboard = VkKeyboard(one_time=True)

    for i in range(n):
        keyboard.add_button('{}'.format(names[i].capitalize()))
    keyboard.add_line()

    keyboard.add_button('Menu', color=VkKeyboardColor.PRIMARY)

    keyboard = keyboard.get_keyboard()
    return keyboard


def keyboard_debt():
    keyboard = VkKeyboard(one_time=False)

    val = [[0] * n for i in range(n)]
    c.execute("SELECT debt FROM users_{}".format(db))
    mas = c.fetchall()
    for i in range(n):
        for j in range(n):
            val[i][j] = mas[n * i + j][0]

    keyboard.add_button('Buy', color=VkKeyboardColor.PRIMARY)
    for i in range(n):
        keyboard.add_button('to {}'.format(names[i].capitalize()))
    keyboard.add_line()

    for i in range(n):
        keyboard.add_button('{}'.format(names[i].capitalize()))
        for j in range(n):
            keyboard.add_button(str(val[i][j]))
        keyboard.add_line()

    keyboard.add_button('Add', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('Reduce', color=VkKeyboardColor.NEGATIVE)

    keyboard = keyboard.get_keyboard()
    return keyboard


def upd(val):
    global cell
    c.execute("SELECT debt FROM users_{} WHERE who = '{}' AND whom = '{}'".format(db, who, whom))
    cell = c.fetchone()[0]
    upd = cell + sign * val
    c.execute("SELECT debt FROM users_{} WHERE who = '{}' AND whom = '{}'".format(db, whom[3:],
                                                                                  'to ' + who))
    checker = c.fetchone()[0]
    if checker:
        c.execute("UPDATE users_{} SET debt = '{}' WHERE who = '{}' AND whom = '{}'".format(db,
                                                                                            max(0, checker - upd),
                                                                                            whom[3:], 'to ' + who))
        if checker < upd:
            c.execute("UPDATE users_{} SET debt = '{}' WHERE who = '{}' AND whom = '{}'".format(
                db, upd - checker, who, whom))
    else:
        c.execute("UPDATE users_{} SET debt = '{}' WHERE who = '{}' AND whom = '{}'".format(db,
                                                                                            max(0, upd), who, whom))
        if upd < 0:
            c.execute("UPDATE users_{} SET debt = '{}' WHERE who = '{}' AND whom = '{}'".format(db,
                                                                                                abs(upd), whom[3:],
                                                                                                'to ' + who))

    conn.commit()
    msg('Update successful', keyboard_debt())
    set_default()


def purchase(val):
    global value
    value = round(val / n)

    c.execute("SELECT debt FROM users_{} WHERE who = '{}'".format(db, who))
    who_owe_whom = c.fetchall()  # HORIZONTAL
    c.execute("SELECT debt FROM users_{} WHERE whom = '{}'".format(db, 'to ' + who))
    whom_owe_who = c.fetchall()  # VERTICAL

    for i in range(n):
        # VERTICAL
        c.execute("UPDATE users_{} SET debt = '{}' WHERE who = '{}' AND whom = '{}'".format(db,
                                                                                            max(0, whom_owe_who[i][0] -
                                                                                                who_owe_whom[i][
                                                                                                    0] + value),
                                                                                            names[i], 'to ' + who))
        # HORIZONTAL
        c.execute("UPDATE users_{} SET debt = '{}' WHERE who = '{}' AND whom = '{}'".format(db,
                                                                                            max(0, who_owe_whom[i][
                                                                                                0] - value), who,
                                                                                            'to ' + names[i]))
    conn.commit()

    msg('Update successful', keyboard_debt())
    set_default()


def set_default():
    global who, whom, act, sign, value, cell
    who, whom, act, cell, sign, value = '', '', 0, None, None, None


def check_who_whom():
    global who, whom
    if who == whom[3:]:
        set_default()
        msg('You owe nothing to yourself', keyboard_debt())
    else:
        c.execute("SELECT debt FROM users_{} WHERE who = '{}' AND whom = '{}'".format(db, who, whom))
        global cell, value
        cell = c.fetchone()[0]
        answer()


def answer():
    global cell, sign, value
    if cell is not None and sign and value:
        upd(value)
    elif cell is not None:
        if sign:
            msg('How many rubles?', keyboard_debt())
        elif value:
            msg('What to do?', keyboard_debt())
    elif sign and value:
        msg('Please specify the persons', keyboard_debt())


def msg(message, keyboard=None):
    vk.messages.send(
        peer_id=event.obj.message['peer_id'],
        message=message,
        keyboard=keyboard,
        random_id=0
    )


def upd_cell(num):
    global cell, who, whom
    cell = num
    c.execute("SELECT who, whom FROM users_{} WHERE debt = {}".format(db, number))
    ans = c.fetchall()
    if len(ans) == 1:
        who, whom = ans[0][0], ans[0][1]
        answer()
    else:
        msg('Please specify the persons', keyboard_debt())


def upd_value(num):
    global value
    value = num
    answer()


while True:
    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:

            # CONVERSATION ID
            group_id = event.obj.message['peer_id']
            if group_id == KIS:
                names, db = ['kirill', 'ilya', 'sergei'], 'kis'
            elif group_id == KAV:
                names, db = ['kirill', 'anton', 'vadim'], 'kav'
            elif group_id == TEST:
                names, db = ['kirill', 'biba', 'boba'], 'test'
            elif group_id == TEST2:
                names, db = ['kirill', 'sinok', 'papa'], 'test2'
            conn = sqlite3.connect("users_{}.db".format(db))
            c = conn.cursor()
            n = len(names)

            text_t, corrected = event.obj.message['text'].lower(), False
            # TEXT CORRECTING
            if text_t.startswith('[club192702895'):
                corrected = True
                if text_t[15] == 'b':
                    text_t = text_t[24:]
                elif text_t[15] == '@':
                    text_t = text_t[31:]
            text = text_t

            # ACTION FROM MENU
            if text == 'debt':
                act = 0
                msg('Your debts', keyboard_debt())
            elif text == 'purchase' or text == 'buy':
                act = 1
                msg('Who?', keyboard_purchase())

            # FIRST PERSON
            elif text in names:
                who = text
                if whom != '':
                    check_who_whom()
                if act == 1:
                    msg('How many rubles?')

            # SECOND PERSON
            elif text.startswith('to ') and text[3:] in names:
                whom = text
                if who != '':
                    check_who_whom()

            # ACTION IN DEBT
            elif text == 'add' or text == 'reduce':
                if text == 'add':
                    sign = 1
                else:
                    sign = -1
                answer()

            # NUMBER CHECK
            elif text.isdigit():
                number = int(text)
                if act == 1:
                    purchase(number)
                else:
                    if corrected:
                        if cell is not None:
                            if value:
                                answer()
                            else:
                                upd_value(number)
                        else:
                            upd_cell(number)
                    else:
                        if value:
                            if cell is not None:
                                answer()
                            else:
                                upd_cell(number)
                        else:
                            upd_value(number)

            # BOT INVOKE
            elif text == 'bot' or text == 'menu':
                set_default()
                vk.messages.send(
                    peer_id=event.obj.message['peer_id'],
                    message='Look',
                    keyboard=open("keyboard_menu.json", "r", encoding="UTF-8").read(),
                    random_id=0
                )
