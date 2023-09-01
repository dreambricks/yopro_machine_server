import os
from datetime import datetime, timedelta
import pickle


class UserData:
    def __init__(self, user_id):
        self.id = user_id
        self.blocked_until = datetime.now()

    def blocks(self, delta):
        self.blocked_until = datetime.now() + delta

    def blocks_for_a_day(self):
        self.blocks(timedelta(days=1))

    def blocks_for_15min(self):
        self.blocks(timedelta(minutes=15))

    def is_blocked(self):
        return datetime.now() < self.blocked_until


class LogUser:
    def __init__(self, pkl_file='users_db.pkl'):
        self.pkl_file = pkl_file
        if os.path.isfile(self.pkl_file):
            with open(self.pkl_file, 'rb') as file:
                self.ids = pickle.load(file)
        else:
            self.ids = {}
            self.store()

    def store(self):
        with open(self.pkl_file, 'wb') as file:
            pickle.dump(self.ids, file)

    def is_blocked(self, user_id):

        # user already exists. check if he/she is blocked
        if user_id in self.ids:
            return self.ids[user_id].is_blocked()

        print(f"new id: '{user_id}'")
        self.ids[user_id] = UserData(user_id)
        return False

    def blocks(self, user_id):
        if user_id not in self.ids:
            # error
            return
        self.ids[user_id].blocks_for_a_day()
        self.store()

    @staticmethod
    def get_id_from_header_items(header_items):
        key_values = {name: value.rstrip() for name, value in header_items}

        if 'X-Forwarded-For' in key_values and len(key_values['X-Forwarded-For']) > 0:
            return key_values['X-Forwarded-For']

        if 'Cookie' in key_values and len(key_values['Cookie']) > 0:
            return key_values['Cookie']

        key = []
        for name, value in sorted(header_items):
            if name in ['Cookie', 'User-Agent', 'X-Forwarded-For']:
                key.append(value.rstrip())
        return '|'.join(key)


if __name__ == "__main__":
    log_user = LogUser('test.pkl')

    header_items = [('X-Forwarded-For', 'ID02')]

    my_user_id = log_user.get_id_from_header_items(header_items)

    if not log_user.is_blocked(my_user_id):
        print(f"Blocking user {my_user_id}")
        log_user.blocks(my_user_id)
    else:
        print(f"User {my_user_id} is already blocked")