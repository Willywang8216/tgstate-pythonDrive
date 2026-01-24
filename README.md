# tgstate-python

**基于 Telegram 的无限私有云存储 & 永久图床系统**

将您的 Telegram 频道或群组瞬间变身为功能强大的私有网盘与图床。无需服务器存储空间，借助 Telegram 的无限云端能力，实现文件管理、外链分享、图片托管等功能。

---

## 一键脚本（推荐）

### 1. 一键安装 / 一键更新（保留数据，推荐）
```bash
bash -lc 'bash <(curl -fsSL https://raw.githubusercontent.com/buyi06/tgstate-python/main/scripts/install.sh)'
```

### 2. 一键重建容器（保留数据，专治容器跑飞）
```bash
bash -lc 'bash <(curl -fsSL https://raw.githubusercontent.com/buyi06/tgstate-python/main/scripts/reset.sh)'
```

### 3. 一键彻底清理（清空数据，不可逆）
```bash
bash -lc 'bash <(curl -fsSL https://raw.githubusercontent.com/buyi06/tgstate-python/main/scripts/purge.sh)'
```

> 💡 运行脚本时会提示输入端口（回车默认 8000），也可通过环境变量跳过交互：`PORT=15767 BASE_URL=https://...`

---

## ⚙️ 首次配置與 .env 範例（支援多頻道 / 多群組）

部署後首次訪問網頁，會進入「引導頁」設定管理員密碼。之後請進入 **「系統設定」** 完成核心配置。  
如果你是用 Docker / 一鍵腳本部署，也可以直接透過 `.env` 檔設定環境變數。

