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
__version__ = "0.7.0"
__maintainer__ = "Walid Mujahid وليد مجاهد"
__email__ = "walid.mujahid.dev@gmail.com"
__status__ = "Development"


REQUEST_HEADERS = {'User-Agent': 'RatingsFetcher/0.7.0 '
                                 '(Author: Walid Mujahid, '
                                 'Email: walid.mujahid.dev@gmail.com, '
                                 'Chess.com username: walidmujahid)'}


class Warnings:
    """TODO: Docstring"""
    def __init__(self, username):
        """TODO: Docstring"""
        self.username = username

    def has_not_played_minimum_standard_games(self):
        """TODO: Docstring"""
        warn(f"{self.username} has not played minimum amount"
             " of standard games. Blitz rating may be used.")

    def has_not_played_minimum_blitz_games(self):
        """TODO: Docstring"""
        warn(f"{self.username} has not played minimum amount"
             " of blitz games.")

    def has_closed_account(self):
        """TODO: Docstring"""
        warn(f"{self.username} has closed their account.")

    def has_violated_fair_play_rules(self):
        """TODO: Docstring"""
        warn(f"{self.username} has violated the fair play rules.")

    def is_not_a_member_of_the_nspcl(self):
        """TODO: Docstring"""
        warn(f"{self.username} is not a member of the Not-So "
             f"PRO Chess League.")

    def is_a_titled_player(self):
        """TODO: Docstring"""
        warn(f"{self.username} is a titled player.")


class Player:
    """TODO: Docstring"""
    def __init__(self, username):
        """TODO: Docstring"""
        self.username = username

    def get_account_status(self):
        """TODO: Docstring"""
        return get(f"https://api.chess.com/pub/player/{self.username}"
                   ).json()['status']

    def get_player_stats(self):
        """TODO: Docstring"""
        return get(f"https://api.chess.com/pub/player/{self.username}/stats",
                   headers=REQUEST_HEADERS).json()


class GamePlay:
    """TODO: Docstring."""
    def __init__(self, username: str, past_months: int=8):
        """TODO: Docstring"""
        self.username = username
        self.past_months = past_months

    def has_played_x_number_of_games_of_type(
            self, game_type: str, minimum_number_of_games_played: int):
        """TODO: Docstring"""
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
        """TODO: Docstring"""
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
        """TODO: Docstring"""
        games_of_type = []

        for dates in self.generate_month_range()[::-1]:
            games = self.get_monthly_archives(dates.year, dates.month)

            for game in games:
                if self.is_game_of_type(game, game_type):
                    games_of_type.append(game)

        return sorted(games_of_type, key=itemgetter('end_time'))

    def count_live_chess_games_of_type(self, game_type: str):
        """TODO: Docstring"""
        return len(self.get_live_chess_games_of_type(game_type))


class PlayerCriteria:
    """TODO: Docstring"""
    def __init__(self, username: str):
        """TODO: Docstring"""
        self.username = username
        self.status = Player(username).get_account_status()
        self.player_game = GamePlay(username)

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
        """TODO: Docstring"""
        return self.player_game.has_played_x_number_of_games_of_type(
            'standard', minimum_number)

    def has_played_minimum_blitz_games(self, minimum_number=10):
        """TODO: Docstring"""
        return self.player_game.has_played_x_number_of_games_of_type(
            'blitz', minimum_number)

    # make sure player has not closed their account
    def has_not_closed_account(self):
        """TODO: Docstring"""
        return True if self.status != 'closed' else False

    # make sure player has not violated any fair policy rules
    # and had their account closed
    def has_not_violated_fair_play_rules(self):
        """TODO: Docstring"""
        return True if self.status != "closed:fair_play_violations" else False


class RatingFetcher:
    """TODO: Docstring"""
    def __init__(self, username):
        """TODO: Docstring"""
        self.username = username
        self.warnings = Warnings(username)
        self.player_criteria = PlayerCriteria(username)
        self.player_stats = Player(username).get_player_stats()

        # get rapid and blitz ratings and put them in a tuple that mentions
        # the game type - e.g blitz or rapid
        self.rapid_rating = (username,
                             self.player_stats['chess_rapid']['last']['rating'],
                             'rapid')
        self.blitz_rating = (username,
                             self.player_stats['chess_rapid']['last']['rating'],
                             'blitz')

    def fetch_rating(self):
        """TODO: Docstring"""
        if self.player_criteria.has_not_violated_fair_play_rules():
            if self.player_criteria.has_not_closed_account():
                if self.player_criteria.is_member_of_nspcl():
                    if self.player_criteria.has_played_minimum_standard_games():
                        return self.rapid_rating
                    else:
                        self.warnings.has_not_played_minimum_standard_games()

                    if self.player_criteria.has_played_minimum_blitz_games():
                        return self.blitz_rating
                    else:
                        self.warnings.has_not_played_minimum_blitz_games()
                        return tuple([self.username, 'does not meet criteria'])
                else:
                    self.warnings.is_not_a_member_of_the_nspcl()
                    return tuple([self.username, 'not a member of NSPCL'])
            else:
                self.warnings.has_closed_account()
                return tuple([self.username, 'account closed'])
        else:
            self.warnings.has_violated_fair_play_rules()
            return tuple([self.username, 'violated fair play rules'])


if __name__ == '__main__':
    list_of_players = ['spaceface23', 'walidmujahid', 'ijgeoffrey',
                       'VicMcCracken', 'eoguel', 'tombulous', 'regicidalmaniac']

    for player in list_of_players:
        print(RatingFetcher(player).fetch_rating())
