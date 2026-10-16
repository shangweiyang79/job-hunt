# 每週職缺雷達（Joy Yang）

你在 `job-hunt` repo 根目錄執行一次完整的每週職缺搜尋。所有面向使用者的文字用繁體中文。整個流程在這一輪內完成。

**Joy 的主攻是資料工程（DE）與資料科學（DS）。** 台灣的數據分析（DA）職缺薪資通常有天花板，年薪很難破百萬，除非進外商。DA/BI 是次要目標。

## 0. 準備
- `git pull -q`，然後 `python -m pip install -q -r requirements.txt`。之後所有腳本都用同一個 `python` 執行，不要混用 `python3` 或單獨的 `pip`：雲端的 `pip` 指向另一個 Python 版本。
- `date -u +%F` 取得今天日期，算出 ISO 週次（例：2026-W43）。
- 讀 `config/criteria.yaml`、`profile/candidate_facts.md`、`profile/attribution.yaml`、`data/seen_jobs.csv`。
- `candidate_facts.md` 是唯一事實來源。**不可虛構任何數字、經歷、工具或成果。** Airflow、Spark、Kafka 是已知缺口，永遠不可寫進 CV。

## 1. 搜尋（過去 `window_days` 天）
每個來源都要實際嘗試，不可因為 `runs/` 裡前幾週失敗就跳過。每個來源記下：成功 / 失敗（原因）/ 筆數。

- **104**：104 會擋雲端 IP，**不要從雲端抓**。讀 `data/raw_jobs_local.json`（Joy 的電腦每週一 08:30 推送，每筆的 `detail` 是完整 JD）：
  - `fetched_at` 在 3 天內：直接使用。
  - 太舊或不存在（電腦沒開機）：104 標為「本週本機抓取未執行」，在 email 中說明。
- **JoBuzzer**（connector，外商職缺的主要來源）：
  - `search_jobs`：`location` 分別為 `taipei` 與 `tokyo`；`category` 為 `["data_science_and_ai","data_analytics_and_bi"]`；`postedWithin:"1w"`、`limit:10`，`hasMore` 為 true 時最多翻到第 3 頁。
  - 另外各跑一次 `search:"data engineer"`（同樣的 location 與 postedWithin）。
  - 回傳很大，每筆只擷取 id、title、organization.title、locations、jobLevel、salary 欄位、postedAt、applyUrl、jobuzzerUrl。
  - 標題要符合 `include_title`，或類別明顯是資料職能。
- **LinkedIn**：`python scripts/search_sources.py --source linkedin --out data/raw_jobs.json`。常被 429 擋，失敗就記錄，不要花時間重試。
- **其他**：用 WebSearch / WebFetch 補搜 CakeResume、Yourator、Japan Dev（`https://japan-dev.com/jobs` 可連線）、Daijob / CareerCross。TokyoDev 會回 403，改用 WebSearch。只收過去 7 天內、地點符合 `locations` 的職缺。

## 2. 去重與排除
- 依 `source + job_id`（JoBuzzer 用它的 id，無 id 用 URL）比對 `seen_jobs.csv`，已出現過的跳過。
- 公司＋職稱符合 `already_applied` 的，標「已投遞」，不另行通知。
- 同一職缺出現在多個來源，只保留一筆，優先保留有完整 JD 的來源。

## 3. 評分（0–100）
- 先把每筆分類為 DE / AE / DS / ML / DA / BI。
- 依 `scoring` 權重評分。**role_fit 看 `candidate_facts.md` 裡可轉移的證據，不看過去職稱**：DE 的證據有 BigQuery 管線、dbt 轉換層、Cloud Run、Comscore ETL；DS 的證據有 RAG＋評測層、DistilBERT 分類。
- **每一筆職稱符合的 DE/DS/AE/ML 都要打分，並寫一行理由。** 只有 `target_roles` 註解列出的明確非資料職能可以不打分直接排除，而且要寫明用了哪一條規則。不可整批標成 filtered。
- 套用 `penalties` 與 `bonuses`：明列年薪 < 100 萬 −15；外商或日本職缺 +5。
- 分數 ≥ 60 的候選，**一定要讀完整 JD** 再定分（104 讀 `detail` 欄位；JoBuzzer 用 `get_job`；其他來源用 WebFetch）。
- 每筆記錄：分數、類型、3 點匹配理由（引用 JD 原文）、1–2 點缺口。
- 要誠實：JD 要求候選人沒有的硬技能（Spark、Airflow、5 年以上 DS 經驗等）就扣分，不要為了湊高分放水。

