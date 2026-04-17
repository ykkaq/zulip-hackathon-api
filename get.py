#!/usr/bin/env python3

import datetime
from pathlib import Path
import re
import hack_api

email = "kouta.sekine@chibatech.ac.jp"


team = "チーム1"

start_year = 2026
start_month = 4
start_day = 22
start_hour = 16
start_minutes = 0
start_seconds = 0

end_year = 2026
end_month = 4
end_day = 29
end_hour = 11
end_minutes = 59
end_seconds = 59

starttime = datetime.datetime(start_year, start_month, start_day, start_hour, start_minutes, start_seconds, tzinfo=datetime.timezone(datetime.timedelta(hours=9)))
endtime = datetime.datetime(end_year, end_month, end_day, end_hour, end_minutes, end_seconds, tzinfo=datetime.timezone(datetime.timedelta(hours=9)))

apikey = str(Path(__file__).with_name("zuliprc"))

# 第1戻り値: scoringによる自動採点をする/しない: True/False, 第2戻り値: 第1戻り値がTrueの場合，採点結果(True:1, False:0)
def scoring(student_id, name, message_id, row_text):
    message = re.sub(re.compile('<.*?>'), '', row_text)
    print(len(message))

    print(message)
    return (False, False)

status,student_id, name, score, total = hack_api.scoring_messages( apikey, email, starttime, endtime, team, scoring)

if status:
    print("学籍番号:",student_id, " 氏名:" , name, " 評価" ,score ,"/", total)
