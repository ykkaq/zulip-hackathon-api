#!/usr/bin/env python3

from typing import Any
import datetime
from zoneinfo import ZoneInfo
import webbrowser
import tkinter as tk
from tkinter import messagebox
import zulip
import time

def defalt_callback(student_id, name, message_id, row_text ):
    return (False, False)


def scoring_messages( apikey,email, starttime, endtime, channel, callback=defalt_callback):
    starttime = int(starttime.timestamp())
    endtime = int(endtime.timestamp())


    client = zulip.Client(config_file=zuliprc)
    apiurl = f"/users/"+email

    result = client.call_endpoint(
        url=apiurl,
        method="GET",
    )
    user = result["user"]
    user_id = user["user_id"]
    name = user["full_name"]
    student_id = email[1:8]


    # Get the 100 last messages sent by "iago@zulip.com" to
    # the channel named "Verona".
    request: dict[str, Any] = {
        "anchor": "newest",
        "num_before": 200,
        "num_after": 0,
        "narrow": [
            {
                "operator": "sender",
                "operand": "user"+str(user_id)+"@hack.cs.chibatech.jp"
            },
            {"operator": "channel", "operand": channel}
        ],
    }
    result = client.get_messages(request)
    if result["result"] == "success":
        if len(result['messages']) == 0:
            return (True, student_id,name,0, 0)
        else:
            if starttime <= result['messages'][0]["timestamp"]:
                print("Check")

            scores = [0]*len(result['messages'])
            i = 0
            while i < len(result['messages']):
                messages = result['messages'][i]
                if starttime <= messages['timestamp']:
                    if messages['timestamp'] <= endtime:
                        print("\n############################################")
                        print("氏名:", name)
                        print("学籍番号:", student_id)
                        submit_time = datetime.datetime.fromtimestamp(messages['timestamp'], tz=ZoneInfo("Asia/Tokyo"))
                        print("投稿日時: ", submit_time)
                        message_id = messages["id"]
                        print("メッセージID: ", message_id)

                        message = messages['content']

                        automatic_flag, result_flag = callback(student_id, name, message_id, message)

                        if automatic_flag:
                            if result_flag:
                                scores[i] = 1
                                i = i + 1
                            else:
                                scores[i] = 0
                                i = i + 1
                        else:
                            html = "<html><body><h1>学籍番号:{0}  氏名:{1}</h1><h2>投稿日時:{2}</h2><h2>メッセージID:{3}</h2>{4}</body></html>".format(student_id,name,submit_time,messages["id"],message)
                            with open("temp.html", "w",  encoding='UTF-8') as f:
                                f.write(html)

                            webbrowser.open("temp.html")
                            ret = tk.messagebox.askyesnocancel(title="メッセージID:" + str(message_id), message="コメントとみなせる場合は「はい」，コメントではない場合は「いいえ」，一つ戻る場合は「キャンセル」")
                            if ret == True:
                                scores[i] = 1
                                i = i + 1
                            elif ret == False:
                                scores[i] = 0
                                i = i + 1
                            elif ret == None:
                                i = i - 1

                #                res = input("コメントとみなせる場合は'Y'，コメントではない場合は'N',一つ戻る場合は'R'を押して下さい:\n")
                #                if res == 'Y' or res == 'y':
                #                    scores[i] = 1
                #                    i = i + 1
                #                    break
                #                elif res == 'N' or res == 'n':
                #                    scores[i] = 0
                #                    i = i + 1
                #                    break
                #                elif res == 'R' or res == 'r':
                #                    print("一つ前のコメントの採点に戻ります．")
                #                    i = i - 1
                #                    break
                #                else:
                #                    print("コマンドが違います．")

            return (True, student_id,name,sum(scores), len(result['messages']))
    else:
        print("error: channel", channel , "does not exist")
        return (False, student_id,name,0, 0)


def add_user(apikey, name, mail, password, class_name, team_name):
    # APIキー
    client = zulip.Client(config_file=apikey)

    # グループIDの取得
    result = client.get_user_groups()

    for groups in result['user_groups']:
        if groups['name'] == class_name:
            class_group_id = groups['id']

#        elif groups['name'] == team_name:
#            team_group_id = groups['id']


    print("クラスID:", class_group_id)
#    print("チームID:", team_group_id)

    # ユーザ登録
    request = {
        "email": mail,
        "password": password,
        "full_name": name,
    }
    result = client.create_user(request)
    print(result)
    print(type(result))
    user_id = result["user_id"]
    print("ユーザID:", user_id)

    # ユーザのグループ登録
    request = {
        "add": user_id,
    }
    result = client.update_user_group_members(class_group_id, request)
#    result = client.update_user_group_members(team_group_id, request)

    # ユーザのチャンネル登録
    result = client.add_subscriptions(
        streams=[
            {"name": team_name},
        ],
        principals=[user_id],
    )

    result = client.add_subscriptions(
        streams=[
            {"name": class_name},
        ],
        principals=[user_id],
    )

    return True


def add_teacher(apikey, name, mail, password, group_names, channel_names):
    # APIキー
    client = zulip.Client(config_file=apikey)


    # ユーザ登録
    request = {
        "email": mail,
        "password": password,
        "full_name": name,
    }
    result = client.create_user(request)
    print(result)
    print(type(result))
    user_id = result["user_id"]
    print("ユーザID:", user_id)

    # ユーザのグループ登録

    result = client.get_user_groups()

    for group_name in group_names:
        # グループIDの取得
        for groups in result['user_groups']:
            if groups['name'] == group_name:
                group_id = groups['id']

        request = {
            "add": user_id,
        }
        result = client.update_user_group_members(group_id, request)


    time.sleep(10)
    # ユーザのチャンネル登録
    for channel_name in channel_names:
        result = client.add_subscriptions(
            streams=[
                {"name": channel_name},
            ],
            principals=[user_id],
        )

    return True

def add_user_channel(apikey, mail, channel_names):
    # APIキー
    client = zulip.Client(config_file=apikey)
    apiurl = f"/users/"+mail

    result = client.call_endpoint(
        url=apiurl,
        method="GET",
    )
    user = result["user"]
    user_id = user["user_id"]
    name = user["full_name"]
    student_id = mail[1:8]

    time.sleep(10)
    # ユーザのチャンネル登録
    for channel_name in channel_names:
        result = client.add_subscriptions(
            streams=[
                {"name": channel_name},
            ],
            principals=[user_id],
        )

    return True