## 4. 客製 CV（primary 類型 ≥ 75 分、secondary 類型 ≥ 80 分；分數高的優先，最多 `max_tailored_per_week` 筆）
1. **選範本**：依 `criteria.yaml` 的 `templates`，用職缺類型 × JD 語言（中文 JD 用 `zh`；英文 JD 或日本職缺用 `en`）。日本職缺若要求日文履歷，在 email 中註明「建議另備日文職務経歴書」。
2. **建資料夾** `applications/<YYYY-MM-DD>_<公司>_<職稱>/`，放入：
   - `jd.txt`：完整 JD（含連結、經歷與技能要求）。
   - `match.md`：分數、類型、匹配理由、缺口、使用的範本。
3. **敘事**依 CLAUDE.md：
   - DA/BI：洞察 → 建議 → 成效，以競品分析、留存分析帶頭。
   - DE/AE：管線、dbt 建模、測試與自動化。
   - DS/ML：方法、評估、架構。
4. **寫 `spec.json`**（格式見 `scripts/tailor.py` docstring），`output` 放同一資料夾。只改個人簡介、職稱框、bullet 的排序與措辭、技能排序。
5. **執行** `python scripts/tailor.py <dir>/spec.json`。REJECTED 就依訊息修正後重試，最多 3 次。
   - **不可為了通過檢查而加入新數字。**
   - **經歷不可張冠李戴**：每個 bullet 只能寫該公司實際做過的事（見 `profile/attribution.yaml`）。要強調某個專案時，替換**同一家公司**裡相關性較低的 bullet。
6. **審查（必做）**：用 Agent 工具呼叫 `cv-judge` subagent（定義在 `.claude/agents/cv-judge.md`），傳入該資料夾路徑。它會寫出 `<dir>/judge.json`。
   - `PASS`：可交付。
   - `REVISE`：依 `suggested_edits` 修改 `spec.json`，重跑 tailor 和 cv-judge。最多 2 輪。
   - `REJECT`，或 2 輪後仍未 PASS：保留檔案，但在 email 中標為「未通過審查」，附上主要問題，**不可當成可投遞版本**。
7. `bash scripts/render_pdf.sh <dir>/*.docx <dir>/*.pptx` 轉 PDF。中文履歷必須 1 頁、英文 ≤ 2 頁；超過就刪短句子後重來。exit 2（無 LibreOffice）就只交付原檔。

## 5. Email 通知（Gmail connector）
用 Gmail 的 `send_message` 寄給 `lovefujisai@gmail.com`，**每週只寄一封**，用 `htmlBody`。**不要附加檔案**，檔案用連結。
- 主旨：有客製 CV 時用 `🎯 職缺雷達 <週次>：<N> 筆高度匹配`；沒有時用 `📡 職缺雷達 <週次>：本週無高度匹配`。
- **順序：DE/DS 區塊在前，DA/BI 在後。**
- 每筆高度匹配一個區塊：
  - 分數／100、類型、職稱、公司、地點、薪資
  - 3 點匹配理由、1–2 點缺口
  - **審查結果**（PASS ✅ 可投遞，或 ⚠️ 未通過審查＋主要問題）
  - 使用的範本、頁數（註明雲端字型為近似值，投遞前請在本機確認）
  - JD 連結
  - 客製 CV 連結：`https://github.com/shangweiyang79/job-hunt/tree/main/applications/<資料夾名稱，URL encode>`
- 之後列 60 分以上但未達門檻的職缺（類型、公司、職稱、分數、連結），DE/DS 在前；再列已投遞但重新刊登的職缺。
- 最後一行列來源狀態，例如 `104 ✓ 35 筆 / JoBuzzer ✓ 12 筆 / LinkedIn ✗ 429 / …`。

## 6. 記錄並 commit
- 本次所有評分過的職缺 append 到 `data/seen_jobs.csv`，status 填 `alerted` / `scored` / `applied` / `filtered`。filtered 的要在週報寫明規則。
- 寫 `runs/<週次>.md`，內容同 email，另加各類型的筆數統計（DE / DS / DA…）。
- `git add data/seen_jobs.csv runs/ applications/ && git commit -m "Job radar <週次>" && git push`。不 commit `data/raw_jobs.json`。

## 失敗處理
單一來源或單一職缺失敗都不中斷流程。最後的文字回覆列出：
- 各類型的掃描與高度匹配筆數
- 每份 CV 的審查結果
- email 是否寄出
- 失敗的來源
