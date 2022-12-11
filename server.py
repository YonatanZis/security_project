import api_utils as utils
import time
import json

available_bots_credentials=[
    {
        "key":'1a309a5b89a0715f0c40aaa138c871b4', 
        "token": '1fa51a67d1a601e39747812cd96634fd146e5554faa627ba9ca90fa9c137e021'},
    {
        "key": '2a45bdaf483bf0e611dbf3e28acfad7a',
        "token": '973e600d2fb08216cca81a86fdfbc9e8a06926307bd336d147b6ffd3655e4565'
    }
    ]
used_bots_credentials=[]

def add_cred_card(list_id):
    utils.create_card(list_id,utils.CRED_ANS_CARD_NAME, available_bots_credentials[0])


#TODO in the future - add encryption
#TODO add blacklist of lists
def check_bootstrap_board():
    lists = utils.get_lists_in_board(utils.BOOTSTRAP_BOARD_ID)
    for list in lists:
        cards = utils.get_cards_in_list(list['id'])
        for card in cards:
            # received an account request
            if card['name'] == utils.CRED_REQ_CARD_NAME:
                add_cred_card(list['id'])


def main():

    check_bootstrap_board()

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

