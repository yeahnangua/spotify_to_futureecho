#请在.env 文件中配置 Navidrome 相关信息和 Spotify API 凭据
#请在.env 文件中配置 Navidrome 相关信息和 Spotify API 凭据
#请在.env 文件中配置 Navidrome 相关信息和 Spotify API 凭据

import os
import logging
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from opencc import OpenCC
from dotenv import load_dotenv
import requests
import hashlib
import random
import string
import time
import re

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class NavidromeClient:
    def __init__(self, url, username, password):
        self.url = url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.version = '1.16.1'
        self.client_name = 'SpotifyToNavidrome'

    def _get_auth_params(self):
        # Generate salt
        salt = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        # Create token: md5(password + salt)
        token = hashlib.md5((self.password + salt).encode('utf-8')).hexdigest()
        return {
            'u': self.username,
            't': token,
            's': salt,
            'v': self.version,
            'c': self.client_name,
            'f': 'json'
        }

    def ping(self):
        try:
            params = self._get_auth_params()
            response = self.session.get(f"{self.url}/rest/ping.view", params=params, verify=True)
            response.raise_for_status()
            data = response.json()
            return data.get('subsonic-response', {}).get('status') == 'ok'
        except Exception as e:
            logger.error(f"Ping failed: {e}")
            return False

    def search(self, query, count=5):
        params = self._get_auth_params()
        params.update({
            'query': query,
            'songCount': count
        })
        try:
            # 使用 search3 接口
            response = self.session.get(f"{self.url}/rest/search3.view", params=params, verify=True)
            response.raise_for_status()
            data = response.json()
            resp = data.get('subsonic-response', {})
            if resp.get('status') == 'ok':
                return resp.get('searchResult3', {}).get('song', [])
            else:
                logger.error(f"Search API returned error: {resp.get('error')}")
                return []
        except Exception as e:
            logger.error(f"Search request failed: {e}")
            return []

    def get_playlists(self, name_filter=None):
        params = self._get_auth_params()
        try:
            response = self.session.get(f"{self.url}/rest/getPlaylists.view", params=params, verify=True)
            response.raise_for_status()
            data = response.json()
            resp = data.get('subsonic-response', {})
            if resp.get('status') == 'ok':
                playlists = resp.get('playlists', {}).get('playlist', [])
                if name_filter:
                    return [p for p in playlists if p['name'] == name_filter]
                return playlists
            else:
                logger.error(f"GetPlaylists API returned error: {resp.get('error')}")
                return []
        except Exception as e:
            logger.error(f"GetPlaylists request failed: {e}")
            return []

    def create_playlist(self, name, song_ids):
        params = self._get_auth_params()
        params.update({
            'name': name,
            'songId': song_ids
        })
        try:
            response = self.session.get(f"{self.url}/rest/createPlaylist.view", params=params, verify=True)
            response.raise_for_status()
            data = response.json()
            resp = data.get('subsonic-response', {})
            if resp.get('status') == 'ok':
                return resp.get('playlist')
            else:
                logger.error(f"CreatePlaylist API returned error: {resp.get('error')}")
                return None
        except Exception as e:
            logger.error(f"CreatePlaylist request failed: {e}")
            return None

    def update_playlist(self, playlist_id, song_ids):
        # updatePlaylist 接口用于添加/删除歌曲
        # songIdToAdd: ID of the song to add to the playlist.
        params = self._get_auth_params()
        params.update({
            'playlistId': playlist_id,
            'songIdToAdd': song_ids
        })
        try:
            response = self.session.get(f"{self.url}/rest/updatePlaylist.view", params=params, verify=True)
            response.raise_for_status()
            data = response.json()
            resp = data.get('subsonic-response', {})
            return resp.get('status') == 'ok'
        except Exception as e:
            logger.error(f"UpdatePlaylist request failed: {e}")
            return False

