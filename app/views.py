from django.shortcuts import render
from django.http.response import HttpResponse, HttpResponseBadRequest, HttpResponseServerError
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import View
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import (
    MessageEvent,
    PostbackEvent,
    TextMessage,
    FlexSendMessage

)
import os
import re
import pickle
import calendar
import datetime


# ローカルではコメントアウト
# CHANNEL_ACCESS_TOKEN = os.environ['CHANNEL_ACCESS_TOKEN']
# CHANNEL_SECRET = os.environ['CHANNEL_SECRET']

# line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
# handler = WebhookHandler(CHANNEL_SECRET)

# ローカルではコメント解除
line_bot_api = LineBotApi("LoQufLNooUro/P/XN9S9OaO8YF45+j47kIahuAzUwoF8mPO1VQQLdwgzTFRUn/qliX/Ndnd6dzKilib3F4gPQ1O4tQkNDoNl7Z57lzDZRCruOxRjKBNIERV2I3LRMvZQ8OKqj1UAdmsGPfZQEeV7iQdB04t89/1O/w1cDnyilFU=")
handler = WebhookHandler("9a2b63f94bf6b809a34bbc2381950c9f")

class CallbackView(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse("OK")

    def post(self, request, *args, **kwargs):
        signature = request.META["HTTP_X_LINE_SIGNATURE"]
        body = request.body.decode("utf-8")

        try:
            handler.handle(body, signature)
        except InvalidSignatureError:
            return HttpResponseBadRequest()
        except LineBotApiError as e:
            print(e)
            return HttpResponseServerError()

        return HttpResponse("OK")

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(CallbackView, self).dispatch(*args, **kwargs)

    @staticmethod
    @handler.add(MessageEvent, message=TextMessage)
    def message_event(event):
        if event.reply_token == "00000000000000000000000000000000":
            return
        
        # 送られてきたメッセージを格納
        text = event.message.text


        # 予約開始
        if text == "予約":

            # プロフィール情報を取得
            profile = line_bot_api.get_profile(event.source.user_id)
            # フックを保存
            hook = [profile.display_name, profile.user_id]
            f = open(profile.user_id, 'wb')
            pickle.dump(hook, f)
            f.close()
            print(pickle.load(open(profile.user_id, 'rb')))

            # カレンダーの取得
            def get_day_of_nth_dow(year, month, nth, dow):
                '''dow: Monday(0) - Sunday(6)'''
                if nth < 1 or dow < 0 or dow > 6:
                    return None

                first_dow, n = calendar.monthrange(year, month)
                day = 7 * (nth - 1) + (dow - first_dow) % 7 + 1

                return day if day <= n else None

            # date関数を返す
            def get_date_of_nth_dow(year, month, nth, dow):
                day = get_day_of_nth_dow(year, month, nth, dow)
                return datetime.date(year, month, day) if day else None
            
            # 現在年月日を取得
            now = datetime.datetime.today()
            # now = datetime.datetime(2021, 12, 16)

            # 直近の木曜日（4日分）を取得
            thu_days=[]
            if now.month < 12:
                for y in range(now.year, now.year+1):
                    for m in range(now.month, now.month+2):
                        # 5週目までを出力
                        for n in range(1, 6):
                            # 5週目の木曜日が存在しない場合（None）は除外
                            if get_day_of_nth_dow(y, m, n, 3) is not None:
                                # 今月の残りの木曜日を取得
                                if m == now.month and get_day_of_nth_dow(y, m, n, 3) > now.day and len(thu_days) < 4:
                                    thu_days.append(get_date_of_nth_dow(y, m, n, 3))
                                # 今月の残りの木曜日が4日未満の場合は来月の木曜日を取得
                                elif len(thu_days) < 4 and m == now.month+1:
                                    thu_days.append(get_date_of_nth_dow(y, m, n, 3))
            elif now.month == 12:
                for y in range(now.year, now.year+2):
                    for m in range(1, 13):
                        # 5週目までを出力
                        for n in range(1, 6):
                            # 5週目の木曜日が存在しない場合（None）は除外
                            if get_day_of_nth_dow(y, m, n, 3) is not None:
                                # 今月の残りの木曜日を取得
                                if m == now.month and get_day_of_nth_dow(y, m, n, 3) > now.day and len(thu_days) < 4:
                                    thu_days.append(get_date_of_nth_dow(y, m, n, 3))
                                # 今月の残りの木曜日が4日未満の場合は来月の木曜日を取得
                                elif len(thu_days) < 4 and y == now.year+1 and m == 1:
                                    thu_days.append(get_date_of_nth_dow(y, m, n, 3))
            print(thu_days)

            # メッセージを送信
            content = {
                "type": "flex",
                "altText": "予約日を以下よりご選択ください",
                "contents": {
                    "type": "bubble",
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "予約日を以下よりご選択ください",
                                "weight": "bold",
                                "align": "center",
                                "contents": []
                            }
                        ]
                    },
                    "footer": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "postback",
                                            "label": f"{thu_days[0].month}月{thu_days[0].day}日(木)",
                                            "displayText": f"{thu_days[0].month}月{thu_days[0].day}日(木)",
                                            "data": thu_days[0].strftime("%Y-%m-%d")
                                        }
                                    },
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "postback",
                                            "label": f"{thu_days[1].month}月{thu_days[1].day}日(木)",
                                            "displayText": f"{thu_days[1].month}月{thu_days[1].day}日(木)",
                                            "data": thu_days[1].strftime("%Y-%m-%d")
                                        }
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "postback",
                                            "label": f"{thu_days[2].month}月{thu_days[2].day}日(木)",
                                            "displayText": f"{thu_days[2].month}月{thu_days[2].day}日(木)",
                                            "data": thu_days[2].strftime("%Y-%m-%d")
                                        }
                                    },
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "postback",
                                            "label": f"{thu_days[3].month}月{thu_days[3].day}日(木)",
                                            "displayText": f"{thu_days[3].month}月{thu_days[3].day}日(木)",
                                            "data": thu_days[3].strftime("%Y-%m-%d")
                                        }
                                    }
                                ]
                            },
                            {
                                "type": "separator",
                                "margin": "xxl"
                            },
                            {
                                "type": "text",
                                "text": "※上記日程以外をご希望の場合はMENUのお問い合わせよりお申し付けください。",
                                "size": "xxs",
                                "margin": "md",
                                "wrap": True,
                                "contents": []
                            }
                        ]
                    }
                }
            }
            result = FlexSendMessage.new_from_json_dict(content)
            line_bot_api.push_message(profile.user_id, messages=result)

    # ボタンの入力を受け取るPostbackEvent
    @handler.add(PostbackEvent)
    def on_postback(event):

        # プロフィール情報を取得
        profile = line_bot_api.get_profile(event.source.user_id)

        # 予約時間を選択
        if len(event.postback.data) == 10:

            # 選択された予約日を追記保存
            array = pickle.load(open(profile.user_id, 'rb'))
            f = open(profile.user_id, 'wb')
            if len(array) < 3:
                array.insert(2, event.postback.data)
            else:
                array[2] = event.postback.data
            pickle.dump(array, f)
            f.close()
            print(pickle.load(open(profile.user_id, 'rb')))

            # メッセージを送信
            content = {
                "type": "flex",
                "altText": "予約時間を以下よりご選択ください",
                "contents": {
                    "type": "bubble",
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "予約時間を以下よりご選択ください",
                                "weight": "bold",
                                "align": "center",
                                "contents": []
                            }
                        ]
                    },
                    "footer": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "postback",
                                            "label": "11:00～",
                                            "displayText": "11:00～",
                                            "data": "11:00"
                                        }
                                    },
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "postback",
                                            "label": "12:00～",
                                            "displayText": "12:00～",
                                            "data": "12:00"
                                        }
                                    },
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "postback",
                                            "label": "13:00～",
                                            "displayText": "13:00～",
                                            "data": "13:00",
                                        }
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "postback",
                                            "label": "14:00～",
                                            "displayText": "14:00～",
                                            "data": "14:00",
                                        }
                                    },
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "postback",
                                            "label": "15:00～",
                                            "displayText": "15:00～",
                                            "data": "15:00",
                                        }
                                    },
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "postback",
                                            "label": "16:00～",
                                            "displayText": "16:00～",
                                            "data": "16:00",
                                        }
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "postback",
                                            "label": "17:00～",
                                            "displayText": "17:00～",
                                            "data": "17:00",
                                        }
                                    },
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "postback",
                                            "label": "18:00～",
                                            "displayText": "18:00～",
                                            "data": "18:00",
                                        }
                                    },
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "postback",
                                            "label": "19:00～",
                                            "displayText": "19:00～",
                                            "data": "19:00",
                                        }
                                    }
                                ]
                            },
                            {
                                "type": "separator",
                                "margin": "xxl"
                            },
                            {
                                "type": "text",
                                "text": "※ご予約は1時間単位とさせていただいております。",
                                "size": "xxs",
                                "margin": "md",
                                "wrap": True,
                                "contents": []
                            },
                            {
                                "type": "text",
                                "text": "※上記時間以外をご希望の場合はMENUのお問い合わせよりお申し付けください。",
                                "size": "xxs",
                                "wrap": True,
                                "contents": []
                            }
                        ]
                    }
                }
            }
            result = FlexSendMessage.new_from_json_dict(content)
            line_bot_api.push_message(profile.user_id, messages=result)

        # 人数を選択
        if len(event.postback.data) == 5:

            # 選択された予約時間を追記保存
            array = pickle.load(open(profile.user_id, 'rb'))
            f = open(profile.user_id, 'wb')
            if len(array) < 4:
                array.insert(3, event.postback.data)
            else:
                array[3] = event.postback.data
            pickle.dump(array, f)
            f.close()
            print(pickle.load(open(profile.user_id, 'rb')))

            # メッセージを送信
            content = {
                "type": "flex",
                "altText": "予約人数を以下よりご選択ください",
                "contents": {
                    "type": "bubble",
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "予約人数を以下よりご選択ください",
                                "weight": "bold",
                                "align": "center",
                                "contents": []
                            }
                        ]
                    },
                    "footer": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "postback",
                                            "label": "1名様",
                                            "text": "1名様",
                                            "data": "1名様"
                                        }
                                    },
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "postback",
                                            "label": "2名様",
                                            "text": "2名様",
                                            "data": "2名様"
                                        }
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "postback",
                                            "label": "3名様",
                                            "text": "3名様",
                                            "data": "3名様"
                                        }
                                    },
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "postback",
                                            "label": "4名様",
                                            "text": "4名様",
                                            "data": "4名様"
                                        }
                                    }
                                ]
                            },
                            {
                                "type": "separator",
                                "margin": "xxl"
                            },
                            {
                                "type": "text",
                                "text": "※5名様以上をご希望の場合はMENUのお問い合わせよりお申し付けください。",
                                "size": "xxs",
                                "margin": "md",
                                "wrap": True,
                                "contents": []
                            }
                        ]
                    }
                }
            }
            result = FlexSendMessage.new_from_json_dict(content)
            line_bot_api.push_message(profile.user_id, messages=result)

        # 最終確認
        if len(event.postback.data) == 3:

            # 選択された人数を追記保存
            array = pickle.load(open(profile.user_id, 'rb'))
            f = open(profile.user_id, 'wb')
            if len(array) < 5:
                array.insert(4, event.postback.data)
            else:
                array[4] = event.postback.data
            pickle.dump(array, f)
            f.close()
            reservation = pickle.load(open(profile.user_id, 'rb'))
            print(pickle.load(open(profile.user_id, 'rb')))

            # 予約日を月日に変換
            reservation_date = reservation[2][5:].replace("-", "月").lstrip("0") + "日(木)"
            print(reservation_date)

            # メッセージを送信
            content = {
                "type": "flex",
                "altText": "ご予約はこちらでお間違いないでしょうか？",
                "contents": {
                    "type": "bubble",
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "こちらでお間違いないでしょうか？",
                                "weight": "bold",
                                "align": "center",
                                "contents": []
                            },
                            {
                                "type": "text",
                                "text": f"お名前　 ：{reservation[0]}様",
                                "margin": "xxl",
                                "contents": []
                            },
                            {
                                "type": "text",
                                "text": f"予約日　 ：{reservation_date}　{reservation[3]}～",
                                "contents": []
                            },
                            {
                                "type": "text",
                                "text": f"予約人数 ：{reservation[4]}",
                                "contents": []
                            }
                        ]
                    },
                    "footer": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "postback",
                                            "label": "OK",
                                            "data": "OK"
                                        }
                                    },
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "postback",
                                            "label": "キャンセル",
                                            "data": "キャンセル"
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                }
            }
            result = FlexSendMessage.new_from_json_dict(content)
            line_bot_api.push_message(profile.user_id, messages=result)

        # LINE通知
        if event.postback.data == "OK":

            # 予約情報を変数に格納
            reservation = pickle.load(open(profile.user_id, 'rb'))
            print(reservation)

            # 予約日を月日に変換
            reservation[2] = reservation[2][5:].replace("-", "月").lstrip("0") + "日(木)"
            print(reservation)

            # unelmaへメッセージを送信
            content = {
                "type": "flex",
                "altText": "cafe unelmaの予約を受け付けました！",
                "contents": {
                    "type": "bubble",
                    "hero": {
                        "type": "image",
                        "url": "https://res.cloudinary.com/dfnnruqnc/image/upload/v1632096188/cafe%20unelma/cafe-unelma_%E3%83%AD%E3%82%B4_p9w5ta.png",
                        "size": "5xl",
                        "aspectRatio": "1.51:1",
                        "aspectMode": "fit",
                        "position": "relative",
                        "offsetTop": "20px"
                    },
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "以下予約を受け付けました！",
                                "weight": "bold",
                                "align": "center",
                                "margin": "xxl",
                                "contents": []
                            },
                            {
                                "type": "text",
                                "text": f"お名前　 ：{reservation[0]}様",
                                "margin": "xxl",
                                "contents": []
                            },
                            {
                                "type": "text",
                                "text": f"予約日　 ：{reservation[2]}　{reservation[3]}～",
                                "contents": []
                            },
                            {
                                "type": "text",
                                "text": f"予約人数 ：{reservation[4]}",
                                "contents": []
                            }
                        ]
                    },
                    "styles": {
                        "hero": {
                            "backgroundColor": "#F2ECDD"
                        },
                        "body": {
                            "backgroundColor": "#F2ECDD"
                        }
                    }
                }
            }
            result = FlexSendMessage.new_from_json_dict(content)

            # ローカルではコメントアウト
            # PUSH_USER_ID = os.environ['PUSH_USER_ID']
            # line_bot_api.push_message(PUSH_USER_ID, messages=result)

            line_bot_api.push_message("U4314fbfe96e7dd43429ddba54b3f6131", messages=result)

            # メッセージを送信
            content = {
                "type": "flex",
                "altText": "ご予約ありがとうございます",
                "contents": {
                    "type": "bubble",
                    "hero": {
                        "type": "image",
                        "url": "https://res.cloudinary.com/dfnnruqnc/image/upload/v1632096188/cafe%20unelma/cafe-unelma_%E3%83%AD%E3%82%B4_p9w5ta.png",
                        "size": "5xl",
                        "aspectRatio": "1.51:1",
                        "aspectMode": "fit",
                        "position": "relative",
                        "offsetTop": "20px"
                    },
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": f"ご予約ありがとうございます！{reservation[0]}様のお越しを心よりお待ちしております。",
                                "weight": "bold",
                                "align": "center",
                                "margin": "xxl",
                                "contents": []
                            },
                            {
                                "type": "text",
                                "text": f"{reservation[0]}様のお越しを心よりお待ちしております。当日はお気をつけてお越しくださいませ。",
                                "size": "sm",
                                "align": "start",
                                "margin": "lg",
                                "wrap": True,
                                "contents": []
                            },
                            {
                                "type": "text",
                                "text": "cafe unelma",
                                "size": "xs",
                                "align": "end",
                                "margin": "lg",
                                "wrap": True,
                                "contents": []
                            },
                            {
                                "type": "text",
                                "text": "冨澤のぞみ",
                                "size": "xs",
                                "align": "end",
                                "wrap": True,
                                "contents": []
                            }
                        ]
                    },
                    "styles": {
                        "hero": {
                            "backgroundColor": "#F2ECDD"
                        },
                        "body": {
                            "backgroundColor": "#F2ECDD"
                        }
                    }
                }
            }
            result = FlexSendMessage.new_from_json_dict(content)
            line_bot_api.push_message(profile.user_id, messages=result)

            # 予約情報のファイルを削除
            os.remove(reservation[1])

        if event.postback.data == "キャンセル":
            # 予約情報のファイルを削除
            os.remove(reservation[1])