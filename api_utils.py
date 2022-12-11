import requests
import json

# maybe erase bootstrap
BOOTSTRAP_TOKEN = '0371b95aaa9e16d0089fa4d55d078f5fab508c5af7e2d82a7c57aa6be908778b'
BOOTSTRAP_KEY = '0e0a04d5f73b65a679a0b49f2f62df9a'
BOOTSTRAP_BOARD_ID = '639637edc1f14f01dd74eff6'
TRELLO_URL = 'https://api.trello.com/1/'
ACCOUNT_KEY = ''
ACCOUNT_TOKEN = ''
SUCCESS = 200
CRED_ANS_CARD_NAME = 'new creds'
CRED_REQ_CARD_NAME = 'request for new account'
KEY_TOKEN_SEPERATOR = ':'
IS_BOOTSTRAP = True

#TODO make the utils generic in regards to key,token since server uses many of them


def check_post_response(response):
    if response.status_code != SUCCESS:
        print("error response:")
        print("status code is " + str(response.status_code))
        print(response.text)

# request type is "GET"\"POST"
# function returns the response
def send_request(request_type, url_details,query_parameters={},request_parameters={}):
    url = TRELLO_URL + url_details 
    if IS_BOOTSTRAP:
        query = {
            'key': BOOTSTRAP_KEY,
            'token': BOOTSTRAP_TOKEN
        }
    else:
        query = {
            'key': ACCOUNT_KEY,
            'token': ACCOUNT_TOKEN
        }
    query.update(query_parameters)
    response = requests.request(
        request_type,
        url,
        params=query,
        **request_parameters # fishy
    )
    return response

    
def create_list(list_name, board_id):
    print("creating list "+ list_name)
    url_details = '/lists'
    query_parameters = {
        'name': list_name,
        'idBoard': board_id
    }
    response = send_request('POST',url_details, query_parameters)
    check_post_response(response)

def create_board(board_name):
    url_details = '/boards/'
    query_parameters = {
        'name': board_name
    }
    response = send_request('POST',url_details=url_details,
    query_parameters=query_parameters)
    check_post_response(response)

def create_card(list_id, name, desc=""):
    url_details = '/cards/'
    query_parameters = {
        'name': name,
        'idList': list_id
    }
    if desc != "":
        query_parameters['desc'] = desc
    response = send_request('POST',url_details=url_details,
    query_parameters=query_parameters)
    check_post_response(response)

def get_list_id(list_name, board_id):
    url_details = '/boards/' + board_id + '/lists'
    response = send_request('GET', url_details)
    lists = json.loads(response.text)
    for list in lists:
        if list['name'] == list_name:
            return list['id']
    return None

def get_all_boards():
    url_details = 'members/me/boards/'
    headers = {
        "Accept": "application/json"
    }
    response = send_request('GET', url_details, request_parameters={'headers': headers})
    check_post_response(response)
    return json.loads(response.text)

def get_board(board_id):
    url_details = '/boards/' + board_id
    headers = {
        "Accept": "application/json"
    }
    response = send_request('GET', url_details, request_parameters={'headers': headers})
    check_post_response(response)
    return json.loads(response.text)


def get_list(list_id):
    url_details = '/lists/' + list_id
    response = send_request('GET', url_details)
    check_post_response(response)
    return json.loads(response.text)


def get_card(card_id):
    url_details = '/cards/' + card_id
    response = send_request('GET', url_details)
    check_post_response(response)
    return json.loads(response.text)

def get_cards_in_list(list_id):
    url_details = '/lists/' + list_id + '/cards'
    headers = {
        "Accept": "application/json"
    }
    response = send_request('GET', url_details, request_parameters={'headers':headers})
    check_post_response(response)
    return json.loads(response.text)

def get_lists_in_board(board_id):
    url_details = '/boards/' + board_id + '/lists'
    headers = {
        "Accept": "application/json"
    }
    response = send_request('GET', url_details, request_parameters={'headers':headers})
    check_post_response(response)
    return json.loads(response.text)
    
def get_command_from_card(card_id):
    card = get_card(card_id)
    desc = card['desc']
    return desc

def get_creds_from_card(card_id):
    desc = get_command_from_card(card_id)
    desc_sep = desc.split(KEY_TOKEN_SEPERATOR)
    return desc_sep[0],desc_sep[1]

def archive_list(list_id):
    url_details = '/lists/' + list_id + '/closed'
    response = send_request('POST', url_details)
    check_post_response(response)