def get_spotify_songs():
    # Load environment variables
    # Configure requests session with language headers
    session = requests.Session()
    session.headers.update({'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'})

    # Spotify Authentication
    scope = "user-library-read"
    try:
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope), requests_session=session)
        logger.info("Spotify 连接成功")
    except Exception as e:
        logger.error(f"Spotify 连接失败: {e}")
        return []

    # Initialize OpenCC
    cc = OpenCC('t2s')

    logger.info("开始从 Spotify 获取已点赞歌曲...")
    
    # 全量获取
    results = sp.current_user_saved_tracks(limit=50, market='TW')
    tracks = results['items']
    
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
    
    song_list = []
    
    logger.info(f"获取到 {len(tracks)} 首歌，正在写入本地文件...")
    
    with open('liked_songs.txt', 'w', encoding='utf-8') as f:
        for item in tracks:
            track = item['track']
            track_name = track['name']
            artist_name = track['artists'][0]['name']

            # Convert to Simplified Chinese
            track_name_simp = cc.convert(track_name)
            artist_name_simp = cc.convert(artist_name)

            # Format: Name - Artist
            line = f"{track_name_simp} - {artist_name_simp}"
            f.write(line + "\n")
            
            song_list.append({'name': track_name_simp, 'artist': artist_name_simp})
            
    return song_list

def load_local_songs():
    file_path = 'liked_songs.txt'
    if not os.path.exists(file_path):
        return None
    
    if os.path.getsize(file_path) == 0:
        return None
        
    logger.info(f"发现本地文件 {file_path}，正在读取...")
    songs = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Try to split by last " - " in case song name contains hyphen
            parts = line.rsplit(' - ', 1)
            if len(parts) == 2:
                songs.append({'name': parts[0], 'artist': parts[1]})
            else:
                # Fallback or skip
                logger.warning(f"无法解析行: {line}")
                
    return songs

def clean_track_name(name):
    # 去除括号及括号内的内容，支持中文和英文括号
    # 例子: "光年之外 (电影 《Passengers》 中国区主题曲)" -> "光年之外"
    return re.sub(r'\(.*?\)|（.*?）', '', name).strip()

def select_best_match(song_list):
    """
    从搜索结果中选择最佳匹配。
    优先选择非 Live 版本。如果只有 Live 版，则选择 Live 版。
    返回: (selected_song, is_live_forced)
    """
    if not song_list:
        return None, False
    
    non_live_songs = []
    for song in song_list:
        title = song.get('title', '').lower()
        if 'live' not in title:
            non_live_songs.append(song)
    
    if non_live_songs:
        # 找到非 Live 版本
        return non_live_songs[0], False
    else:
        # 只有 Live 版本，退而求其次
        return song_list[0], True

