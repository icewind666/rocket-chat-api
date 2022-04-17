# -*- coding: utf-8 -*-

import logging
import json
import telegram
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
from RocketChatApi import RocketChatClient


def status(bot, update):
    """
    Returns a message.
    Just a check if bot is alive
    :param bot:
    :param update:
    :return:
    """
    bot.sendMessage(chat_id=update.message.chat_id, text="I'm ok, thank you")


def echo(bot, update):
    """
    Just an ping echo
    :param bot:
    :param update:
    :return:
    """
    mr_url = update.message.text
    if mr_url:
        bot.sendMessage(chat_id=update.message.chat_id, text="echo {}".format(mr_url))
        send_msg_to_rocket(mr_url)


def send_msg_to_rocket(msg):
    try:
        if rocket_client:
            msg_format = "Дамы и господа, Вашему вниманию представляется merge request : {}".format(msg)
            rocket_client.send_room(bot_options["rocketchat_room_id_to_post"], msg_format)
        return True
    except Exception as e:
        logging.error("Error while sending ot rocket: {}".format(str(e)))
        return False


def load_config(config_filename):
    """
    Loads all configuration data from given json filename
    :param config_filename:
    :return: config data if OK - None otherwise
    """
    try:
        with open(config_filename, "r") as f_handle:
            config_data = json.load(f_handle)
        return config_data
    except Exception as e:
        logging.error("Config file is invalid: {}".format(str(e)))
        return None


if __name__ == "__main__":

    # Set basic file logging configuration
    logging.basicConfig(format=u"%(levelname)-8s [%(asctime)s] %(message)s",
                        level=logging.DEBUG, filename="mr_bot.log")

    # Load configuration
    bot_options = load_config("config.json")

    if bot_options is None:
        # no configs. we are done.
        exit(0)

    rocket_client = RocketChatClient(bot_options["rocketchat_url"])
    rocket_client.login(bot_options["bot_rocket_login"], bot_options["bot_rocket_password"])
    
    REQUEST_KWARGS = {
        "proxy_url": bot_options["proxy_url"],
        "urllib3_proxy_kwargs": bot_options["urllib3_proxy_kwargs"]
    }
    
    # Starting telegram updater bot
    bot = telegram.ext.Updater(token=bot_options["telegram_bot_token"], request_kwargs=REQUEST_KWARGS)

    auth_args = {
                    "username": bot_options["urllib3_proxy_kwargs"]["username"],
                    "password": bot_options["urllib3_proxy_kwargs"]["username"]
                }
    tg_proxy_request = telegram.utils.request.Request(proxy_url=bot_options["proxy_url"],
                                                      urllib3_proxy_kwargs=auth_args)

    # Starting bot to send responses in chats
    sendingBot = telegram.Bot(token=bot_options["telegram_bot_token"], request=tg_proxy_request)

    # Get bot message dispatcher
    dispatcher = bot.dispatcher

    # Adding command handlers to bot dispatcher
    status_handler = CommandHandler("status", status)
    dispatcher.add_handler(status_handler)

    # Handle free-test message - sends it to rocket chat room
    echo_handler = MessageHandler(Filters.text, echo)
    dispatcher.add_handler(echo_handler)

    # Tell telegram we are ready to go
    bot.start_polling()
