# Candidate facts — single source of truth for tailoring

Tailored CVs may **reorder, select, shorten, and rephrase** only what is below or already in `templates/`.
Never add a number, employer, title, date, tool, or outcome that is not written here. If a JD asks for
something not listed, report it as a gap in the alert. Do not invent it.

## Identity
- 楊上瑋 Shang-Wei (Joy) Yang · Tel +886-988285769 · shangweiyang79@gmail.com · 新北市中和區 (Taipei area)
- LinkedIn: linkedin.com/in/shang-wei-yang-670b9091 · GitHub: github.com/shangweiyang79
- Languages: Mandarin (native) · English proficient, TOEIC 925 · Japanese proficient, JLPT N1 (163)
- Certification: iPAS AI應用規劃師 中級 (passed, 2026)

## Experience (dates and titles are fixed)
### TaiwanPlus — Data Analyst / 資料分析師 · Taipei · 2025/05 – now
Government-funded international English media platform (政府支持之國際媒體平台).
- Dashboards & reporting automation: built self-service website and app dashboards plus monthly reports used across departments; automated the underlying Python → BigQuery pipeline; data-operation efficiency **+100%**.
- Competitive analysis (flagship DA story): benchmarked NHK World, CNA, Arirang with SimilarWeb Pro + GA4 + government statistics. TaiwanPlus traffic ≈ **0.4%** of NHK's, but it led all three on time-on-site, pages/visit, and bounce rate, so the problem was audience positioning, not product. Peers get **40–89%** of traffic from their home country vs TaiwanPlus Taiwan share **29%**, while **25%** of on-site users browse in English. Cross-referenced with official stats: about **17.6萬 / ~176K** English-fluent foreign residents in Taiwan, an uncontested audience. Recommended repositioning as an English life-media for foreigners in Taiwan, with SEO, community partners, and offline channels per segment (white-collar, students/teachers, blue-collar).
- YouTube retention analysis: found the drop-off points and topic gaps behind stalled growth; content and publishing changes lifted overall channel KPI **+50%**.
- Recommender analysis: the website AI video recommender under-weighted high-CTR categories; re-ranking lifted views **+5%**.
- Computex 2026 exhibition video project: cross-department performance analysis; views approaching **110萬 / ~1.1M**.
- Internal RAG AI assistant (Python → BigQuery → Vertex AI Search → Gemini, Streamlit on Cloud Run, company Google-account auth): **deployed internal tool** for editors to query content and competitor intel; **+30%** decision/retrieval efficiency. Has an eval layer: 8 deterministic checks verify citations and numbers against the DB, and a gate catches 90% of reviewer-rejected answers while passing 80% of accepted ones (threshold fitted on 20 answers, one labeller; state this caveat if mentioned). Public repo: github.com/shangweiyang79/AI_project.
- News classification (DS framing): DistilBERT + Gemini confidence cascade with a data-leakage / label-cleaning story; accuracy 0.81, macro-F1 0.81 (repo TaiwanPlus-News-Classification).

### United Daily News Group 聯合報系 — Data Analyst / 資料分析師 · New Taipei · 2025/04 – 2025/05
- Bi-weekly traffic and subscription-conversion analysis presented to department heads, with content recommendations.
- AI-assisted topic-selection workflow (Google Trends API + AI) to support content and SEO.

### Powen Gallery 紅野畫廊 — Gallery Manager / 藝廊經理 · Taipei · 2018/11 – 2024/03
- Monthly ad budget NT$50–60K; audience targeting, A/B testing, attribution; monthly reach **5x to 200K**; Instagram followers **40x**.
- GA4 / GTM / Power BI audience analysis.
- Cross-border stakeholder work across Japan, Italy, and the Czech Republic (3 countries): turned vague curatorial expectations into concrete collaboration specs and secured overseas exhibition space.

### Academia Sinica 中央研究院人文社會科學研究中心 — Research Assistant / 研究助理 · Taipei · 2018/03 – 2018/10
- SQL-based data extraction and cleaning for quantitative academic research.

## Education & training
- National Central University 國立中央大學 — M.S. Economics 經濟學碩士 · 2013/09 – 2015/06 (EN template says Jul. 2015). GPA 3.87/4.0; highest mark on oral defence; thesis Honourable Mention, Taiwan Economic Association Best Master's Thesis Award. Thesis: "Are Foreign-Owned Auction Houses More Efficient in the Chinese Art Market?"
- TibaMe 緯育 Data Engineering Program 資料工程師養成班 · 2024/12 – 2025/03. Capstone 台灣電影市場消費者喜好分析: scraped box-office data, ETL with Prefect, Tableau dashboard; found certain re-released film genres under-programmed and made release-window recommendations.

## Skills (only these)
- BI & viz: Power BI, Tableau, Looker Studio / Data Studio, GA4, GTM, Google Search Console, Excel
- Data: SQL, Python (pandas, scikit-learn), BigQuery / GCP, AWS, ETL (Prefect), Git, Docker
- Analytics methods: KPI / metric design, dashboarding, reporting automation, funnel & retention, segmentation, A/B testing, competitive benchmarking
- ML / AI: classification, regression, clustering, feature engineering; RAG, vector DB, semantic search, LLM evals, AI agents (Agentic AI)

## Narrative rules (from CLAUDE.md)
- **Never move a project to another employer.** Bullets under an employer describe only that employer's work (`profile/attribution.yaml`; tailor.py enforces it).
- **Analyst / BI roles**: Insight → Recommendation → Impact. Lead with the competitive-analysis and retention stories; keep tools secondary.
- **Scientist / engineer roles**: lead with the pipeline, RAG + evals, classification, methodology rigor.
- The Chinese CV is **one A4 page with photo** (`templates/中文履歷_楊上瑋_數據分析師.pptx`); every text box must stay ≤ its original character count.
- English resume ≤ 2 pages.
