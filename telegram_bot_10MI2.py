from telegram.ext import Updater, CommandHandler, MessageHandler, ConversationHandler, Filters
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
import numpy as np
from PIL import Image
import requests
from io import BytesIO


grayscale_levels_extended = "$@B%8&WM#*oa" \
                            "hkbdpqwmZO0Q" \
                            "LCJUYXzcvunx" \
                            "rjft/\\|()1{" \
                            "}[]?-_+~<>i!" \
                            "lI;:,\"^`'. "  # 70 levels
grayscale_levels = "@%#*+=-:. "  # 10 levels


def start(bot, updater, chat_data):
    chat_data['levels'] = 10
    markup = ReplyKeyboardMarkup([['10 levels of gray'], ['70 levels of gray']],
                                 one_time_keyboard=False)
    chat_data['markup'] = markup
    updater.message.reply_text("Send me a picture and i will gladly convert it to ASCII!\n"
                               "10 levels of gray are set by default.",
                               reply_markup=markup)
    return 1


def stop(bot, updater, chat_data):
    markup = ReplyKeyboardMarkup([['/start']], one_time_keyboard=True)
    updater.message.reply_text('Until we meet again!', reply_markup=markup)
    return ConversationHandler.END



def choose_levels(bot, updater, chat_data):
    if updater.message.text == '70 levels of gray':
        chat_data['levels'] = 70
        updater.message.reply_text("Now there are 70 levels of gray.",
                                   reply_markup=chat_data['markup'])
    elif updater.message.text == '10 levels of gray':
        chat_data['levels'] = 10
        updater.message.reply_text("Now there are 10 levels of gray.",
                                   reply_markup=chat_data['markup'])

    return 1



def picture_to_ascii(bot, updater, chat_data):
    try:
        file = bot.getFile(updater.message.photo[-1].file_id)

        response = requests.get(file["file_path"])
        image = Image.open(BytesIO(response.content)).convert('L')
        # updater.message.reply_text(str(image))

        # cols = image.size[0]
        cols = 120
        width, height = image.size[0], image.size[1]
        w = width / cols  # w shows how many pixels of the original picture a symbol will resemble in width
        h = w / 0.43  # h shows how many pixels of the original picture a symbol will resemble in height
        rows = int(height / h)

        ascii_image = []
        for i in range(rows):
            y1 = int(i * h)
            y2 = int((i + 1) * h)
            if i == rows - 1:
                y2 = height
            current_row = ""

            for j in range(cols):
                x1 = int(j * w)
                x2 = int((j + 1) * w)
                if j == cols - 1:
                    x2 = width
                area_for_current_symbol = image.crop((x1, y1, x2, y2))
                average = int(get_average_brightness_level(area_for_current_symbol))
                grayscale_value = int((average / 255) * (chat_data['levels'] - 1))

                current_row += (grayscale_levels if chat_data['levels'] == 10 else grayscale_levels_extended)[grayscale_value]
            ascii_image.append(current_row + "\n")
        with open(str(updater.message.chat.id) + '.txt', 'w') as ascii_ready:
            ascii_ready.writelines(ascii_image)
        bot.sendDocument(updater.message.chat.id, document=open(str(updater.message.chat.id) + '.txt', 'rb'))
        # updater.message.reply_text('\n'.join(ascii_image))
    except Exception as e:
        updater.message.reply_text(str(e))

    return 1


def get_average_brightness_level(image):
    im = np.array(image)
    w, h = im.shape
    return np.average(im.reshape(w * h))


def main():
    updater = Updater("839428088:AAFB7IVAZAuz_2YXPjStDd5Qu4OefhKh86A")
    dp = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start, pass_chat_data=True)],

        states={
            1: [MessageHandler(Filters.text, choose_levels, pass_chat_data=True),
            MessageHandler(Filters.photo, picture_to_ascii, pass_chat_data=True)],
        },

        fallbacks=[CommandHandler('stop', stop, pass_chat_data=True)]
    )
    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