### 第一步：取得 BOT_TOKEN
1. 在 Telegram 搜尋 **[@BotFather](https://t.me/BotFather)** 並點「Start」。
2. 傳送指令 `/newbot` 建立新機器人。
3. 依照提示輸入 Name（顯示名稱）與 Username（帳號，必須以 `bot` 結尾）。
4. 建立成功後，BotFather 會回傳一段文字，其中  
   `Use this token to access the HTTP API:` 下方那串字串就是 **BOT_TOKEN**。

### 第二步：取得 Chat ID / 頻道 ID（CHANNEL_NAME）

你可以使用「公開 @username」或「數字 ID」兩種方式標識頻道 / 群組：

- 公開頻道 / 群組：使用 `@channel_username` 或 `@group_username`
- 私有頻道 / 群組：使用數字 ID，通常長得像 `-1001234567890`

**取得方式 A：用 getUpdates（適合單一頻道）**

1. 建立一個頻道或群組（公開或私有皆可）。
2. **務必將機器人加入該頻道 / 群組，並設為「管理員」**（至少要有讀取訊息與發送訊息權限）。
3. 在該頻道/群組裡隨便發一則訊息。
4. 在瀏覽器開啟：  
   `https://api.telegram.org/bot<你的Token>/getUpdates`  
   （請把 `<你的Token>` 換成剛剛拿到的 BOT_TOKEN）
5. 查看回傳的 JSON，找到 `chat` 下的 `id` 欄位：
   - 若是頻道/超級群組，通常是 `-100xxxxxxxxxx` 這種格式。
6. 若該頻道是公開的，也會有 `username` 欄位，像 `my_channel_name`，這時你就可以直接在 CHANNEL_NAME 裡寫 `@my_channel_name`。

> **💡 小提醒**：  
> 如果 `getUpdates` 回傳 `"result": []`，請在群組多發幾則訊息，  
> 或到 @BotFather 關掉 Group Privacy：  
> `/mybots` → 選擇你的 bot → Bot Settings → Group Privacy → Turn off

**取得方式 B：支援多個頻道 / 群組（多頻道模式）**

本專案現在支援 **多個頻道 / 群組 同時使用**，你可以：

- 建立多個頻道（例如：  
  - `@team_media`：團隊素材  
  - `@team_archive`：歸檔備份  
  - `-1001234567890`：私有群組收集原始檔）
- 把同一個 Bot 加入所有相關頻道 / 群組，並設為管理員。
- 對每個頻道重複上述步驟，取得每一個頻道的 `@username` 或數字 ID。

### 第三步：設定 .env / 系統設定（支援多頻道）

你可以選擇：

- 直接修改 `.env`（自架 / Docker 常用）
- 或在 Web 頁面的「系統設定」輸入對應欄位（會寫入資料庫，優先於 .env）

`.env` 範例（多頻道版本）：

```env
BOT_TOKEN=1234567890:AA...your_bot_token...

# 同時監聽多個頻道 / 群組，逗號或分號皆可：
# - 使用 @username（公開頻道/群組）
# - 使用 -100 開頭的數字 ID（私有頻道/群組）
# 第一個條目會被視為「預設頻道」，Web 上未特別指定時就會傳到這裡
CHANNEL_NAME=@team_media,-100111222333,987654321

# Web 管理後台密碼（可選）
PASS_WORD=你的管理密碼

# PicGo 上傳用 API Key（可選）
PICGO_API_KEY=your_picgo_api_key

# 對外分享時使用的基底網址（建議設定成你的網域）
BASE_URL=https://pan.example.com
```

對應到 Web「系統設定」：

- **BOT_TOKEN**：第一步取得的 Token。
- **CHANNEL_NAME**：
  - 單頻道：可填 `@my_channel` 或 `-1001234567890`
  - 多頻道：支持 `@ch1,-100xxx,123456789` 或 `@ch1; -100xxx; 123456789`
  - 前端會自動解析為多個頻道，並在上傳區顯示可搜尋的頻道清單。
- **BASE_URL**（可選）：你實際對外提供服務的網址，例如：
  - `http://1.2.3.4:8000`
  - `https://pan.example.com`（有反向代理時建議設定）

> **注意（多頻道模式）**：
> - Bot 一定要加進所有你填在 CHANNEL_NAME 裡的頻道 / 群組，否則對某些頻道的刪除 / 上傳會失敗。
> - 老的「單頻道配置」仍然完全可用，你只要填一個值即可，行為和舊版一致。

保存後即可開始使用！

---

## 🌐 反向代理说明 (Caddy/Nginx)

如果您使用 Caddy/Nginx 等反向代理工具，请注意以下几点：

### 1. Cookie 与 HTTPS
系统已优化 Cookie 策略，支持在 HTTP (IP:Port) 和 HTTPS 环境下自动适配。但如果您在反代层开启了 HTTPS，请确保将请求头正确透传。

### 2. Caddy 配置示例
在您的 `Caddyfile` 中追加以下配置（仅供参考）：

```caddy
buyi.us.ci {
    encode gzip
    reverse_proxy 127.0.0.1:8000
}
```

### 3. Nginx 配置示例
确保透传 `Host` 和 `X-Forwarded-*` 头：

```nginx
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

---

## ❓ 常见问题排查

### Q: 登录后跳转回登录页 / 无法登录 / 500 错误？
*   **密码字符支持**：系统已修复 Cookie 存储问题，现在支持包含中文、空格、Emoji 等任意字符的强密码。
*   **500 Internal Server Error**：如果您在登录时遇到 500 错误，通常是因为旧版本未正确处理特殊字符 Cookie。请尝试清除浏览器 Cookie 或使用无痕模式。
*   **重置与排查**：
    *   查看日志：`docker logs tgstate --tail 200`
    *   **重置数据卷**（注意：这会清空所有数据！）：
        ```bash
        docker rm -f tgstate; docker volume rm tgstate-data; docker volume create tgstate-data
        ```
*   **检查密码**：设置密码时系统会自动去除首尾空格，请确认输入的密码无误。
*   **Cookie 问题**：如果您在本地开发环境使用 `localhost`，通常没问题。如果是 IP 访问，请确保浏览器没有禁用 Cookie。尝试点击浏览器地址栏的小锁/图标查看 Cookie 是否写入。
*   **重置配置**：如果实在无法登录，可以删除 `data/file_metadata.db` 中的 `app_settings` 表记录（需懂 SQL），或直接删除数据库文件（会丢失文件索引，不推荐）。

### Q: 退出登录点击无反应或报错？
*   退出登录使用了 JavaScript 弹窗确认，请确保页面 JS 已加载（查看控制台是否有报错）。
*   如果提示网络错误，请刷新页面重试。

### Q: 复制链接失败？
*   在非 HTTPS 环境下（如 HTTP IP 访问），浏览器可能会限制剪贴板 API。系统已内置回退机制，如果自动复制失败，会弹窗显示链接供您手动复制。
*   建议配置 HTTPS 反代以获得最佳体验。

### Q: 删除文件后列表不刷新？
*   删除操作是异步的。如果删除成功但列表未消失，可能是网络延迟。
*   请尝试刷新页面。如果文件仍在，说明删除失败（可能是 Bot 权限不足，请检查 Bot 是否为频道管理员）。

### Q: 分享链接是 127.0.0.1？
*   系统前端会自动根据您当前的浏览器地址生成分享链接。如果您看到 127.0.0.1，说明您就是通过 127.0.0.1 访问的。
*   请尝试用公网 IP 或域名访问网页，分享链接会自动变更为对应的 IP/域名。

---

## 📂 功能特性
*   **无限存储**：依赖 Telegram 频道，容量无上限。
*   **短链接分享**：生成简洁的分享链接（`/d/AbC123`），自动适配当前访问域名。
*   **拖拽上传**：支持批量拖拽上传，大文件自动分块。
*   **图床模式**：支持 Markdown/HTML 格式一键复制，适配 PicGo。
*   **隐私安全**：所有数据存储在您的私有频道，Web 端支持密码保护。

---

## 📺 在线预览 / 强制下载 / Range 说明（验收命令）

系统对分享链接 (`/d/{id}`) 提供了智能的 Content-Disposition 策略和流式支持：

1.  **默认策略**：
    *   **可预览类型**（图片、PDF、文本、代码、音视频）：返回 `Content-Disposition: inline`，浏览器会尝试直接在标签页中打开预览。
    *   **不可预览类型**（压缩包、二进制等）：返回 `Content-Disposition: attachment`，浏览器会直接触发下载。
2.  **强制下载**：
    *   在链接后添加 `?download=1` 参数（例如 `/d/GNW2KH?download=1`），无论文件类型，服务器一律返回 `attachment`，强制浏览器下载文件。
3.  **Range 支持（音视频播放）**：
    *   对于 `video/*` 和 `audio/*` 类型，服务器完整支持 HTTP Range 请求。
    *   响应包含 `206 Partial Content`、`Accept-Ranges: bytes` 和 `Content-Range` 头。
    *   这确保了在移动端（iOS/Android）和桌面端播放器中，您可以随意拖动进度条，支持断点续传。
4.  **HEAD 请求支持**：
    *   完整支持 `HEAD` 方法，返回与 `GET` 一致的 Headers（包含文件大小、类型等），方便反向代理缓存或下载工具探测。
5.  **浏览器兼容性提示**：
    *   不同浏览器对 PDF、视频编码（如 HEVC/MKV）的内置支持程度不同。如果遇到无法预览的情况，请尝试使用 `?download=1` 下载，或更换 Chrome/Edge 等现代浏览器。

### 🚀 一键验收命令

您可以在 Linux/macOS 终端中直接复制运行以下命令，验证服务器的响应头是否符合预期（请替换 `BASE_URL` 和 `ID` 为您的实际值）：

```bash
bash -lc '
set -euo pipefail
# 请修改为您自己的域名和文件ID
BASE="${BASE_URL:-https://pan.777256.xyz}"
ID="${ID:-GNW2KH}"
URL="${BASE%/}/d/${ID}"

# 获取最终跳转地址（处理可能的 HTTP->HTTPS 重定向）
FINAL="$(curl -sS -L -o /dev/null -w "%{url_effective}" --max-time 15 "$URL" || true)"; [ -n "$FINAL" ] || FINAL="$URL"

echo "URL=$URL"
echo "FINAL=$FINAL"
echo

echo "== 1. HEAD 请求 (应返回 200/206，不应是 405) =="
curl -sS -I --max-time 15 "$FINAL" | egrep -i "HTTP/|content-type|content-disposition|accept-ranges|content-range|content-length|x-content-type-options" || true
echo

echo "== 2. Default GET (可预览类型应 inline; 不可预览应 attachment) =="
curl -sS -L -D - -o /dev/null --max-time 20 "$FINAL" | egrep -i "HTTP/|content-type:|content-disposition:|accept-ranges:|content-range:|content-length:|x-content-type-options:" || true
echo

echo "== 3. GET ?download=1 (必须 attachment) =="
curl -sS -L -D - -o /dev/null --max-time 20 "$FINAL?download=1" | egrep -i "HTTP/|content-type:|content-disposition:" || true
echo

echo "== 4. Range bytes=0-1023 (音视频应 206 + Content-Range) =="
curl -sS -L -D - -o /dev/null --max-time 20 -H "Range: bytes=0-1023" "$FINAL" | egrep -i "HTTP/|accept-ranges:|content-range:|content-length:" || true
'
```

**✅ 验收通过标准：**
*   **HEAD**: 返回状态码 200 OK（或 302 跳转后的 200），且包含 `Content-Type` 等头信息。
*   **Default**: 对于 PDF/图片，`Content-Disposition` 应包含 `inline`。
*   **Download**: 带 `?download=1` 时，`Content-Disposition` 必须包含 `attachment`。
*   **Range**: 对于音视频文件，应返回 `HTTP/1.1 206 Partial Content` 且包含 `Content-Range` 头。

---
## 免责声明与合规使用（重要）

本项目基于 **Telegram Bot + 频道** 实现个人文件管理/分享能力。

- Telegram 的 Bot 平台条款对“将其用于**云存储类外部服务**”存在限制与风险  
- 本项目 **仅供学习与个人用途**  
- **严禁**用于以下场景：  
  - 侵权内容（盗版资源、未授权转载/传播等）  
  - 任何违法用途  
  - 公开资源分发/公共下载站  
  - 商业网盘/对外提供存储服务

使用本项目产生的任何后果由使用者自行承担；开发者不对由此造成的封号、数据丢失、法律风险等负责。


## 📄 License
MIT License
