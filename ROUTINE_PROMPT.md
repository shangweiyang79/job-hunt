# 每週職缺雷達（Joy Yang）

你在 `job-hunt` repo 根目錄執行一次完整的每週職缺搜尋。所有面向使用者的文字用繁體中文。整個流程在這一輪內完成。

## 0. 準備
- `pip install -q -r requirements.txt`
- `date -u +%F` 取得今天日期，算出 ISO 週次（例：2026-W43）。
- 讀 `config/criteria.yaml`、`profile/candidate_facts.md`、`data/seen_jobs.csv`。
- `candidate_facts.md` 是唯一事實來源。**不可虛構任何數字、經歷、工具或成果。**

## 1. 搜尋（過去 `window_days` 天）
- `python scripts/search_sources.py --source 104 linkedin --out data/raw_jobs.json`，失敗的來源會寫在 `errors` 欄位。
- LinkedIn 若回 429，改用 WebSearch：`site:linkedin.com/jobs/view "Data Analyst" Taipei`、`... Tokyo`。
- 依 `criteria.yaml` 的 `sources`，用 WebSearch / WebFetch 補搜 CakeResume、Yourator、TokyoDev、Japan Dev、Daijob / CareerCross。只收過去 7 天內刊登或更新、職稱符合 `include_title`、地點符合 `locations` 的職缺。
- 每個來源記下：成功 / 失敗（原因）/ 筆數。

## 2. 去重與排除
- 依 `source + job_id`（無 id 用 URL）比對 `seen_jobs.csv`，已出現過的跳過。
- 公司＋職稱符合 `already_applied` 的，標「已投遞」，不另行通知。
- 同一職缺出現在多個來源，只保留一筆。

## 3. 評分（0–100）
- 依 `scoring` 權重評分。分數 ≥ 60 的候選，**一定要讀完整 JD**（104 用 `python scripts/search_sources.py --detail 104:<id>`，其他來源用 WebFetch），不可只看標題。
- 每筆記錄：分數、3 點匹配理由（引用 JD 原文）、1–2 點缺口、職缺類型（DA/BI 或 DS/DE/AE）。
- 要誠實：JD 要求候選人沒有的硬技能（例如 Spark 生產經驗、5 年以上 DS 經驗）就扣分，不要為了湊高分而放水。

## 4. 高度匹配：客製化 CV（分數 ≥ `high_match_threshold`，取前 `max_tailored_per_week` 筆）
1. 選範本：
   - 台灣中文 JD → `templates/中文履歷_楊上瑋_數據分析師.pptx`（一頁含照片）。JD 要求自傳時，另外改 `templates/中文自傳_楊上瑋_資料分析師_通用版.docx`。
   - 英文 JD 或日本職缺 → DA/BI 用 `templates/Resume_Shangwei Yang_Data Analyst.docx`；DS/DE/AE 用 `templates/Resume_ Shangwei Yang_Data Scientist.docx`。
   - 日本職缺若要求日文履歷，在通知中註明「建議另備日文職務経歴書」。
2. 敘事：DA/BI 職缺用「洞察 → 建議 → 成效」，以競品分析與留存分析帶頭，工具放次要。DS/DE/AE 職缺強調管線、RAG＋evals、分類模型與方法嚴謹度。
3. 寫 `out/<YYYY-MM-DD>_<公司>_<職稱>/spec.json`（格式見 `scripts/tailor.py` docstring）。只改個人簡介、職稱、bullet 的排序與措辭、技能排序。中文 pptx 的職稱框可改成對應職稱。
4. `python scripts/tailor.py out/.../spec.json`。若 REJECTED，依訊息修正後重試（最多 3 次）；**不可為了通過檢查而加入新數字**。
5. `bash scripts/render_pdf.sh out/.../*.docx out/.../*.pptx`。中文履歷必須 1 頁、英文 ≤ 2 頁、自傳 1 頁；超過就刪短句子後重來。exit 2（無 LibreOffice）就只交付原檔。
6. `python scripts/drive_sync.py --upload out/<dir>/*.pdf out/<dir>/*.docx out/<dir>/*.pptx --folder-path "自動客製/<YYYY-MM-DD>_<公司>_<職稱>"`，記下 folder 連結。上傳失敗不中斷，在通知中標註。

## 5. Telegram 通知
- 每筆高度匹配寫一則訊息到 `out/msg_<n>.txt`，然後執行 `python scripts/notify_telegram.py --text-file out/msg_<n>.txt --files <pdf 或原檔>`：
  ```
  🎯 高度匹配 <分數>/100｜<職稱>
  <公司>｜<地點>｜<薪資>
  ✅ <匹配理由 1>
  ✅ <匹配理由 2>
  ✅ <匹配理由 3>
  ⚠️ 缺口：<缺口>
  📄 版本：<DA 或 DS 範本>（頁數：<n>，雲端字型為近似值，投遞前請在本機用 Word 確認）
  🔗 JD：<url>
  📁 Drive：<folder url>
  ```
- 本週 0 筆高度匹配時，只發一則：`📡 職缺雷達 <週次>：掃描 <N> 筆，無 ≥<門檻> 分職缺。前 3 名：<公司 職稱 分數> …`
- 有來源失敗時，在最後一則訊息附一行 `來源狀態：104 ✓ / LinkedIn ✗ 429 / …`。

## 6. 記錄並 commit
- 本次所有評分過的職缺 append 到 `data/seen_jobs.csv`，status 填 `alerted` / `scored` / `applied` / `filtered`。
- 寫 `runs/<週次>.md`：來源狀態表、高度匹配清單（含理由與 Drive 連結）、60–79 分清單（公司、職稱、分數、連結）、已投遞的重新刊登職缺。
- `git add data/seen_jobs.csv runs/ && git commit -m "Job radar <週次>" && git push`。不 commit `out/`。

## 失敗處理
單一來源或單一職缺失敗都不中斷流程。最後的文字回覆列出：掃描筆數、高度匹配筆數、Telegram 是否送出、Drive 連結、失敗的來源。