def main():
    load_dotenv()

    # Navidrome Configuration
    navidrome_url = os.getenv('NAVIDROME_URL')
    navidrome_user = os.getenv('NAVIDROME_USERNAME')
    navidrome_pass = os.getenv('NAVIDROME_PASSWORD')
    target_playlist_name = os.getenv('NAVIDROME_PLAYLIST')
    
    if not all([navidrome_url, navidrome_user, navidrome_pass, target_playlist_name]):
        logger.error("Navidrome 配置缺失，请检查 .env 文件 (确保 NAVIDROME_PLAYLIST 已填写)")
        return

    # Initialize Navidrome Client
    navi_client = NavidromeClient(navidrome_url, navidrome_user, navidrome_pass)
    if navi_client.ping():
        logger.info(f"Navidrome 连接成功: {navidrome_url}")
    else:
        logger.error("Navidrome 连接失败，请检查 URL 和 账号密码")
        return

    # Try to load from local file first
    songs_to_process = load_local_songs()
    
    # If no local songs, fetch from Spotify
    if not songs_to_process:
        logger.info("本地文件为空或不存在，尝试从 Spotify 获取...")
        songs_to_process = get_spotify_songs()
        
    if not songs_to_process:
        logger.error("未能获取任何歌曲")
        return

    #Process ALL songs
    # total_songs = len(songs_to_process)
    # logger.info(f"开始处理 {total_songs} 首歌曲...")

    # 限制只处理前 30 首 (测试用)
    songs_to_process = songs_to_process[:40]
    total_songs = len(songs_to_process)
    logger.info(f"本次仅处理前 {total_songs} 首歌曲 (测试模式)")

    matched_song_ids = []
    failed_songs = []
    success_count = 0
    fail_count = 0

    for index, song in enumerate(songs_to_process, 1):
        track_name = song['name']
        artist_name = song['artist']
        
        # 简化日志，每10首打印一次
        if index % 10 == 1 or index == total_songs:
            logger.info(f"正在处理进度: [{index}/{total_songs}] ...")

        # === 策略 1: 搜索 "歌名 歌手" ===
        search_query_1 = f"{track_name} {artist_name}"
        results = navi_client.search(search_query_1)
        
        matched_song, is_live_forced = select_best_match(results)
        
        if not matched_song:
            # === 策略 2: 降级搜索，去除括号，只搜 "歌名" ===
            cleaned_name = clean_track_name(track_name)
            if cleaned_name != track_name: # 只有当清理后名字发生变化时才尝试
                search_query_2 = cleaned_name
                # logger.info(f"    尝试降级搜索: {search_query_2}")
                results = navi_client.search(search_query_2)
                matched_song, is_live_forced = select_best_match(results)

        # === 结果处理 ===
        if matched_song:
            matched_song_ids.append(matched_song.get('id'))
            success_count += 1
            
            # 只显示 "仅Live" 的匹配，隐藏普通匹配以减少干扰
            if is_live_forced:
                logger.warning(f"    ⚠️ 找到匹配 (仅Live): {matched_song.get('title')} - {matched_song.get('artist')}")
            # else:
            #     # 普通匹配不打印日志
            #     pass
        else:
            logger.warning(f"    ❌ 未找到匹配: {track_name}")
            fail_count += 1
            failed_songs.append(f"{track_name} - {artist_name}")
            
        # Add a small delay to be nice to the server
        time.sleep(0.1)

    logger.info("="*30)
    logger.info("搜索匹配完成")
    logger.info(f"总计: {total_songs}")
    logger.info(f"匹配成功: {success_count}")
    logger.info(f"匹配失败: {fail_count}")

    # 写入失败列表
    if failed_songs:
        with open('failed.txt', 'w', encoding='utf-8') as f:
            for line in failed_songs:
                f.write(line + "\n")
        logger.info(f"已将 {len(failed_songs)} 首未匹配歌曲写入 failed.txt")

    if not matched_song_ids:
        logger.warning("没有匹配到任何歌曲，无需操作歌单。")
        return

    # Playlist Operation
    logger.info(f"正在处理歌单: {target_playlist_name}")
    
    # Check if playlist exists
    existing_playlists = navi_client.get_playlists(target_playlist_name)
    
    if existing_playlists:
        playlist = existing_playlists[0]
        playlist_id = playlist['id']
        logger.info(f"歌单 '{target_playlist_name}' 已存在 (ID: {playlist_id})，正在添加歌曲...")
        
        # Subsonic updatePlaylist 可能有 URL 长度限制，虽然 GET 请求通常可以很长，但为了安全起见，分批添加是个好习惯
        # 假设一次添加 50 首
        batch_size = 50
        for i in range(0, len(matched_song_ids), batch_size):
            batch = matched_song_ids[i:i+batch_size]
            if navi_client.update_playlist(playlist_id, batch):
                logger.info(f"    Batch {i//batch_size + 1} 添加成功 ({len(batch)} 首)")
            else:
                logger.error(f"    Batch {i//batch_size + 1} 添加失败")
            time.sleep(0.5)
            
    else:
        logger.info(f"歌单 '{target_playlist_name}' 不存在，正在创建...")
        # createPlaylist 也可以一次性传很多 songId，同样分批可能不适用（create必须一次性？不，create 必须至少创建一个，后续可以用 update）
        # 策略：用前 50 首创建歌单，剩下的用 update 追加
        
        initial_batch = matched_song_ids[:50]
        remaining_batch = matched_song_ids[50:]
        
        new_playlist = navi_client.create_playlist(target_playlist_name, initial_batch)
        if new_playlist:
            logger.info(f"歌单创建成功 (ID: {new_playlist['id']})")
            
            if remaining_batch:
                logger.info("正在追加剩余歌曲...")
                batch_size = 50
                for i in range(0, len(remaining_batch), batch_size):
                    batch = remaining_batch[i:i+batch_size]
                    if navi_client.update_playlist(new_playlist['id'], batch):
                        logger.info(f"    Batch {i//batch_size + 1} 追加成功 ({len(batch)} 首)")
                    else:
                        logger.error(f"    Batch {i//batch_size + 1} 追加失败")
                    time.sleep(0.5)
        else:
            logger.error("歌单创建失败")

    logger.info("全部任务完成！")

if __name__ == "__main__":
    main()
