import requests
import json
import m3u8
import os
import datetime
from time import sleep
from bs4 import BeautifulSoup

class tiktok_load_stream:
    def __init__(self, account_id):
        self.headers = {
            'Cookie': 'tt_csrf_token=Io8ixUuY-ik61Kvsp-1l6GpXZz4j1dYloWG4; ttwid=1%7CWV6WiB1CQrvIunmIL36_3xoaXXz6jtWxMZcy7EwJ0L4%7C1691689599%7C280de2f4ca3cc8a04a6c09b5813a4a1197a6bd1d18d2d89d4e54274bce977e8b'
        }
        self.account_id = account_id
        dt_now = datetime.datetime.now()
        self.dir_name = dt_now.strftime(f'{account_id}-%Y-%m-%d-%H-%M')
        self.m3u8Data = None
        self.m3u8_url = None
        self.sequence = [] # 10個のスタック
        self.playlist_write_flag = False
    
    def get_m3u8_url(self, quality: str):
        """quality is video quality. ao | ld | origin | sd | uhd"""
        url = f"https://www.tiktok.com/@{self.account_id}/live"
        getHtmlContext = requests.get(url, headers=self.headers)
        html = BeautifulSoup(getHtmlContext.text, 'html.parser')
        tiktokState = html.select('#SIGI_STATE')[0].string
        tiktokStateData = json.loads(str(tiktokState))
        try:
            streamState = json.loads(tiktokStateData['LiveRoom']['liveRoomUserInfo']['liveRoom']['streamData']['pull_data']['stream_data'])
            # 画質プロパティ：ao, ld, origin, sd, uhd
            print("video quality list: ", end="")
            print(
                [ quality['sdk_key'] for 
                    quality in tiktokStateData['LiveRoom']['liveRoomUserInfo']['liveRoom']['streamData']['pull_data']['options']['qualities'] ]
            )
            stream_m3u8_url = streamState['data'][quality]['main']['hls']
            self.m3u8_url = stream_m3u8_url

            # ライブ配信の状態 2-配信中, 4-配信終了
            if 4 == tiktokStateData['LiveRoom']['liveRoomUserInfo']['user']['status']:
                print("not live.")
                return False

            return True
        except Exception as e:
            print(e)
            print("not live.")
            return False

    # m3u8の読み込みと更新
    def load_m3u8(self):
        try:
            self.m3u8Data = m3u8.load(self.m3u8_url)
            return True
        except:
            print(".m3u8 file is not found.")
            return False
    
    def download_m3u8_playlist(self):
        # ディレクトリの作成
        if not os.access(self.dir_name, os.F_OK):
            os.mkdir(self.dir_name)
        # Playlistの保存
        self.m3u8Data.dump(f'{self.dir_name}/playlist.m3u8')

    def download(self):
        # シーケンス取得
        for seg in self.m3u8Data.segments:
            tsFileName = seg.uri
            if not tsFileName in self.sequence:
                print(seg.uri)
                self.sequence.append(tsFileName)
                # tsの保存
                try:
                    with open(f"{self.dir_name}/" + seg.uri, 'wb') as f:
                        f.write( requests.get(seg.absolute_uri, timeout=10).content )
                except:
                    print("end the stream and finished download.")
                    self.stop()
                    return False

                # m3u8に追記
                if self.playlist_write_flag:
                    with open(f'{self.dir_name}/playlist.m3u8', 'a') as f:
                        f.write(f'#EXTINF:{seg.duration},\n{seg.uri}\n')

        # シーケンス更新（10個にする）
        if len(self.sequence) > 10:
            self.sequence = self.sequence[len(self.sequence)-10:]

        self.playlist_write_flag = True
        sleep(5)
        self.load_m3u8()
        self.download()

    def stop(self):
        with open(f'{self.dir_name}/playlist.m3u8', 'a') as f:
            f.write('#EXT-X-ENDLIST\n')



liver_list = ['harrytickerkun']
def main():
    try:
        for user_id in liver_list:
            stream = tiktok_load_stream(user_id)
            status = stream.get_m3u8_url(quality='origin')
            if status:
                print(f"live: {user_id}")
    except KeybordIntterupt:
        print('KeyboardInterrupt')

while True:
    print("check " + str(datetime.datetime.now()))
    main()
    sleep(60*5)
