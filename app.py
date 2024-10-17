from flask import Flask, render_template, request
import requests
import pandas as pd

app = Flask(__name__)

# 楽天APIの設定
API_URL = "https://app.rakuten.co.jp/services/api/Travel/KeywordHotelSearch/20170426?[parameter]=[value]…"
API_KEY = "1074298303244057275"  # 取得した楽天APIのアプリケーションIDに置き換えてください

# ホテル検索関数
def search_hotels(keyword):
    params = {
        'applicationId': API_KEY,
        'keyword': keyword,  # ユーザーが入力したキーワード（都道府県や地名、最寄駅）
        'smoking': 1,  # 喫煙可の部屋を検索
        'hits': 30,  # 最大30件取得
    }

    response = requests.get(API_URL, params=params)
    
    # APIのレスポンスが正常かチェック
    if response.status_code != 200:
        return pd.DataFrame(), "APIリクエストに失敗しました。"

    data = response.json()

    # データが見つからない場合
    if 'hotels' not in data:
        return pd.DataFrame(), "関連するホテルが見つかりませんでした。正しい地名や駅名を入力してください。"

    # ホテル情報をリストに変換
    hotels = []
    for hotel in data['hotels']:
        hotel_info = hotel['hotel'][0]['hotelBasicInfo']
        hotels.append({
            '画像': f'<img src="{hotel_info.get("hotelImageUrl", "#")}" style="width:100px;">',
            'ホテル名': hotel_info['hotelName'],
            '住所': hotel_info['address1'] + hotel_info['address2'],
            '最寄り駅': hotel_info['nearestStation'],
            '料金': f"{hotel_info.get('hotelMinCharge', '-')}円〜",  # 料金を表示
            '予約ページ': hotel_info['hotelInformationUrl']
        })

    # データをpandasデータフレームに変換
    df = pd.DataFrame(hotels).fillna('-')
    
    return df, None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        keyword = request.form.get('keyword')
        if keyword:
            hotels_df, error_message = search_hotels(keyword)
            if error_message:
                return render_template('hotels.html', tables=None, error=error_message)
            if hotels_df.empty:
                return render_template('hotels.html', tables=None, error="該当する喫煙可能なホテルは見つかりませんでした。")
            # HTMLのテーブルとしてデータフレームを表示
            hotels_df['予約ページ'] = hotels_df['予約ページ'].apply(lambda x: f'<a href="{x}" target="_blank">リンク</a>')
            hotels_html = hotels_df.to_html(classes='table table-striped', index=False, escape=False)
            hotels_html = hotels_html.replace('<th>画像</th>', '<th></th>')
            return render_template('hotels.html', tables=hotels_html, error=None)
        else:
            return render_template('hotels.html', tables=None, error="地名や駅名を入力してください。")
    return render_template('hotels.html', tables=None, error=None)

if __name__ == '__main__':
    app.run(debug=True)
