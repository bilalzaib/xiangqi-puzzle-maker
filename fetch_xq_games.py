import csv

import requests

# --------------------------------------------------------------------
# Required: Get admin JWT from browser cookies or storage data
JWT = 'admin-JWT'
# Required: Add a valid username fromm xiangqi.com
user = 'zaib'
# Optional: Mention, how many games should script fetch of a given user
DEFAULT_TOTAL_GAMES = 30
# --------------------------------------------------------------------

BASE_URL = 'https://api.play.xiangqi.com'
REQUEST_URL_T = BASE_URL + '/api/users/games/{}'
GAMES_PER_PAGE = 12


def fetch_games(username, total_games=DEFAULT_TOTAL_GAMES):
    headers = {'Authorization': 'Bearer {}'.format(JWT)}
    url = REQUEST_URL_T.format(username)

    print(f'Fetching games of {username}. Please wait...')
    games = []
    # TODO: Get total available games of a user
    for page in range(1, (total_games // GAMES_PER_PAGE) + 2):
        params = {'page': page}
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code != 200:
                raise Exception(
                    'Invalid Response, code: {}, error: {}'.format(response.status_code, response.text))

            games += response.json()['games']
        except Exception as exp:
            print('EXCEPTION ==> ', str(exp))

    return games


games = fetch_games(user)

print(f'Games are saved to {user}.csv')
with open(f'{user}.csv', 'w', newline='') as csvfile:
    fieldnames = ['id', 'rplayer', 'bplayer', 'moves_count', 'moves']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for game in games:
        if game['moves_count'] < 11 or not game.get('uci_moves'):
            continue

        row = {
            'id': game['id'],
            'rplayer': game['rplayer']['username'],
            'bplayer': game['bplayer']['username'],
            'moves_count': game['moves_count'],
            'moves': game['uci_moves'],
        }
        writer.writerow(row)
