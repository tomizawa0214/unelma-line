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
import pickle
import calendar
import datetime
import googleapiclient.discovery
import google.auth


CHANNEL_ACCESS_TOKEN = os.environ["CHANNEL_ACCESS_TOKEN"]
CHANNEL_SECRET = os.environ["CHANNEL_SECRET"]

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

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
            f = open(profile.user_id, "wb")
            pickle.dump(hook, f)
            f.close()
            print("予約開始")

            # カレンダーの取得
            def get_day_of_nth_dow(year, month, nth, dow):
                """dow: Monday(0) - Sunday(6)"""
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
                "altText": "予約日を以下よりご選択ください。",
                "contents": {
                    "type": "bubble",
                    "header": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "image",
                                "url": "https://res.cloudinary.com/dfnnruqnc/image/upload/v1632133381/cafe%20unelma/step1_gsw8tc.png",
                                "size": "full",
                                "aspectRatio": "7:1"
                            }
                        ]
                    },
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

        # メニューのカルーセル出力
        if text == "メニュー":

            # プロフィール情報を取得
            profile = line_bot_api.get_profile(event.source.user_id)
            print("メニューを表示")

            # メッセージを送信
            content = {
                "type": "flex",
                "altText": "cafe unelmaのFOOD & DRINKメニューです。",
                "contents": {
                    "type": "carousel",
                    "contents": [
                        {
                            "type": "bubble",
                            "hero": {
                                "type": "image",
                                "url": "https://res.cloudinary.com/dfnnruqnc/image/upload/v1632436431/cafe%20unelma/%E3%82%AD%E3%83%83%E3%82%B7%E3%83%A5_yrwqdy.jpg",
                                "size": "full"
                            },
                            "body": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "キッシュサラダプレート",
                                        "weight": "bold",
                                        "size": "lg",
                                        "contents": []
                                    },
                                    {
                                        "type": "text",
                                        "text": "￥920",
                                        "weight": "bold",
                                        "size": "lg",
                                        "align": "end",
                                        "contents": []
                                    },
                                    {
                                        "type": "text",
                                        "text": "手づくりキッシュと大きいソーセージがのった、野菜をたっぷり食べるプレートです。",
                                        "size": "xs",
                                        "color": "#AAAAAA",
                                        "margin": "lg",
                                        "wrap": True,
                                        "contents": []
                                    }
                                ]
                            },
                            "footer": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "※キッシュの内容は日替わりです。",
                                        "size": "xxs",
                                        "color": "#AAAAAA",
                                        "wrap": True,
                                        "contents": []
                                    },
                                    {
                                        "type": "text",
                                        "text": "※スープやサラダは旬の野菜を使用するので、写真と異なる場合がございます。",
                                        "size": "xxs",
                                        "color": "#AAAAAA",
                                        "wrap": True,
                                        "contents": []
                                    }
                                ]
                            },
                            "styles": {
                                "footer": {
                                    "separator": True
                                }
                            }
                        },
                        {
                            "type": "bubble",
                            "hero": {
                                "type": "image",
                                "url": "https://res.cloudinary.com/dfnnruqnc/image/upload/v1632436431/cafe%20unelma/%E3%82%AD%E3%83%BC%E3%83%9E%E3%82%AB%E3%83%AC%E3%83%BC_qh4qzc.jpg",
                                "size": "full"
                            },
                            "body": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "無水キーマカレープレート",
                                        "weight": "bold",
                                        "size": "lg",
                                        "contents": []
                                    },
                                    {
                                        "type": "text",
                                        "text": "￥1,020",
                                        "weight": "bold",
                                        "size": "lg",
                                        "align": "end",
                                        "contents": []
                                    },
                                    {
                                        "type": "text",
                                        "text": "野菜の水分だけで作りました。野菜の甘みがつまった中辛カレーです。",
                                        "size": "xs",
                                        "color": "#AAAAAA",
                                        "margin": "lg",
                                        "wrap": True,
                                        "contents": []
                                    },
                                    {
                                        "type": "text",
                                        "text": "お子様用に甘口に変更もOK！ごはん大盛も無料です。",
                                        "size": "xs",
                                        "color": "#AAAAAA",
                                        "wrap": True,
                                        "contents": []
                                    }
                                ]
                            },
                            "footer": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "※スープやサラダ等は旬の野菜を使用するので、写真と異なる場合がございます。",
                                        "size": "xxs",
                                        "color": "#AAAAAA",
                                        "wrap": True,
                                        "contents": []
                                    }
                                ]
                            },
                            "styles": {
                                "footer": {
                                    "separator": True
                                }
                            }
                        },
                        {
                            "type": "bubble",
                            "hero": {
                                "type": "image",
                                "url": "https://res.cloudinary.com/dfnnruqnc/image/upload/v1632436431/cafe%20unelma/%E3%82%A2%E3%83%92%E3%83%BC%E3%82%B8%E3%83%A7_u6cfrk.jpg",
                                "size": "full"
                            },
                            "body": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "お野菜アヒージョプレート",
                                        "weight": "bold",
                                        "size": "lg",
                                        "wrap": True,
                                        "contents": []
                                    },
                                    {
                                        "type": "text",
                                        "text": "￥1,100",
                                        "weight": "bold",
                                        "size": "lg",
                                        "align": "end",
                                        "contents": []
                                    },
                                    {
                                        "type": "text",
                                        "text": "旬のお野菜を使った日替わりのアヒージョ！",
                                        "size": "xs",
                                        "color": "#AAAAAA",
                                        "margin": "lg",
                                        "wrap": True,
                                        "contents": []
                                    },
                                    {
                                        "type": "text",
                                        "text": "スペアリブものった、がっつり食べたい人にオススメ！",
                                        "size": "xs",
                                        "color": "#AAAAAA",
                                        "wrap": True,
                                        "contents": []
                                    }
                                ]
                            },
                            "footer": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "※バケットのおかわりは+120円です。",
                                        "size": "xxs",
                                        "color": "#AAAAAA",
                                        "wrap": True,
                                        "contents": []
                                    }
                                ]
                            },
                            "styles": {
                                "footer": {
                                    "separator": True
                                }
                            }
                        },
                        {
                            "type": "bubble",
                            "header": {
                                "type": "box",
                                "layout": "vertical",
                                "flex": 0,
                                "backgroundColor": "#109972",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "TOPPING!",
                                        "weight": "bold",
                                        "size": "xxl",
                                        "color": "#FFFFFF",
                                        "align": "center",
                                        "contents": []
                                    }
                                ]
                            },
                            "body": {
                                "type": "box",
                                "layout": "vertical",
                                "spacing": "md",
                                "contents": [
                                    {
                                        "type": "box",
                                        "layout": "horizontal",
                                        "contents": [
                                            {
                                                "type": "text",
                                                "text": "チーズ",
                                                "weight": "bold",
                                                "size": "lg",
                                                "flex": 3,
                                                "align": "start",
                                                "contents": [
                                                    {
                                                        "type": "span",
                                                        "text": "チーズ"
                                                    },
                                                    {
                                                        "type": "span",
                                                        "text": "｜カレーにオススメ！",
                                                        "size": "xs",
                                                        "weight": "regular"
                                                    }
                                                ]
                                            },
                                            {
                                                "type": "text",
                                                "text": "￥50",
                                                "weight": "bold",
                                                "size": "lg",
                                                "align": "end",
                                                "contents": []
                                            }
                                        ]
                                    },
                                    {
                                        "type": "box",
                                        "layout": "horizontal",
                                        "contents": [
                                            {
                                                "type": "text",
                                                "text": "やさい増し",
                                                "weight": "bold",
                                                "size": "lg",
                                                "align": "start",
                                                "contents": []
                                            },
                                            {
                                                "type": "text",
                                                "text": "￥100",
                                                "weight": "bold",
                                                "size": "lg",
                                                "align": "end",
                                                "contents": []
                                            }
                                        ]
                                    },
                                    {
                                        "type": "box",
                                        "layout": "horizontal",
                                        "contents": [
                                            {
                                                "type": "text",
                                                "text": "ソーセージ",
                                                "weight": "bold",
                                                "size": "lg",
                                                "flex": 3,
                                                "align": "start",
                                                "wrap": True,
                                                "contents": [
                                                    {
                                                        "type": "span",
                                                        "text": "ソーセージ"
                                                    },
                                                    {
                                                        "type": "span",
                                                        "text": "（1本）",
                                                        "size": "xs",
                                                        "weight": "regular"
                                                    }
                                                ]
                                            },
                                            {
                                                "type": "text",
                                                "text": "￥100",
                                                "weight": "bold",
                                                "size": "lg",
                                                "align": "end",
                                                "contents": []
                                            }
                                        ]
                                    },
                                    {
                                        "type": "box",
                                        "layout": "horizontal",
                                        "contents": [
                                            {
                                                "type": "text",
                                                "text": "スペアリブ",
                                                "weight": "bold",
                                                "size": "lg",
                                                "flex": 3,
                                                "align": "start",
                                                "wrap": True,
                                                "contents": [
                                                    {
                                                        "type": "span",
                                                        "text": "スペアリブ"
                                                    },
                                                    {
                                                        "type": "span",
                                                        "text": "（1個）",
                                                        "size": "xs",
                                                        "weight": "regular"
                                                    }
                                                ]
                                            },
                                            {
                                                "type": "text",
                                                "text": "￥150",
                                                "weight": "bold",
                                                "size": "lg",
                                                "align": "end",
                                                "contents": []
                                            }
                                        ]
                                    },
                                    {
                                        "type": "box",
                                        "layout": "horizontal",
                                        "contents": [
                                            {
                                                "type": "text",
                                                "text": "バケット",
                                                "weight": "bold",
                                                "size": "lg",
                                                "flex": 3,
                                                "align": "start",
                                                "wrap": True,
                                                "contents": [
                                                    {
                                                        "type": "span",
                                                        "text": "バケット"
                                                    },
                                                    {
                                                        "type": "span",
                                                        "text": "（3枚）",
                                                        "size": "xs",
                                                        "weight": "regular"
                                                    }
                                                ]
                                            },
                                            {
                                                "type": "text",
                                                "text": "￥120",
                                                "weight": "bold",
                                                "size": "lg",
                                                "align": "end",
                                                "contents": []
                                            }
                                        ]
                                    }
                                ]
                            }
                        },
                        {
                            "type": "bubble",
                            "hero": {
                                "type": "image",
                                "url": "https://res.cloudinary.com/dfnnruqnc/image/upload/v1632436431/cafe%20unelma/%E3%82%AB%E3%83%9C%E3%83%81%E3%83%A3%E3%83%81%E3%83%BC%E3%82%BA%E3%82%B1%E3%83%BC%E3%82%AD_pxjdug.jpg",
                                "size": "full"
                            },
                            "body": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "かぼちゃとゴルゴンゾーラのベイクドチーズケーキ",
                                        "weight": "bold",
                                        "size": "lg",
                                        "wrap": True,
                                        "contents": []
                                    },
                                    {
                                        "type": "text",
                                        "text": "￥500",
                                        "weight": "bold",
                                        "size": "lg",
                                        "align": "end",
                                        "contents": []
                                    },
                                    {
                                        "type": "text",
                                        "text": "それぞれの素材を活かした甘さ控えめのケーキです。",
                                        "size": "xs",
                                        "color": "#AAAAAA",
                                        "margin": "lg",
                                        "wrap": True,
                                        "contents": []
                                    },
                                    {
                                        "type": "text",
                                        "text": "ハチミツと黒こしょうをお好みでかけてお召し上がりください！",
                                        "size": "xs",
                                        "color": "#AAAAAA",
                                        "wrap": True,
                                        "contents": []
                                    }
                                ]
                            }
                        },
                        {
                            "type": "bubble",
                            "hero": {
                                "type": "image",
                                "url": "https://res.cloudinary.com/dfnnruqnc/image/upload/v1632436431/cafe%20unelma/%E3%82%A2%E3%83%9C%E3%82%AB%E3%83%89%E3%83%90%E3%83%8A%E3%83%8A%E3%83%A2%E3%83%B3%E3%83%96%E3%83%A9%E3%83%B3_jgurno.jpg",
                                "size": "full"
                            },
                            "body": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "アボカドバナナモンブラン",
                                        "weight": "bold",
                                        "size": "lg",
                                        "wrap": True,
                                        "contents": []
                                    },
                                    {
                                        "type": "text",
                                        "text": "￥400",
                                        "weight": "bold",
                                        "size": "lg",
                                        "align": "end",
                                        "contents": []
                                    },
                                    {
                                        "type": "text",
                                        "text": "手づくりアーモンド生地にバナナとたっぷりのアボカドクリームがのっています。しっかり濃厚！",
                                        "size": "xs",
                                        "color": "#AAAAAA",
                                        "margin": "lg",
                                        "wrap": True,
                                        "contents": []
                                    }
                                ]
                            }
                        },
                        {
                            "type": "bubble",
                            "hero": {
                                "type": "image",
                                "url": "https://res.cloudinary.com/dfnnruqnc/image/upload/v1632436432/cafe%20unelma/%E9%BB%92%E3%82%B4%E3%83%9E%E3%83%96%E3%83%A9%E3%83%B3%E3%83%9E%E3%83%B3%E3%82%B8%E3%82%A7_mpprh2.jpg",
                                "size": "full"
                            },
                            "body": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "黒ごまブランマンジェ",
                                        "weight": "bold",
                                        "size": "lg",
                                        "wrap": True,
                                        "contents": []
                                    },
                                    {
                                        "type": "text",
                                        "text": "￥400",
                                        "weight": "bold",
                                        "size": "lg",
                                        "align": "end",
                                        "contents": []
                                    },
                                    {
                                        "type": "text",
                                        "text": "栄養価が高い黒ごまをたっぷりと使用した香り高いブランマンジェです。",
                                        "size": "xs",
                                        "color": "#AAAAAA",
                                        "margin": "lg",
                                        "wrap": True,
                                        "contents": []
                                    }
                                ]
                            }
                        },
                        {
                            "type": "bubble",
                            "header": {
                                "type": "box",
                                "layout": "vertical",
                                "flex": 0,
                                "backgroundColor": "#F2AAC1",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "DESSERT",
                                        "weight": "bold",
                                        "size": "xxl",
                                        "color": "#FFFFFF",
                                        "align": "center",
                                        "contents": []
                                    }
                                ]
                            },
                            "body": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "box",
                                        "layout": "horizontal",
                                        "contents": [
                                            {
                                                "type": "text",
                                                "text": "spoonの手づくりジェラート",
                                                "weight": "bold",
                                                "size": "lg",
                                                "flex": 3,
                                                "align": "start",
                                                "wrap": True,
                                                "contents": []
                                            },
                                            {
                                                "type": "text",
                                                "text": "￥330",
                                                "weight": "bold",
                                                "size": "lg",
                                                "align": "end",
                                                "contents": []
                                            }
                                        ]
                                    },
                                    {
                                        "type": "text",
                                        "text": "高崎イオン近くにある大人気ジェラート！！",
                                        "size": "xs",
                                        "color": "#AAAAAA",
                                        "wrap": True,
                                        "contents": []
                                    },
                                    {
                                        "type": "text",
                                        "text": "内容は日替わりです。",
                                        "size": "xs",
                                        "color": "#AAAAAA",
                                        "wrap": True,
                                        "contents": []
                                    },
                                    {
                                        "type": "box",
                                        "layout": "horizontal",
                                        "margin": "lg",
                                        "contents": [
                                            {
                                                "type": "text",
                                                "text": "デザート2種もり",
                                                "weight": "bold",
                                                "size": "lg",
                                                "flex": 3,
                                                "align": "start",
                                                "contents": []
                                            },
                                            {
                                                "type": "text",
                                                "text": "￥600",
                                                "weight": "bold",
                                                "size": "lg",
                                                "align": "end",
                                                "contents": []
                                            }
                                        ]
                                    },
                                    {
                                        "type": "text",
                                        "text": "少し小さめサイズのジェラートとお好きなデザートのお得なもり合わせ",
                                        "size": "xs",
                                        "color": "#AAAAAA",
                                        "wrap": True,
                                        "contents": []
                                    },
                                    {
                                        "type": "box",
                                        "layout": "horizontal",
                                        "margin": "lg",
                                        "contents": [
                                            {
                                                "type": "text",
                                                "text": "デザート3種もり",
                                                "weight": "bold",
                                                "size": "lg",
                                                "flex": 3,
                                                "align": "start",
                                                "wrap": True,
                                                "contents": []
                                            },
                                            {
                                                "type": "text",
                                                "text": "￥850",
                                                "weight": "bold",
                                                "size": "lg",
                                                "align": "end",
                                                "contents": []
                                            }
                                        ]
                                    },
                                    {
                                        "type": "text",
                                        "text": "お好きなデザートを3つお選びください。少し小さめサイズでご用意いたします。",
                                        "size": "xs",
                                        "color": "#AAAAAA",
                                        "wrap": True,
                                        "contents": []
                                    }
                                ]
                            }
                        },
                        {
                            "type": "bubble",
                            "hero": {
                                "type": "image",
                                "url": "https://res.cloudinary.com/dfnnruqnc/image/upload/v1632436431/cafe%20unelma/%E3%83%89%E3%83%A9%E3%82%A4%E3%82%AA%E3%83%AC%E3%83%B3%E3%82%B8%E3%83%86%E3%82%A3%E3%83%BC_gzmuf1.jpg",
                                "size": "full"
                            },
                            "body": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "ドライオレンジティー",
                                        "weight": "bold",
                                        "size": "lg",
                                        "wrap": True,
                                        "contents": [
                                            {
                                                "type": "span",
                                                "text": "ドライオレンジティー"
                                            },
                                            {
                                                "type": "span",
                                                "text": "（Hot）",
                                                "size": "xs"
                                            }
                                        ]
                                    },
                                    {
                                        "type": "text",
                                        "text": "￥450",
                                        "weight": "bold",
                                        "size": "lg",
                                        "align": "end",
                                        "contents": []
                                    },
                                    {
                                        "type": "text",
                                        "text": "高崎市にある、愛媛明浜みかん専門店のスリーサンズさんより入荷！！みかんそのままの甘さが際立ちます。まずは半分、そのままで食べてみてください！",
                                        "size": "xs",
                                        "color": "#AAAAAA",
                                        "margin": "lg",
                                        "wrap": True,
                                        "contents": []
                                    }
                                ]
                            },
                            "footer": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "ドライオレンジは店内でも販売しています！",
                                        "size": "xxs",
                                        "color": "#AAAAAA",
                                        "wrap": True,
                                        "contents": []
                                    }
                                ]
                            },
                            "styles": {
                                "footer": {
                                    "separator": True
                                }
                            }
                        },
                        {
                            "type": "bubble",
                            "hero": {
                                "type": "image",
                                "url": "https://res.cloudinary.com/dfnnruqnc/image/upload/v1632436432/cafe%20unelma/%E6%9F%91%E6%A9%98%E3%82%BD%E3%83%BC%E3%83%80_mwthq5.jpg",
                                "size": "full"
                            },
                            "body": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "自家製かんきつシロップソーダ",
                                        "weight": "bold",
                                        "size": "lg",
                                        "wrap": True,
                                        "contents": []
                                    },
                                    {
                                        "type": "text",
                                        "text": "￥400",
                                        "weight": "bold",
                                        "size": "lg",
                                        "align": "end",
                                        "contents": []
                                    },
                                    {
                                        "type": "text",
                                        "text": "フレッシュなかんきつと旨味のあるミニトマトをシロップ漬けにしました。甘酸っぱいさわやかなドリンクです。",
                                        "size": "xs",
                                        "color": "#AAAAAA",
                                        "margin": "lg",
                                        "wrap": True,
                                        "contents": []
                                    }
                                ]
                            },
                            "footer": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "※かんきつは時期により変更致します。",
                                        "size": "xxs",
                                        "color": "#AAAAAA",
                                        "wrap": True,
                                        "contents": []
                                    }
                                ]
                            },
                            "styles": {
                                "footer": {
                                    "separator": True
                                }
                            }
                        },
                        {
                            "type": "bubble",
                            "header": {
                                "type": "box",
                                "layout": "vertical",
                                "flex": 0,
                                "backgroundColor": "#7B5544",
                                "contents": [
                                {
                                    "type": "text",
                                    "text": "COFFEE",
                                    "weight": "bold",
                                    "size": "xxl",
                                    "color": "#FFFFFF",
                                    "align": "center",
                                    "contents": []
                                }
                                ]
                            },
                            "body": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "box",
                                        "layout": "horizontal",
                                        "contents": [
                                            {
                                                "type": "text",
                                                "text": "ハンドドリップコーヒー",
                                                "weight": "bold",
                                                "size": "lg",
                                                "flex": 3,
                                                "align": "start",
                                                "wrap": True,
                                                "contents": [
                                                    {
                                                        "type": "span",
                                                        "text": "ハンドドリップコーヒー"
                                                    },
                                                    {
                                                        "type": "span",
                                                        "text": "（Hot / Ice）",
                                                        "size": "xs",
                                                        "weight": "regular"
                                                    }
                                                ]
                                            },
                                            {
                                                "type": "text",
                                                "text": "￥450",
                                                "weight": "bold",
                                                "size": "lg",
                                                "align": "end",
                                                "contents": []
                                            }
                                        ]
                                    },
                                    {
                                        "type": "text",
                                        "text": "前橋にあるSAMURAI COFFEEさんの深煎りフレンチ豆を使用しています。一杯ずつじっくりハンドドリップいたします！",
                                        "size": "xs",
                                        "color": "#AAAAAA",
                                        "wrap": True,
                                        "contents": []
                                    },
                                    {
                                        "type": "box",
                                        "layout": "horizontal",
                                        "margin": "lg",
                                        "contents": [
                                            {
                                                "type": "text",
                                                "text": "カフェオレ",
                                                "weight": "bold",
                                                "size": "lg",
                                                "flex": 3,
                                                "align": "start",
                                                "contents": []
                                            },
                                            {
                                                "type": "text",
                                                "text": "￥550",
                                                "weight": "bold",
                                                "size": "lg",
                                                "align": "end",
                                                "contents": []
                                            }
                                        ]
                                    },
                                    {
                                        "type": "box",
                                        "layout": "horizontal",
                                        "margin": "lg",
                                        "contents": [
                                            {
                                                "type": "text",
                                                "text": "ソイオレ",
                                                "weight": "bold",
                                                "size": "lg",
                                                "flex": 3,
                                                "align": "start",
                                                "wrap": True,
                                                "contents": [
                                                {
                                                    "type": "span",
                                                    "text": "ソイオレ"
                                                },
                                                {
                                                    "type": "span",
                                                    "text": "（Hot / Ice）",
                                                    "size": "xs",
                                                    "weight": "regular"
                                                }
                                                ]
                                            },
                                            {
                                                "type": "text",
                                                "text": "￥550",
                                                "weight": "bold",
                                                "size": "lg",
                                                "align": "end",
                                                "contents": []
                                            }
                                        ]
                                    },
                                    {
                                        "type": "box",
                                        "layout": "horizontal",
                                        "margin": "lg",
                                        "contents": [
                                            {
                                                "type": "text",
                                                "text": "玄米コーヒー",
                                                "weight": "bold",
                                                "size": "lg",
                                                "flex": 3,
                                                "align": "start",
                                                "wrap": True,
                                                "contents": [
                                                {
                                                    "type": "span",
                                                    "text": "玄米コーヒー"
                                                },
                                                {
                                                    "type": "span",
                                                    "text": "（Hot / Ice）",
                                                    "size": "xs",
                                                    "weight": "regular"
                                                }
                                                ]
                                            },
                                            {
                                                "type": "text",
                                                "text": "￥450",
                                                "weight": "bold",
                                                "size": "lg",
                                                "align": "end",
                                                "contents": []
                                            }
                                        ]
                                    },
                                    {
                                        "type": "text",
                                        "text": "話題のノンカフェインコーヒーです。",
                                        "size": "xs",
                                        "color": "#AAAAAA",
                                        "wrap": True,
                                        "contents": []
                                    },
                                    {
                                        "type": "text",
                                        "text": "コーヒーに負けないコクもありつつ、玄米の香ばしい香りも楽しめます！",
                                        "size": "xs",
                                        "color": "#AAAAAA",
                                        "wrap": True,
                                        "contents": []
                                    },
                                    {
                                        "type": "box",
                                        "layout": "horizontal",
                                        "margin": "lg",
                                        "contents": [
                                            {
                                                "type": "text",
                                                "text": "玄米カフェオレ",
                                                "weight": "bold",
                                                "size": "lg",
                                                "flex": 3,
                                                "align": "start",
                                                "wrap": True,
                                                "contents": []
                                            },
                                            {
                                                "type": "text",
                                                "text": "￥550",
                                                "weight": "bold",
                                                "size": "lg",
                                                "align": "end",
                                                "contents": []
                                            }
                                        ]
                                    },
                                    {
                                        "type": "box",
                                        "layout": "horizontal",
                                        "margin": "lg",
                                        "contents": [
                                            {
                                                "type": "text",
                                                "text": "玄米ソイオレ",
                                                "weight": "bold",
                                                "size": "lg",
                                                "flex": 3,
                                                "align": "start",
                                                "wrap": True,
                                                "contents": [
                                                {
                                                    "type": "span",
                                                    "text": "玄米ソイオレ"
                                                },
                                                {
                                                    "type": "span",
                                                    "text": "（Hot / Ice）",
                                                    "size": "xs",
                                                    "weight": "regular"
                                                }
                                                ]
                                            },
                                            {
                                                "type": "text",
                                                "text": "￥550",
                                                "weight": "bold",
                                                "size": "lg",
                                                "align": "end",
                                                "contents": []
                                            }
                                        ]
                                    }
                                ]
                            }
                        },
                        {
                            "type": "bubble",
                            "header": {
                                "type": "box",
                                "layout": "vertical",
                                "flex": 0,
                                "backgroundColor": "#BD611E",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "DRINK",
                                        "weight": "bold",
                                        "size": "xxl",
                                        "color": "#FFFFFF",
                                        "align": "center",
                                        "contents": []
                                    }
                                ]
                            },
                            "body": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "box",
                                        "layout": "horizontal",
                                        "contents": [
                                            {
                                                "type": "text",
                                                "text": "アッサムティー",
                                                "weight": "bold",
                                                "size": "lg",
                                                "flex": 3,
                                                "align": "start",
                                                "wrap": True,
                                                "contents": [
                                                {
                                                    "type": "span",
                                                    "text": "アッサムティー"
                                                },
                                                {
                                                    "type": "span",
                                                    "text": "（Hot）",
                                                    "size": "xs",
                                                    "weight": "regular"
                                                }
                                                ]
                                            },
                                            {
                                                "type": "text",
                                                "text": "￥400",
                                                "weight": "bold",
                                                "size": "lg",
                                                "align": "end",
                                                "contents": []
                                            }
                                        ]
                                    },
                                    {
                                        "type": "text",
                                        "text": "ストレート / ミルク",
                                        "size": "xs",
                                        "wrap": True,
                                        "contents": []
                                    },
                                    {
                                        "type": "box",
                                        "layout": "horizontal",
                                        "margin": "lg",
                                        "contents": [
                                            {
                                                "type": "text",
                                                "text": "アイスティー",
                                                "weight": "bold",
                                                "size": "lg",
                                                "flex": 3,
                                                "align": "start",
                                                "wrap": True,
                                                "contents": []
                                            },
                                            {
                                                "type": "text",
                                                "text": "￥300",
                                                "weight": "bold",
                                                "size": "lg",
                                                "align": "end",
                                                "contents": []
                                            }
                                        ]
                                    },
                                    {
                                        "type": "text",
                                        "text": "ストレート / ミルク",
                                        "size": "xs",
                                        "wrap": True,
                                        "contents": []
                                    },
                                    {
                                        "type": "box",
                                        "layout": "horizontal",
                                        "margin": "lg",
                                        "contents": [
                                            {
                                                "type": "text",
                                                "text": "ハーブティー",
                                                "weight": "bold",
                                                "size": "lg",
                                                "flex": 3,
                                                "align": "start",
                                                "wrap": True,
                                                "contents": [
                                                    {
                                                        "type": "span",
                                                        "text": "ハーブティー"
                                                    },
                                                    {
                                                        "type": "span",
                                                        "text": "（Hot / Ice）",
                                                        "size": "xs"
                                                    }
                                                ]
                                            },
                                            {
                                                "type": "text",
                                                "text": "￥400",
                                                "weight": "bold",
                                                "size": "lg",
                                                "align": "end",
                                                "contents": []
                                            }
                                        ]
                                    },
                                    {
                                        "type": "box",
                                        "layout": "horizontal",
                                        "margin": "lg",
                                        "contents": [
                                            {
                                                "type": "text",
                                                "text": "かんきつジュース",
                                                "weight": "bold",
                                                "size": "lg",
                                                "flex": 3,
                                                "align": "start",
                                                "wrap": True,
                                                "contents": []
                                            },
                                            {
                                                "type": "text",
                                                "text": "￥450",
                                                "weight": "bold",
                                                "size": "lg",
                                                "align": "end",
                                                "contents": []
                                            }
                                        ]
                                    },
                                    {
                                        "type": "text",
                                        "text": "スリーサンズさんより入荷の100%ジュース！！オススメです！",
                                        "size": "xs",
                                        "color": "#AAAAAA",
                                        "wrap": True,
                                        "contents": []
                                    },
                                    {
                                        "type": "box",
                                        "layout": "horizontal",
                                        "margin": "lg",
                                        "contents": [
                                            {
                                                "type": "text",
                                                "text": "ジンジャーエール",
                                                "weight": "bold",
                                                "size": "lg",
                                                "flex": 3,
                                                "align": "start",
                                                "wrap": True,
                                                "contents": []
                                            },
                                            {
                                                "type": "text",
                                                "text": "￥300",
                                                "weight": "bold",
                                                "size": "lg",
                                                "align": "end",
                                                "contents": []
                                            }
                                        ]
                                    },
                                    {
                                        "type": "box",
                                        "layout": "horizontal",
                                        "margin": "lg",
                                        "contents": [
                                            {
                                                "type": "text",
                                                "text": "ミルク",
                                                "weight": "bold",
                                                "size": "lg",
                                                "flex": 3,
                                                "align": "start",
                                                "wrap": True,
                                                "contents": [
                                                    {
                                                        "type": "span",
                                                        "text": "ミルク"
                                                    },
                                                    {
                                                        "type": "span",
                                                        "text": "（Hot / Ice）",
                                                        "size": "xs"
                                                    }
                                                ]
                                            },
                                            {
                                                "type": "text",
                                                "text": "￥300",
                                                "weight": "bold",
                                                "size": "lg",
                                                "align": "end",
                                                "contents": []
                                            }
                                        ]
                                    },
                                    {
                                        "type": "box",
                                        "layout": "horizontal",
                                        "margin": "lg",
                                        "contents": [
                                            {
                                                "type": "text",
                                                "text": "ソイミルク",
                                                "weight": "bold",
                                                "size": "lg",
                                                "flex": 3,
                                                "align": "start",
                                                "wrap": True,
                                                "contents": [
                                                    {
                                                        "type": "span",
                                                        "text": "ソイミルク"
                                                    },
                                                    {
                                                        "type": "span",
                                                        "text": "（Hot / Ice）",
                                                        "size": "xs"
                                                    }
                                                ]
                                            },
                                            {
                                                "type": "text",
                                                "text": "￥300",
                                                "weight": "bold",
                                                "size": "lg",
                                                "align": "end",
                                                "contents": []
                                            }
                                        ]
                                    },
                                    {
                                        "type": "box",
                                        "layout": "horizontal",
                                        "margin": "lg",
                                        "contents": [
                                            {
                                                "type": "text",
                                                "text": "黒ごまオレ",
                                                "weight": "bold",
                                                "size": "lg",
                                                "flex": 3,
                                                "align": "start",
                                                "wrap": True,
                                                "contents": [
                                                    {
                                                        "type": "span",
                                                        "text": "黒ごまオレ"
                                                    },
                                                    {
                                                        "type": "span",
                                                        "text": "（Hot）",
                                                        "size": "xs"
                                                    }
                                                ]
                                            },
                                            {
                                                "type": "text",
                                                "text": "￥400",
                                                "weight": "bold",
                                                "size": "lg",
                                                "align": "end",
                                                "contents": []
                                            }
                                        ]
                                    }
                                ]
                            }
                        }
                    ]
                }
            }
            result = FlexSendMessage.new_from_json_dict(content)
            line_bot_api.push_message(profile.user_id, messages=result)

    # ボタンの入力を受け取るPostbackEvent
    @handler.add(PostbackEvent)
    def on_postback(event):

        # プロフィール情報を取得
        profile = line_bot_api.get_profile(event.source.user_id)

        # 予約時間を選択（yyyy-mm-dd）
        if len(event.postback.data) == 10:

            # 選択された予約日を追記保存
            try:
                array = pickle.load(open(profile.user_id, "rb"))
                f = open(profile.user_id, "wb")
                if len(array) < 3:
                    array.insert(2, event.postback.data)
                else:
                    array[2] = event.postback.data
                pickle.dump(array, f)
                f.close()
                print("予約時間を選択")

                # メッセージを送信
                content = {
                    "type": "flex",
                    "altText": "予約時間を以下よりご選択ください。",
                    "contents": {
                        "type": "bubble",
                        "header": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "image",
                                    "url": "https://res.cloudinary.com/dfnnruqnc/image/upload/v1632133381/cafe%20unelma/step2_nbor66.png",
                                    "size": "full",
                                    "aspectRatio": "7:1"
                                }
                            ]
                        },
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
            except FileNotFoundError:
                print("error!")
                # メッセージを送信
                content = {
                    "type": "flex",
                    "altText": "前回の選択から時間が経過したため、大変お手数ですが再度ご予約をお願いいたします。",
                    "contents": {
                        "type": "bubble",
                        "direction": "ltr",
                        "body": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "前回の選択から時間が経過したため、大変お手数ですが再度ご予約をお願いいたします。",
                                    "weight": "bold",
                                    "color": "#FF0000",
                                    "align": "start",
                                    "wrap": True,
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
                                                "type": "message",
                                                "label": "予約する",
                                                "text": "予約"
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
                

        # 人数を選択
        if event.postback.data == "11:00" \
            or event.postback.data == "12:00" \
            or event.postback.data == "13:00" \
            or event.postback.data == "14:00" \
            or event.postback.data == "15:00" \
            or event.postback.data == "16:00" \
            or event.postback.data == "17:00" \
            or event.postback.data == "18:00" \
            or event.postback.data == "19:00":

            try:
                # 選択された予約時間を追記保存
                array = pickle.load(open(profile.user_id, "rb"))
                f = open(profile.user_id, "wb")
                if len(array) < 4:
                    array.insert(3, event.postback.data)
                else:
                    array[3] = event.postback.data
                pickle.dump(array, f)
                f.close()
                print("予約人数を選択")

                # 編集スコープの設定(読み書き両方OKの設定)
                SCOPES = ["https://www.googleapis.com/auth/calendar"]
                # カレンダーIDの設定
                calendar_id = os.environ["MAIL"]
                # 認証ファイルを使用して認証用オブジェクトを作成
                gapi_creds = google.auth.load_credentials_from_file("credentials.json", SCOPES)[0]
                # 認証用オブジェクトを使用してAPIを呼び出すためのオブジェクト作成
                service = googleapiclient.discovery.build("calendar", "v3", credentials=gapi_creds)

                # 予約の重複を確認
                events_result = service.events().list(
                    calendarId=calendar_id,
                    timeMin=f"{array[2]}T00:00:00+00:00",
                    singleEvents=True,
                    orderBy="startTime"
                ).execute()
                events = events_result.get("items", [])

                availability = ["default"]
                for appointment in events:
                    start = appointment["start"].get("dateTime", appointment["start"].get("date"))
                    if f"{array[2]}T{array[3]}" in start:
                        availability.append("no")
                    else:
                        availability.append("yes")

                # メッセージを送信（予約不可の場合）
                if "no" in availability:
                    print("選択された日時の予約はできません。")
                    content = {
                        "type": "flex",
                        "altText": "大変申し訳ございません。予約が満席に達してしまったため、大変お手数ですが再度予約時間をご選択ください。",
                        "contents": {
                            "type": "bubble",
                            "header": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "大変申し訳ございません。",
                                        "weight": "bold",
                                        "color": "#FF0000",
                                        "align": "start",
                                        "wrap": True,
                                        "contents": []
                                    },
                                    {
                                        "type": "text",
                                        "text": "予約が満席に達してしまったため、大変お手数ですが再度予約時間をご選択ください。",
                                        "weight": "bold",
                                        "color": "#FF0000",
                                        "align": "start",
                                        "wrap": True,
                                        "contents": []
                                    },
                                    {
                                        "type": "image",
                                        "url": "https://res.cloudinary.com/dfnnruqnc/image/upload/v1632133381/cafe%20unelma/step2_nbor66.png",
                                        "margin": "xl",
                                        "size": "full",
                                        "aspectRatio": "7:1"
                                    }
                                ]
                            },
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
                # メッセージを送信（予約可能の場合）
                else:
                    print("選択された日時の予約が可能です。")
                    content = {
                        "type": "flex",
                        "altText": "予約人数を以下よりご選択ください。",
                        "contents": {
                            "type": "bubble",
                            "header": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "image",
                                        "url": "https://res.cloudinary.com/dfnnruqnc/image/upload/v1632133381/cafe%20unelma/step3_wpinh5.png",
                                        "size": "full",
                                        "aspectRatio": "7:1"
                                    }
                                ]
                            },
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
            except FileNotFoundError:
                print("error!")
                # メッセージを送信
                content = {
                    "type": "flex",
                    "altText": "前回の選択から時間が経過したため、大変お手数ですが再度ご予約をお願いいたします。",
                    "contents": {
                        "type": "bubble",
                        "direction": "ltr",
                        "body": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "前回の選択から時間が経過したため、大変お手数ですが再度ご予約をお願いいたします。",
                                    "weight": "bold",
                                    "color": "#FF0000",
                                    "align": "start",
                                    "wrap": True,
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
                                                "type": "message",
                                                "label": "予約する",
                                                "text": "予約"
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

        # 最終確認（X名様）
        if len(event.postback.data) == 3:

            try:
                # 選択された人数を追記保存
                array = pickle.load(open(profile.user_id, "rb"))
                f = open(profile.user_id, "wb")
                if len(array) < 5:
                    array.insert(4, event.postback.data)
                else:
                    array[4] = event.postback.data
                pickle.dump(array, f)
                f.close()
                reservation = pickle.load(open(profile.user_id, "rb"))
                print("予約内容の確認")

                # 予約日を月日に変換
                reservation_date = reservation[2][5:].replace("-", "月").lstrip("0") + "日(木)"

                # 編集スコープの設定(読み書き両方OKの設定)
                SCOPES = ["https://www.googleapis.com/auth/calendar"]
                # カレンダーIDの設定
                calendar_id = os.environ["MAIL"]
                # 認証ファイルを使用して認証用オブジェクトを作成
                gapi_creds = google.auth.load_credentials_from_file("credentials.json", SCOPES)[0]
                # 認証用オブジェクトを使用してAPIを呼び出すためのオブジェクト作成
                service = googleapiclient.discovery.build("calendar", "v3", credentials=gapi_creds)

                # 予約の重複を確認
                events_result = service.events().list(
                    calendarId=calendar_id,
                    timeMin=f"{array[2]}T00:00:00+00:00",
                    singleEvents=True,
                    orderBy="startTime"
                ).execute()
                events = events_result.get("items", [])

                availability = ["default"]
                for appointment in events:
                    start = appointment["start"].get("dateTime", appointment["start"].get("date"))
                    if f"{array[2]}T{array[3]}" in start:
                        availability.append("no")
                    else:
                        availability.append("yes")

                # メッセージを送信（予約不可の場合）
                if "no" in availability:
                    print("選択された日時の予約はできません。")
                    content = {
                        "type": "flex",
                        "altText": "大変申し訳ございません。予約が満席に達してしまったため、大変お手数ですが再度予約時間をご選択ください。",
                        "contents": {
                            "type": "bubble",
                            "header": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "大変申し訳ございません。",
                                        "weight": "bold",
                                        "color": "#FF0000",
                                        "align": "start",
                                        "wrap": True,
                                        "contents": []
                                    },
                                    {
                                        "type": "text",
                                        "text": "予約が満席に達してしまったため、大変お手数ですが再度予約時間をご選択ください。",
                                        "weight": "bold",
                                        "color": "#FF0000",
                                        "align": "start",
                                        "wrap": True,
                                        "contents": []
                                    },
                                    {
                                        "type": "image",
                                        "url": "https://res.cloudinary.com/dfnnruqnc/image/upload/v1632133381/cafe%20unelma/step2_nbor66.png",
                                        "margin": "xl",
                                        "size": "full",
                                        "aspectRatio": "7:1"
                                    }
                                ]
                            },
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
                # メッセージを送信（予約可能の場合）
                else:
                    content = {
                        "type": "flex",
                        "altText": "ご予約はこちらでお間違いないでしょうか？",
                        "contents": {
                            "type": "bubble",
                            "header": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "image",
                                        "url": "https://res.cloudinary.com/dfnnruqnc/image/upload/v1632133381/cafe%20unelma/step4_sjezbu.png",
                                        "size": "full",
                                        "aspectRatio": "7:1"
                                    }
                                ]
                            },
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
                                    },
                                    {
                                        "type": "separator",
                                        "margin": "lg"
                                    },
                                    {
                                        "type": "text",
                                        "text": "※連続でタップするとエラーメッセージが表示されますのでご注意ください。ご予約通知が届いていればご予約は完了しております。",
                                        "size": "xs",
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
            except FileNotFoundError:
                print("error!")
                # メッセージを送信
                content = {
                    "type": "flex",
                    "altText": "前回の選択から時間が経過したため、大変お手数ですが再度ご予約をお願いいたします。",
                    "contents": {
                        "type": "bubble",
                        "direction": "ltr",
                        "body": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "前回の選択から時間が経過したため、大変お手数ですが再度ご予約をお願いいたします。",
                                    "weight": "bold",
                                    "color": "#FF0000",
                                    "align": "start",
                                    "wrap": True,
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
                                                "type": "message",
                                                "label": "予約する",
                                                "text": "予約"
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

        # LINE通知（unelma用）
        if event.postback.data == "OK":

            # 予約情報を変数に格納
            try:
                reservation = pickle.load(open(profile.user_id, "rb"))

                # 予約日を月日に変換
                reservation_date = reservation[2][5:].replace("-", "月").lstrip("0") + "日(木)"

                # 編集スコープの設定(読み書き両方OKの設定)
                SCOPES = ["https://www.googleapis.com/auth/calendar"]
                # カレンダーIDの設定
                calendar_id = os.environ["MAIL"]
                # 認証ファイルを使用して認証用オブジェクトを作成
                gapi_creds = google.auth.load_credentials_from_file("credentials.json", SCOPES)[0]
                # 認証用オブジェクトを使用してAPIを呼び出すためのオブジェクト作成
                service = googleapiclient.discovery.build("calendar", "v3", credentials=gapi_creds)

                # 予約の重複を確認
                events_result = service.events().list(
                    calendarId=calendar_id,
                    timeMin=f"{reservation[2]}T00:00:00+00:00",
                    singleEvents=True,
                    orderBy="startTime"
                ).execute()
                events = events_result.get("items", [])

                availability = ["default"]
                for appointment in events:
                    start = appointment["start"].get("dateTime", appointment["start"].get("date"))
                    if f"{reservation[2]}T{reservation[3]}" in start:
                        availability.append("no")
                    else:
                        availability.append("yes")

                # メッセージを送信（予約不可の場合）
                if "no" in availability:
                    print("選択された日時の予約はできません。")
                    content = {
                        "type": "flex",
                        "altText": "大変申し訳ございません。予約が満席に達してしまったため、大変お手数ですが再度予約時間をご選択ください。",
                        "contents": {
                            "type": "bubble",
                            "header": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "大変申し訳ございません。",
                                        "weight": "bold",
                                        "color": "#FF0000",
                                        "align": "start",
                                        "wrap": True,
                                        "contents": []
                                    },
                                    {
                                        "type": "text",
                                        "text": "予約が満席に達してしまったため、大変お手数ですが再度予約時間をご選択ください。",
                                        "weight": "bold",
                                        "color": "#FF0000",
                                        "align": "start",
                                        "wrap": True,
                                        "contents": []
                                    },
                                    {
                                        "type": "image",
                                        "url": "https://res.cloudinary.com/dfnnruqnc/image/upload/v1632133381/cafe%20unelma/step2_nbor66.png",
                                        "margin": "xl",
                                        "size": "full",
                                        "aspectRatio": "7:1"
                                    }
                                ]
                            },
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
                # メッセージを送信（予約可能の場合）
                else:
                    # 取得済みの日時をdateオブジェクトに変換
                    tstr = f"{reservation[2]} {reservation[3]}:00"
                    tdatetime = datetime.datetime.strptime(tstr, '%Y-%m-%d %H:%M:%S')

                    register = {
                        # タイトル
                        "summary": f"{reservation[0]}様",
                        # 概要文
                        "description" : f"人数：{reservation[4]}",
                        # 開始時刻
                        "start": {
                            "dateTime": datetime.datetime(tdatetime.year, tdatetime.month, tdatetime.day, tdatetime.hour, 00).isoformat(),
                            "timeZone": "Japan"
                        },
                        # 終了時刻
                        "end": {
                            "dateTime": datetime.datetime(tdatetime.year, tdatetime.month, tdatetime.day, tdatetime.hour+2, 00).isoformat(),
                            "timeZone": "Japan"
                        }
                    }

                    # カレンダーに予定を登録
                    service.events().insert(calendarId=calendar_id, body=register).execute()

                    # unelmaへメッセージを送信
                    content = {
                        "type": "flex",
                        "altText": "cafe unelmaの予約を受け付けました！",
                        "contents": {
                            "type": "bubble",
                            "body": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "image",
                                        "url": "https://res.cloudinary.com/dfnnruqnc/image/upload/v1632096188/cafe%20unelma/cafe-unelma_%E3%83%AD%E3%82%B4_p9w5ta.png",
                                        "size": "3xl"
                                    },
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

                    PUSH_USER_ID = os.environ["PUSH_USER_ID"] 
                    line_bot_api.push_message(PUSH_USER_ID, messages=result)

                    # メッセージを送信（お客様用）
                    content = {
                        "type": "flex",
                        "altText": "ご予約ありがとうございます。",
                        "contents": {
                            "type": "bubble",
                            "body": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "image",
                                        "url": "https://res.cloudinary.com/dfnnruqnc/image/upload/v1632096188/cafe%20unelma/cafe-unelma_%E3%83%AD%E3%82%B4_p9w5ta.png",
                                        "size": "3xl"
                                    },
                                    {
                                        "type": "text",
                                        "text": f"ご予約ありがとうございます！",
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
                    # 予約情報のファイルを削除
                    os.remove(reservation[1])

                result = FlexSendMessage.new_from_json_dict(content)
                line_bot_api.push_message(profile.user_id, messages=result)
            except FileNotFoundError:
                print("error!")
                # メッセージを送信
                content = {
                    "type": "flex",
                    "altText": "前回の選択から時間が経過したため、大変お手数ですが再度ご予約をお願いいたします。",
                    "contents": {
                        "type": "bubble",
                        "direction": "ltr",
                        "body": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "前回の選択から時間が経過したため、大変お手数ですが再度ご予約をお願いいたします。",
                                    "weight": "bold",
                                    "color": "#FF0000",
                                    "align": "start",
                                    "wrap": True,
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
                                                "type": "message",
                                                "label": "予約する",
                                                "text": "予約"
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

        if event.postback.data == "キャンセル":

            try:
                # 予約情報のファイルを削除
                reservation = pickle.load(open(profile.user_id, "rb"))
                os.remove(reservation[1])

                # メッセージを送信（お客様用）
                content = {
                    "type": "flex",
                    "altText": "ご予約をキャンセルしました",
                    "contents": {
                        "type": "bubble",
                        "direction": "ltr",
                        "body": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "ご予約をキャンセルしました",
                                    "weight": "bold",
                                    "align": "center",
                                    "contents": []
                                }
                            ]
                        }
                    }
                }
                result = FlexSendMessage.new_from_json_dict(content)
                line_bot_api.push_message(profile.user_id, messages=result)
            except FileNotFoundError:
                print("error!")
                # メッセージを送信
                content = {
                    "type": "flex",
                    "altText": "前回の選択から時間が経過したため、大変お手数ですが再度ご予約をお願いいたします。",
                    "contents": {
                        "type": "bubble",
                        "direction": "ltr",
                        "body": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "前回の選択から時間が経過したため、大変お手数ですが再度ご予約をお願いいたします。",
                                    "weight": "bold",
                                    "color": "#FF0000",
                                    "align": "start",
                                    "wrap": True,
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
                                                "type": "message",
                                                "label": "予約する",
                                                "text": "予約"
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