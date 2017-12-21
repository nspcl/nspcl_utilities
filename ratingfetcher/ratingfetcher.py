#! python
# -*- coding: utf-8 -*-
""""Retrieves player rating based on defined criteria."""
from datetime import date
from dateutil.relativedelta import relativedelta
from warnings import warn
from operator import itemgetter

from requests import get


__author__ = "Walid Mujahid وليد مجاهد"
__copyright__ = "Copyright 2017, Walid Mujahid وليد مجاهد"
__credits__ = ["Walid Mujahid وليد مجاهد"]
__license__ = "MIT"
__version__ = "0.6.1"
__maintainer__ = "Walid Mujahid وليد مجاهد"
__email__ = "walid.mujahid.dev@gmail.com"
__status__ = "Prototype"


REQUEST_HEADERS = {'User-Agent': 'RatingsFetcher/0.6.1 '
                                 '(Author: Walid Mujahid, '
                                 'Email: walid.mujahid.dev@gmail.com, '
                                 'Chess.com username: walidmujahid)'}


class GamePlay:
    """TODO: Docstring."""
    def __init__(self, username: str, past_months: int=8):
        self.username = username
        self.past_months = past_months

    def has_played_x_number_of_games_of_type(
            self, game_type: str, minimum_number_of_games_played: int):
        game_count = self.count_live_chess_games_of_type(game_type)

        return True if game_count >= minimum_number_of_games_played else False

    @staticmethod
    def is_game_of_type(game: dict, game_type: str):
        """Checks if the game is of a certain type - like 'standard' or 'blitz'.
        """
        if game['time_class'] == game_type:
            return True
        else:
            return False

    def generate_month_range(self):
        today = date.today()
        list_of_months_in_range = []
        custom_number_of_months_ago = today + relativedelta(
            months=-self.past_months)

        while custom_number_of_months_ago <= today:
            list_of_months_in_range.append(custom_number_of_months_ago)
            custom_number_of_months_ago += relativedelta(months=1)

        return list_of_months_in_range

    @staticmethod
    def request_monthly_archive(url: str):
        """Gets monthly archive using url"""
        return get(url, headers=REQUEST_HEADERS).json()['games']

    def get_monthly_archives(self, year: int, month: int):
        """Get a monthly archive for custom year and month."""
        url = f'https://api.chess.com/pub/player/' \
              f'{self.username}/games/{year}/{month:02d}'

        return self.request_monthly_archive(url)

    def get_live_chess_games_of_type(self, game_type: str):
        games_of_type = []

        for dates in self.generate_month_range()[::-1]:
            games = self.get_monthly_archives(dates.year, dates.month)

            for game in games:
                if self.is_game_of_type(game, game_type):
                    games_of_type.append(game)

        return sorted(games_of_type, key=itemgetter('end_time'))

    def count_live_chess_games_of_type(self, game_type: str):
        return len(self.get_live_chess_games_of_type(game_type))


class PlayerCriteria:
    def __init__(self, username: str):
        self.username = username
        self.player_game = GamePlay(self.username)

    def is_member_of_nspcl(self):
        """Returns True if player is a member of the NSPCL."""
        nspcl_members = 'https://api.chess.com/pub/club/' \
                        'not-so-pro-chess-league/members'

        response = get(nspcl_members, headers=REQUEST_HEADERS).json()
        members = list(set(response['weekly'] + response['monthly'] +
                           response['all_time']))

        if self.username.lower() in members:
            return True
        else:
            return False

    def has_played_minimum_standard_games(self, minimum_number=10):
        return self.player_game.has_played_x_number_of_games_of_type(
            'standard', minimum_number)

    def has_played_minimum_blitz_games(self, minimum_number=10):
        return self.player_game.has_played_x_number_of_games_of_type(
            'blitz', minimum_number)

    def fetch_rating(self):
        """TODO: Docstring"""
        url = f"https://api.chess.com/pub/player/{self.username}/stats"

        # get rapid and blitz ratings and put them in a tuple that mentions
        # the game type - e.g blitz or rapid
        rapid_rating = (get(url, headers=REQUEST_HEADERS
                            ).json()['chess_rapid']['last']['rating'], 'rapid')
        blitz_rating = (get(url, headers=REQUEST_HEADERS
                            ).json()['chess_rapid']['last']['rating'], 'blitz')

        if self.is_member_of_nspcl():
            if self.has_played_minimum_standard_games():
                return rapid_rating
            else:
                warn(f"{self.username} has not played minimum amount"
                     " of standard games. Blitz rating may be used.")

            if self.has_played_minimum_blitz_games():
                return blitz_rating
            else:
                warn(f"{self.username} has not played minimum amount"
                     " of blitz games.")
        else:
            warn(f"{self.username} is not a member of the Not-So "
                 f"PRO Chess League.")


if __name__ == '__main__':
    list_of_players = ['walidmujahid', 'ijgeoffrey', 'VicMcCracken', 'eoguel',
                       'tombulous']

    for player in list_of_players:
        print(PlayerCriteria(player).fetch_rating())
