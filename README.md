# Spotify to Navidrome Sync Tool

这是一个 Python 脚本，用于将你的 **Spotify 已点赞歌曲 (Liked Songs)** 自动同步到你的 **Navidrome** 个人音乐服务器的指定歌单中。

## ✨ 功能特点

*   **自动获取**：从 Spotify 获取你收藏的全部歌曲。
*   **智能匹配**：在 Navidrome 中自动搜索对应歌曲。
    *   自动进行**繁简转换** (例如：Spotify 上的 "光年之外" 即使是繁体，也能在 Navidrome 中匹配简体中文歌曲)。
    *   优先匹配**录音室版本**，如果只有 Live 版会自动降级匹配。
    *   智能去除歌名中的括号备注 (如 " (电影主题曲)") 提高匹配率。
*   **歌单管理**：
    *   如果 Navidrome 中指定歌单不存在，会自动创建。
    *   如果歌单已存在，会将新歌追加进去。
*   **本地缓存**：首次获取的歌单会保存为 `liked_songs.txt`，方便调试或备份。
*   **失败记录**：未匹配到的歌曲会记录在 `failed.txt` 中，方便后续手动查找。

## 🛠️ 准备工作

在开始之前，你需要准备：

1.  **Python 3.x** 环境。
2.  **Spotify 开发者应用**：
    *   访问 [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)。
    *   登录并在 Dashboard 中点击 "Create App"。
    *   App Name 和 Description 随意填写。
    *   在 **Redirect URI** 中，添加 `http://127.0.0.1:8888/callback`
    *   勾选 Web Playback SDK 和 Web API
    *   保存
    *   记录下 **Client ID** 和 **Client Secret**。
3.  **Navidrome 服务器**：你需要有自己的 Navidrome 地址、账号和密码。

## 🚀 安装与配置

### 1. 克隆或下载本项目

```bash
git clone https://github.com/yourusername/spotify_to_futureecho.git
cd spotify_to_futureecho
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

打开项目根目录下一个名为 `.env` 的文件，并填入以下内容：

```ini
# Navidrome 配置
NAVIDROME_URL=http://your-navidrome-url:4533
NAVIDROME_USERNAME=your_username
NAVIDROME_PASSWORD=your_password
NAVIDROME_PLAYLIST=Spotify_Liked  # 你想在 Navidrome 中创建/更新的歌单名称

# Spotify 配置 (从 Spotify Developer Dashboard 获取)
SPOTIPY_CLIENT_ID=your_spotify_client_id
SPOTIPY_CLIENT_SECRET=your_spotify_client_secret
SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback
```

## ▶️ 使用方法

### 运行脚本

```bash
python main.py
```

### 首次运行注意

第一次运行时，脚本会自动打开浏览器跳转到 Spotify 授权页面。 
点击同意授权。
之后脚本会自动保存 token 缓存，后续运行无需再次授权。

## 📂 文件说明

*   `liked_songs.txt`: 脚本运行后生成的 Spotify 歌曲列表缓存。如果想强制重新从 Spotify 拉取最新列表，请删除此文件。
*   `failed.txt`: 运行结束后生成，列出了在 Navidrome 中未找到匹配的歌曲。

## ⚠️ 注意事项

*   脚本默认会尝试将 Spotify 的繁体中文歌名转换为简体中文去匹配，以适应国内常见的音乐库命名习惯。

## 🤝 贡献

欢迎提交 Issue 或 Pull Request 来改进这个脚本！
