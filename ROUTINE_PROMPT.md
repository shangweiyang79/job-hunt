# 每週職缺雷達（Joy Yang）

你在 `job-hunt` repo 根目錄執行一次完整的每週職缺搜尋。所有面向使用者的文字用繁體中文。整個流程在這一輪內完成。

## 0. 準備
- `python -m pip install -q -r requirements.txt`。之後所有腳本都用同一個 `python` 執行，不要混用 `python3` 或單獨的 `pip`：雲端環境的 `pip` 指向另一個 Python 版本，會出現找不到 `requests` 的錯誤。
- `date -u +%F` 取得今天日期，算出 ISO 週次（例：2026-W43）。
- 讀 `config/criteria.yaml`、`profile/candidate_facts.md`、`data/seen_jobs.csv`。
- `candidate_facts.md` 是唯一事實來源。**不可虛構任何數字、經歷、工具或成果。**

## 1. 搜尋（過去 `window_days` 天）
- **104 不要從雲端抓**：104 會擋雲端 IP（HTTP 403）。每週一 08:30 使用者的電腦會把 104 結果（含完整 JD，在每筆的 `detail` 欄位）推到 `data/raw_jobs_local.json`。先 `git pull` 再讀這個檔：
  - `fetched_at` 在 3 天內：用它當 104 的來源，評分時直接讀 `detail`，不要再呼叫 `--detail 104:...`。
  - 檔案太舊或不存在（電腦沒開機）：104 標為「本週本機抓取未執行」，在 email 與週報中說明，不要嘗試從雲端抓 104。
- LinkedIn：`python scripts/search_sources.py --source linkedin --out data/raw_jobs.json`，失敗的來源會寫在 `errors` 欄位。
- LinkedIn 若回 429，改用 WebSearch：`site:linkedin.com/jobs/view "Data Analyst" Taipei`、`... Tokyo`。
- 依 `criteria.yaml` 的 `sources`，用 WebSearch / WebFetch 補搜 CakeResume、Yourator、TokyoDev、Japan Dev、Daijob / CareerCross。只收過去 7 天內刊登或更新、職稱符合 `include_title`、地點符合 `locations` 的職缺。
- 每個來源記下：成功 / 失敗（原因）/ 筆數。

## 2. 去重與排除
- 依 `source + job_id`（無 id 用 URL）比對 `seen_jobs.csv`，已出現過的跳過。
- 公司＋職稱符合 `already_applied` 的，標「已投遞」，不另行通知。
- 同一職缺出現在多個來源，只保留一筆。

## 3. 評分（0–100）
- 依 `scoring` 權重評分。分數 ≥ 60 的候選，**一定要讀完整 JD**（104 讀 `data/raw_jobs_local.json` 裡的 `detail`，其他來源用 WebFetch），不可只看標題。
- 每筆記錄：分數、3 點匹配理由（引用 JD 原文）、1–2 點缺口、職缺類型（DA/BI 或 DS/DE/AE）。
- 要誠實：JD 要求候選人沒有的硬技能（例如 Spark 生產經驗、5 年以上 DS 經驗）就扣分，不要為了湊高分而放水。

## 4. 高度匹配：客製化 CV（分數 ≥ `high_match_threshold`，取前 `max_tailored_per_week` 筆）
1. 選範本：
   - 台灣中文 JD → `templates/中文履歷_楊上瑋_數據分析師.pptx`（一頁含照片）。JD 要求自傳時，另外改 `templates/中文自傳_楊上瑋_資料分析師_通用版.docx`。
   - 英文 JD 或日本職缺 → DA/BI 用 `templates/Resume_Shangwei Yang_Data Analyst.docx`；DS/DE/AE 用 `templates/Resume_ Shangwei Yang_Data Scientist.docx`。
   - 日本職缺若要求日文履歷，在通知中註明「建議另備日文職務経歴書」。
2. 敘事：DA/BI 職缺用「洞察 → 建議 → 成效」，以競品分析與留存分析帶頭，工具放次要。DS/DE/AE 職缺強調管線、RAG＋evals、分類模型與方法嚴謹度。
3. 寫 `applications/<YYYY-MM-DD>_<公司>_<職稱>/spec.json`（格式見 `scripts/tailor.py` docstring），`output` 也放同一個資料夾。只改個人簡介、職稱、bullet 的排序與措辭、技能排序。中文 pptx 的職稱框可改成對應職稱。
4. `python scripts/tailor.py applications/.../spec.json`。若 REJECTED，依訊息修正後重試（最多 3 次）；**不可為了通過檢查而加入新數字**。
5. `bash scripts/render_pdf.sh applications/<dir>/*.docx applications/<dir>/*.pptx`。中文履歷必須 1 頁、英文 ≤ 2 頁、自傳 1 頁；超過就刪短句子後重來。exit 2（無 LibreOffice）就只交付原檔。
6. 在同一資料夾寫 `match.md`：職缺連結、分數、匹配理由、缺口、使用的範本。這個資料夾會 commit 到 repo；本機下次執行 drive_sync 時會自動上傳到 Drive `應徵最新/自動客製/`。

## 5. Email 通知（Gmail connector）
用 Gmail 的 `send_message` 寄給 `lovefujisai@gmail.com`，**每週只寄一封**，用 `htmlBody`。**不要附加檔案**，檔案用連結。
- 主旨：有高度匹配時 `🎯 職缺雷達 <週次>：<N> 筆高度匹配`；沒有時 `📡 職缺雷達 <週次>：本週無高度匹配`。
- 每筆高度匹配一個區塊：
  - 分數／100、職稱、公司、地點、薪資
  - 3 點匹配理由（引用 JD 原文）、1–2 點缺口
  - 使用的範本（DA 或 DS）、頁數（註明雲端字型為近似值，投遞前請在本機用 Word 確認）
  - JD 連結
  - 客製 CV 連結：`https://github.com/shangweiyang79/job-hunt/tree/main/applications/<資料夾名稱，空白與中文需 URL encode>`
- 之後列 60–79 分的職缺（公司、職稱、分數、連結），以及已投遞但重新刊登的職缺。
- 最後一行列來源狀態：`104 ✓ 35 筆 / LinkedIn ✗ 429 / …`。
- 寄信失敗時，在最後回覆中說明原因。

## 6. 記錄並 commit
- 本次所有評分過的職缺 append 到 `data/seen_jobs.csv`，status 填 `alerted` / `scored` / `applied` / `filtered`。
- 寫 `runs/<週次>.md`：內容同 email（來源狀態、高度匹配、60–79 分清單）。
- `git add data/seen_jobs.csv runs/ applications/ && git commit -m "Job radar <週次>" && git push`。不 commit `data/raw_jobs.json`。

## 失敗處理
單一來源或單一職缺失敗都不中斷流程。最後的文字回覆列出：掃描筆數、高度匹配筆數、email 是否寄出、客製 CV 資料夾、失敗的來源。
