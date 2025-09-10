from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import re
import csv
import pandas as pd
import yt_dlp

def get_playlists_from_channel_playlists_tab(channel_playlists_url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(channel_playlists_url)

    time.sleep(5)

    last_height = driver.execute_script("return document.documentElement.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.documentElement.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    links = driver.find_elements(By.TAG_NAME, "a")
    playlist_data = []

    for link in links:
        href = link.get_attribute("href")
        title = link.get_attribute("title")
        if href and "list=" in href:
            match = re.search(r'list=([a-zA-Z0-9_-]+)', href)
            if match:
                playlist_id = match.group(1)
                playlist_data.append((title or "No title", playlist_id))

    driver.quit()
    return playlist_data

# Hàm lưu danh sách playlist vào CSV
def write_playlists_to_csv(data, filename="playlists.csv"):
    with open(filename, mode='w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Title", "Playlist ID"])
        writer.writerows(data)
    print(f"Saved {len(data)} playlists to '{filename}'")

# Hàm lấy thông tin video từ playlist
def get_videos_from_playlist(playlist_url):
    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        'skip_download': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(playlist_url, download=False)
            playlist_title = info.get('title', 'Unknown Playlist')
            videos = []

            if 'entries' in info:
                for entry in info['entries']:
                    title = entry.get('title')
                    video_id = entry.get('id')
                    if title and video_id:
                        embed_url = f"https://www.youtube.com/embed/{video_id}"
                        videos.append((title, embed_url))

            return playlist_title, videos
        except Exception as e:
            print(f"Lỗi khi xử lý playlist {playlist_url}: {e}")
            return None, []

channel_playlists_url = "https://www.youtube.com/@AniOneVietnam/playlists"  # URL playlist kênh
results = get_playlists_from_channel_playlists_tab(channel_playlists_url)

# === Lấy tên channel từ URL ===
channel_name = channel_playlists_url.split("@")[-1].replace("/playlists", "")
# Nếu là link dạng /channel/UCxxxx thì nên đổi sang cách khác, ở đây ta xử lý @handle

# File tạm cho playlists
playlists_csv = f"{channel_name}_playlists.csv"
playlists_cleaned_csv = f"{channel_name}_playlists_cleaned.csv"
videos_csv = f"{channel_name}_videos.csv"

# === Xuất playlists ban đầu ===
write_playlists_to_csv(results, output_file=playlists_csv)

# === Xóa trùng Playlist ID ===
df = pd.read_csv(playlists_csv)
df_cleaned = df.drop_duplicates(subset=['Playlist ID'], keep='first')
df_cleaned.to_csv(playlists_cleaned_csv, index=False)
print(f"Đã xóa các Playlist ID trùng lặp. Kết quả được lưu trong '{playlists_cleaned_csv}'.")

# === Cào video từ các playlist ===
all_videos_data = []
for index, row in df_cleaned.iterrows():
    playlist_id = row['Playlist ID']
    playlist_title_csv = row['Title']
    playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
    
    print(f"Đang xử lý playlist: {playlist_title_csv} ({playlist_url})")
    
    playlist_title, videos = get_videos_from_playlist(playlist_url)
    
    if playlist_title:
        print(f"Playlist: {playlist_title}\nTổng cộng: {len(videos)} video\n")
        for i, (video_title, embed_link) in enumerate(videos, 1):
            print(f"{i}. {video_title}\n   {embed_link}")
            all_videos_data.append({
                'Playlist Title': playlist_title_csv,
                'Playlist ID': playlist_id,
                'Video Title': video_title,
                'Embed URL': embed_link
            })
        print("\n")
    else:
        print(f"Không thể lấy dữ liệu từ playlist {playlist_url}\n")

# === Lưu thông tin video vào CSV theo tên channel ===
if all_videos_data:
    videos_df = pd.DataFrame(all_videos_data)
    videos_df.to_csv(videos_csv, index=False)
    print(f"Đã lưu thông tin video vào '{videos_csv}'.")
else:
    print("Không có dữ liệu video để lưu.")