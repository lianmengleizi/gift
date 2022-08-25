# coding:utf-8

"""
    1: 导入user.json 文件检查
    2: 导入gift.json 文件检查
    3: 确定用户表中每个用户的信息字段
    4: 读取user.json文件
    5: 写入user.json文件（检测该用户是否存在），存在则不可写入

    username 姓名
    role normal or admin
    create_time timestamp
    update_time timestamp
    gift []
"""
import time
import json
import os.path

from common.error import UserExistsError, RoleError, LevelError, NegativeNumberError, CountError
from common.consts import ROLES, FIRSTLEVELS, SECONDLEVELS
from common.utils import check_file, timestamp_to_string


class Base(object):
    def __init__(self, user_json, gift_json):
        self.user_json = user_json
        self.gift_json = gift_json

        self.__check_user_json()
        self.__check_gift_json()
        self.__init_gifts()

    #  1: 导入user.json 文件检查
    def __check_user_json(self):
        check_file(self.user_json)

    # 2: 导入gift.json 文件检查
    def __check_gift_json(self):
        check_file(self.gift_json)

    #  读取user.json文件
    def __read_users(self, time_to_str=False):
        with open(self.user_json, 'r') as f:
            data = json.loads(f.read())

        if time_to_str == True:
            for username, v in data.items():
                v['create_time'] = timestamp_to_string(v['create_time'])
                v['update_time'] = timestamp_to_string(v['update_time'])
                data[username] = v

        return data

    # 写入user.json文件（检测该用户是否存在），存在则不可写入
    def __write_user(self, **user):
        if 'username' not in user:
            raise ValueError('missing username')
        if 'role' not in user:
            raise ValueError('missing role')
        # 3: 确定用户表中每个用户的信息字段
        user['active'] = True
        user['create_time'] = time.time()
        user['update_time'] = time.time()
        user['gift'] = []

        users = self.__read_users()
        # print(users)
        # return

        if user['username'] in users:
            raise UserExistsError('username %s had exists' % user['username'])

        users.update(
            {user['username']: user}
        )

        self.__save(users, self.user_json)
        return users

    def __change_role(self, username, role):
        users = self.__read_users()
        user = users.get(username)
        if not user:
            return False

        if role not in ROLES:
            raise RoleError('not use role %s' % role)

        user['role'] = role
        user['update_time'] = time.time()
        users[username] = user

        self.__save(users, self.user_json)
        return True

    def __change_active(self, username):
        users = self.__read_users()
        user = users.get(username)
        if not user:
            return False

        user['active'] = not user['active']
        user['update_time'] = time.time()
        users[username] = user

        self.__save(users, self.user_json)
        return True

    def __delete_user(self, username):
        users = self.__read_users()
        user = users.get(username)
        if not user:
            return False

        delete_user = users.pop(username)
        json_data = json.dumps(users)
        with open(self.user_json, 'w') as f:
            f.write(json_data)

        return delete_user

    def __read_gifts(self):
        with open(self.gift_json) as f:
            data = json.loads(f.read())
        return data

    def __init_gifts(self):
        data = {
            'level1': {
                'level1': {},
                'level2': {},
                'level3': {}
            },
            'level2': {
                'level1': {},
                'level2': {},
                'level3': {}
            },
            'level3': {
                'level1': {},
                'level2': {},
                'level3': {}
            },
            'level4': {
                'level1': {},
                'level2': {},
                'level3': {}
            }
        }
        gifts = self.__read_gifts()
        if len(gifts) != 0:
            return
        self.__save(data, self.gift_json)

    def __write_gift(self, first_level, second_level, gift_name, gift_count):
        if first_level not in FIRSTLEVELS:
            raise LevelError('firstlevel not exists')
        if second_level not in SECONDLEVELS:
            raise LevelError('secondlevel not exists')

        gifts = self.__read_gifts()

        current_gift_pool = gifts[first_level]
        current_second_gift_pool = current_gift_pool[second_level]

        if gift_count <= 0:
            gift_count = 1

        if gift_name in current_second_gift_pool:
            current_second_gift_pool[gift_name]['count'] = current_second_gift_pool[gift_name]['count'] + gift_count
        else:
            current_second_gift_pool[gift_name] = {
                'name': gift_name,
                'count': gift_count
            }
        current_gift_pool[second_level] = current_second_gift_pool
        gifts[first_level] = current_gift_pool

        self.__save(gifts, self.gift_json)

    def __gift_update(self, first_level, second_level, gift_name, gift_count=1, is_admin=False):
        assert isinstance(gift_count, int), 'gift count is int'

        if first_level not in FIRSTLEVELS:
            raise LevelError('firstlevel not exists')
        if second_level not in SECONDLEVELS:
            raise LevelError('secondlevel not exists')

        gifts = self.__read_gifts()

        current_gift_pool = gifts[first_level]
        current_second_gift_pool = current_gift_pool[second_level]
        if gift_name not in current_second_gift_pool:
            return False

        current_gift = current_second_gift_pool[gift_name]

        if is_admin == True:
            if gift_count <= 0:
                raise CountError('gift count not 0')
            current_gift['count'] = gift_count
            print(gift_count)
        else:
            if current_gift['count'] - gift_count < 0:
                raise NegativeNumberError('gift count can not negative')

        # current_gift['count'] -= gift_count
        current_second_gift_pool[gift_name] = current_gift
        current_gift_pool[second_level] = current_second_gift_pool

        self.__save(gifts, self.gift_json)

    def __check_and_getgift(self, first_level, second_level, gift_name):
        if first_level not in FIRSTLEVELS:
            raise LevelError('firstlevel not exists')
        if second_level not in SECONDLEVELS:
            raise LevelError('secondlevel not exists')

        gifts = self.__read_gifts()

        level_one = gifts[first_level]
        level_two = level_one[second_level]

        if gift_name not in level_two:
            return False

        return {
            'level_one': level_one,
            'level_two': level_two,
            'gifts': gifts
        }

    def __delete_gift(self, first_level, second_level, gift_name):
        data = self.__check_and_getgift(first_level, second_level, gift_name)

        if not data:
            return data

        current_gift_pool = data.get('level_one')
        current_second_gift_pool = data.get('level_two')
        gifts = data.get('gifts')

        delete_gift_data = current_second_gift_pool.pop(gift_name)
        current_gift_pool[second_level] = current_second_gift_pool
        gifts[first_level] = current_gift_pool
        self.__save(gifts, self.gift_json)
        return delete_gift_data

    def __save(self, data, path):
        json_data = json.dumps(data)
        with open(path, 'w') as f:
            f.write(json_data)


if __name__ == '__main__':
    gift_path = os.path.join(os.getcwd(), 'storage', 'gift.json')
    user_path = os.path.join(os.getcwd(), 'storage', 'user.json')
    base = Base(user_json=user_path, gift_json=gift_path)
    # result = base.write_user(username='shilei', role='admin')
    # print(result)
    # result = base.read_gifts()
    # print(result)
    # base.gift_update(first_level='level4', second_level='level2', gift_name='小米', gift_count=5)
    # print(base.read_users())
