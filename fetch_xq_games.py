import csv

import requests

JWT = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTY3NzEwMTI1NCwianRpIjoiMmYyNmFmYjUtNmM1MC00OWZhLWIwODctNTVjODUyMzg1NDA1IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6NDE2OSwibmJmIjoxNjc3MTAxMjU0LCJleHAiOjE2NzgxMzgwNTR9._7nhRcZnsFKdiOuyMPf62XaqkyVzgqtXn9Tof-Fj5dM'
BASE_URL = 'https://api.play.xiangqi.com'
REQUEST_URL_T = BASE_URL + '/api/users/games/{}'

DEFAULT_TOTAL_GAMES = 30
GAMES_PER_PAGE = 12


def fetch_games(username, total_games=DEFAULT_TOTAL_GAMES):
    headers = {'Authorization': 'Bearer {}'.format(JWT)}
    url = REQUEST_URL_T.format(username)

    games = []
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


user = 'zaib'
games = fetch_games(user, total_games=15)

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
