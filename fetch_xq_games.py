import csv
import time

import requests

# --------------------------------------------------------------------
# Required: Get admin JWT from browser cookies or storage data
JWT = 'admin-JWT'
# Required: Add a valid username fromm xiangqi.com
USERS = ['SeeShuk', 'lemontea', 'MartyJr', 'DavidK', 'maxland', 'ngkaizhe', 'Mann']
# Optional: Mention, how many recent games should be fetched of each user
DEFAULT_TOTAL_GAMES = 150
# --------------------------------------------------------------------

BASE_URL = 'https://api.play.xiangqi.com'
REQUEST_URL_T = BASE_URL + '/api/users/games/{}'
GAMES_PER_PAGE = 12


def fetch_user_games(username, total_games=DEFAULT_TOTAL_GAMES):
    print(f'Fetching games of {username}')

    response = game_request(username)
    if not response:
        return []

    games = parse_games(response)

    for page in range(2, response['total_pages']):
        if len(games) >= total_games:
            break

        time.sleep(0.5)
        print(f'Fetching... page ==> {page}')
        response = game_request(username, page=page)
        if not response:
            print('Something went wrong with the games request')
            break

        games += parse_games(response)

    print(f'Fetched {len(games)} of {username}')
    return games


def game_request(username, page=1):
    try:
        headers = {'Authorization': 'Bearer {}'.format(JWT)}
        url = REQUEST_URL_T.format(username)
        params = {'page': page}
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            raise Exception(
                'Invalid Response, code: {}, error: {}'.format(response.status_code, response.text))

        return response.json()
    except Exception as exp:
        print('EXCEPTION ==> ', str(exp))


def parse_games(res_json):
    games = []
    for game in res_json['games']:
        if not game['end_reason'] or game['moves_count'] < 5:
            continue

        games.append({
            'id': game['id'],
            'rplayer': game['rplayer']['username'],
            'bplayer': game['bplayer']['username'],
            'moves_count': game['moves_count'],
            'moves': game['uci_moves'],
        })

    return games


if __name__ == '__main__':
    file_name = 'out-games.csv'
    with open(file_name, 'w', newline='') as csvfile:
        fieldnames = ['id', 'rplayer', 'bplayer', 'moves_count', 'moves']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        games_count = 0
        for username in USERS:
            games = fetch_user_games(username)
            games_count += len(games)

            for game in games:
                writer.writerow(game)

    print(f'{games_count} saved to {file_name} file')
