# R1 實作 TODO List(v0.8.33)

> 依據:`r1_design_draft.md` v1.3.32(正式版;framework v0.5.1 已 merge／重新 pull，四個 ROS consumers 正式導入中)。本文件將設計規劃書轉為可逐步執行、可逐項查核的實作清單。
> 正式位置：`src/rv2_project/docs/r1_design_docs/`；舊 transport 下路徑不再使用。
> 文中「§x.y」一律指設計規劃書章節；「T*.n」指本文件的 TODO 項目。

## 0. 版本歷史

| 版本 | 說明 |
|---|---|
| v0.8.33 | **更新 Agent:`coco-codex`**。使用者確認 framework #9 merge 並要求接續。乾淨 standalone master 已實際 git pull --ff-only origin master，本地／origin／即時遠端均 ae4790668efc83f99584c300e6963d522e04e12c、VERSION0.5.1；與原 tag a058498 的 tree47fb1a9 完全相同，原 tag 不移動。先規劃四個 ROS consumers 在乾淨候選工作分支以 gitlink-only commits 導入，再用各自 nested 四步／lint 正式驗證；transport 另重做 Debian downstream gate。驗證後才各附獨立版本 commit/tag/PR，transport 移除公開 legacy API 預計 v0.2.0，其餘三包 v0.1.2。Project PR #1 尚 open，既有 snapshots／tags 不回寫；元件 merge 後再新增 snapshot。原 dirty sources、master、Doxyfile 與 TSan SKIP 限制保留。 |
| v0.8.32 | **更新 Agent:`coco-codex`**。Project v0.1.1 版本 commit/tag fddcccd 已推 PR #1，乾淨 release nested 四步及 lint 通過。src 全面唯讀盤點 9 份 .gitmodules／14 個 gitlinks 皆為最新已合併版本。乾淨 transport 分支分開提交 legacy 移除 664a1a4、T12/export 423ff10；integration 分開提交 I15/I18 6a36157、依賴清理 58e167d，原工作樹 dirty bytes 不動。Framework R1-only UBSan/T0 相容性 e690efa、README rebase/pin 17a9a0a 與只改 VERSION 的 v0.5.1 a058498 分開提交；84 Python 回歸、四套 shell 查核、lint 全過，已推 PR #9/tag。正式 consumer pin／定版仍待使用者 merge 與重新 pull；開發預驗證另記 T14，不將 TSan SKIP 算入 T12.2。 |
| v0.8.31 | **更新 Agent:`coco-codex`**。T14.1 的五個 project checkout 均實際 pull，HEAD／origin／即時遠端及原 release tag tree 全一致；transport 固定 cc7cec2，所有四個 ROS consumers 的 nested framework 均 f5952a8/v0.5.0。v0.1.0 snapshot bytes 不變，新 v0.1.1 資料 commit 907ff3d、gitlink commit 5d1c44f。只有 package.xml 進版的 PR-ready 候選以官方 Docker nested 四步前三級及 lint 通過：unit131/integration9、CMake/XML 全 PASS，sanitizers N/A；準備獨立 version commit/tag 與 project PR。原 T14.2–T14.4、TSan／legacy 依賴缺口不提前勾選，逐項 logs 保留。 |
| v0.8.30 | **更新 Agent:`coco-codex`**。使用者確認 transport merge 並要求 project 新 snapshot／PR／tag，後續移除 transport legacy、提交 I15/I18 與 T12/export，最後同步 framework README。遠端核對 transport v0.1.2 主線 cc7cec2 與原 tag 8f56a55 tree 相同；project master 已有 30afa23，可正常提出 PR，不需 bootstrap 空主線。先規劃 v0.1.1 snapshot 並保留 v0.1.0，再按順序實作 T14；legacy 移除尚不在已合併 v0.1.2，禁止誤記已解決依賴。Framework v0.5.0 的 UBSan／T0 硬性 legacy target 需相容修正，必須維持 fail-closed、先 merge 新框架再正式導入，不改既有發布 tree／tag；TSan runtime 仍未完成。 |
| v0.8.29 | **更新 Agent:`coco-codex`**。T13 完成：使用者同意以 merge 2ee952c 納入原 docs 歷史，保留完整 bundle／Git metadata（含 stash reflog）及原 staged workspace。五包乾淨 checkout 實際 pull 後固定已合併 release SHA，原 tags/tree 核對不移動；根目錄 framework v0.5.0，既有五個 workspace gitlinks 保留。rv2_project v0.1.0 功能 commit 3ba0b4d，官方 Docker nested 四步、lint、乾淨 clone unit 131／integration 9 與 CMake/XML 全 PASS；sanitizers N/A，容器已卸載。首輪缺 rebase 前 tags／一份 Ruff 格式失敗與修正 log 皆保留；後續文件完成紀錄不冒充重跑 ROS。T12.2、待 merge／未提交補強及 legacy dirty dependency 缺口不勾消；新 project 空 remote 尚無 PR base，本次提交留本地、不自建空主線／release tag。 |
| v0.8.28 | **更新 Agent:`coco-codex`**。依使用者要求先同步搬遷後文件，修復本地測試報告連結，新增 rv2_project v0.1.0 ROS2 snapshot 規格與 T13。2026-09-13 查核：framework v0.5.0、interfaces/mocks/integration v0.1.1 已合併；transport PR #8 尚 open，主線仍 v0.1.1，不能記成 v0.1.2 已合併。新增總驗收缺口清單，區分已提交 release、未提交 I15/I18/T12 補強與 dirty legacy dependency，歷史 PASS 不升格為 clean snapshot 驗收。Snapshot 僅固定版本組合，非自動 release／總驗收認證；先規範再實作，原 Git 歷史與 staged submodules 保留。 |
| v0.8.27 | **更新 Agent:`coco-codex`**。依使用者要求補 interfaces 正常 0.1.0→0.1.1 獨立版本 commit/tag 5bef9c0、更新 PR #1，取代暫不定版例外。Mocks/integration 格式提交 5af25b8／46e7116 與正式 lint 均 PASS；使用者另批准 I10 程序退出補強，獨立 commit 07d8a13，不混入 I15/I18。兩包完整四步串行皆 exit 0：mocks unit 3／integration 20、UBSan 3；integration 一般 21／I10 ASan 2 cases PASS，TSan SKIP。驗證後獨立 v0.1.1 commit/tag mocks 37d6e7f、integration 5adecce，提出 PR #4／#3。保留所有原來源 bytes、I15/I18 未提交差異與 dirty rv2_interfaces 依賴限制；metadata-only release 後未重跑 ROS，docs 無 remote 留本地。 |
| v0.8.26 | **更新 Agent:`coco-codex`**。使用者要求推送 consumer PR；framework 本地 master 再次 pull 確認仍為 f5952a8。以已提交 checkout 驗證：interfaces build/full entry PASS、lint SKIP，更新 PR #1，維持 0.1.0 不定版例外；transport lint、一般 134／ASan 64／UBSan 84 PASS，獨立 v0.1.2 commit/tag 8f56a55 後提出 PR #8。乾淨 rv2_interfaces 缺 legacy 欄位的編譯失敗保留；成功結果依賴現有唯讀 dirty workspace dependency，PR 明示非全 clean-dependency 重現。mocks/integration committed lint 分別 FAIL 11／26，不 push／release／PR，待允許另行提交格式化修正；既有 source 差異與 Doxyfile 不動，docs 無 remote 仍留本地。 |
| v0.8.25 | **更新 Agent:`coco-codex`**。依使用者最新裁決取代「固定合併前原 tag SHA」：使用者採 rebase 合併，必須先在本地 framework master 執行 git pull，再核對實際合併後版本 SHA 才更新 consumers。已 git pull --ff-only origin master，確認本地／origin/master／即時遠端皆為 v0.5.0 release f5952a8；四個頂層 consumers 改 pin 該主線 SHA，不再 pin af386de。兩者 tree 相同、原 tag 不移動，保留前輪 commits／歷史及既有來源差異；本次只補 gitlink 修正提交、不升 package 版本／push／PR。 |
| v0.8.24 | **更新 Agent:`coco-codex`**。使用者已合併 framework PR #8 並要求更新各 package submodule；主線 release f5952a8 與原 v0.5.0 tag af386de tree 一致，固定原 tag、不移動既有標記。先修文件，再更新四個頂層 consumers 的 gitlink／nested checkout，以獨立 dependency commits 與 Docker 入口查核驗證；不混入 I15/I18、格式化或 export 等既有來源差異，不改 package 版本、rv2 Doxyfile 或另行初始化中的 rv2_project staged workspace。不把本輪 pin／入口驗證說成完整 ROS／sanitizer 重驗，T12.2 仍未完成。 |
| v0.8.23 | **更新 Agent:`coco-codex`**。使用者授權診斷並修正 I15；受控初始 client-not-ready 證實合法 code=10 背景成功被舊 code=0-only 等待漏接，修正前 FAIL／修正後 PASS。僅修啟動 identity／ready／retry callback gate 與 teardown log，保留原 activity/seal/terminal/亂序控制本體、runtime、timeout 及既有 I18/其他 diff。無參數完整流程一般 21/21、I10 ASan 2/2 PASS、整體 exit 0，UBSan N/A、TSan SKIP/77；owner/framework lint PASS。framework 附獨立 v0.5.0 commit/tag af386de，PR #8 恢復可審核；仍待使用者 merge 才更新 consumer pins，T12.2 不勾選。 |
| v0.8.22 | **更新 Agent:`coco-codex`**。使用者授權診斷並修正 I18；先保留原失敗與未重現診斷，收集實際註冊回覆/重試事件，區分啟動註冊與 service-response-failure 驗收。受控初始 client-not-ready 證實 code=10 後可合法背景成功；修正前 FAIL、修正後 PASS，保持 ACTIVE、matching identity、G/G+1、恰一次 terminal/mandatory retry 及 late-event 去重，不放寬 timeout 或修改 runtime。完整 test_run 的 I18 PASS，但另有 I15 初始註冊等待 FAIL，整體 20/21；lint 與另跑 I10 ASan 2 cases PASS。PR #8 改為 I15 validation pending，下一版定版繼續暫緩。r1_interfaces API 權限已恢復並提出 PR #1，維持 0.1.0、不新增 release commit/tag；新版 framework merge 前不更新 consumer gitlink。 |
| v0.8.21 | **更新 Agent:`coco-codex`**。依使用者新裁決，TSan 預設 off，正式使用流程為 test_build→test_deps→無參數 test_run→test_clean，lint 維持獨立入口。test_run 在既有依賴就緒容器內串行完成一般 unit/integration 與 owner 適用 sanitizer，按 run/profile 隔離並保留產物、逐項狀態/log；特殊 selectors 保留單項模式，不呼叫 todo_check 重建環境或重裝依賴。關閉的 TSan 明示 SKIP，不能掩蓋其他失敗或勾選 T12.2；保留既有 ament 非重複檢查。r1_interfaces SSH remote 已確認可用，但 API 404 仍阻塞 PR；使用者已裁決保持 package.xml 0.1.0，本次不新增 release commit/tag。framework PR 經使用者 merge 後才更新所有 consumer pins/PR，既有 v0.4.0 tag 不移動。 |
| v0.8.20 | **更新 Agent:`coco-codex`**。依使用者要求查詢 TSan unexpected memory mapping；官方 LLVM 說明高 ASLR entropy 與固定 shadow mapping 衝突，本機官方容器確認 mmap_rnd_bits=32，GCC clean probe 仍阻塞，既有 Clang 18 證據亦有 personality CHECK。維持主機/容器安全設定，先規範 framework 的顯式 `-t on\|off`（預設 on）：off 只略過選定 TSan job，stdout 明示 SKIP、exit 77，不建立/清除容器或產物、不降級成未 instrument 的測試。非法參數仍失敗、其他測試不受影響、T12.2 不勾選。框架先開發驗證，consumer gitlink/版本與 rv2 Doxyfile 不動；實測結果見 T12 補充。 |
| v0.8.19 | **更新 Agent:`coco-codex`**。四個 consumer 已以 gitlink-only commits 固定 framework v0.3.0 原 tag `67755d6`。正式 nested 串行 ASan 64/I10 2、UBSan 84/mocks 3、三包 Debian 乾淨安裝與 t2–t11 完整鏈全過，勾選 T12.1/T12.3/T12.4/T12.5；transport 完整 134 cases、T11 21 cases，cppcheck 原生 32 SKIP 如實保留。M22 真實 calc/activity/seal 交錯與 terminal 順序已補，ASan 額外五次亦通過。原 K11 平行 DDS 干擾失敗與探針證據保留，原斷言/runtime 不改。T12.2 仍因兩 owner 的 TSan clean probe unexpected memory mapping 阻塞；不附 package release/PR、不提前改版本，來源與既有格式化 diff 保留，容器已卸載，詳見 T12 正式結果。 |
| v0.8.18 | **更新 Agent:`coco-codex`**。正式 nested 測試發現 UBSan K11 的 23.94 Hz 失敗；XML 證實與 t5 同 topic 重疊 265 ms，兩個官方容器通訊探針證實 default bridge/domain 0 可互通。修正 §1.2 執行規範：不同 container 名稱不代表 DDS 隔離，未明確驗證隔離的 ROS 測試須全域串行；停止把本輪平行排程當作隔離實證，保留失敗 log，待既有流程完成後串行重驗 UBSan 與完整鏈。不放寬 K11 門檻、不修改 runtime、不改已發布 framework。M22 兩種交錯已補且 ASan 及額外五次皆過；最終逐項結果仍待收斂。 |
| v0.8.17 | **更新 Agent:`coco-codex`**。使用者已合併 framework PR #7，主線 release `6a04bfe` 與原 v0.3.0 tag `67755d6` tree 完全相同；保留原 tag，四個 consumer 將固定其版本 commit。接續從各自 nested 入口正式執行 sanitizer、打包與 t2–t11 連續鏈，補 M22 決定性交錯測試；既有 diff 保留、package 版本待 PR-ready 才獨立提交、rv2 Doxyfile 不動。TSan 仍需重新證實 runtime 能力，不放寬安全設定、不將平台阻塞當 PASS；尚未取得本輪結果的小項不勾選。 |
| v0.8.16 | **更新 Agent:`coco-codex`**。T12 framework 已實作隔離 run/mount 防護、sanitizer compile/link/ELF 與精確案例 gate、Debian dependency closure/內部版本與乾淨安裝；21 sanitizer unit、16 packaging unit、入口/CMake/既有回歸與全檔 lint PASS。開發預驗證：transport ASan 64、UBSan 84、mocks UBSan 3、I10 ASan 2 cases PASS；transport 完整 134 功能案例 PASS(cppcheck 原生 32 SKIP)。乾淨安裝先抓出缺少 r1_interfaces export，補 CMake 一行後三包 deb/discovery/downstream compile/link/node 啟停 PASS。L14/S11/K12/K15/K16 與 I10 shutdown 測試補強保留 consumer diff；M22 決定性交錯證據仍待補。GCC/Clang TSan 均遇平台啟動阻塞，不放寬安全設定、不勾選正式 T12。framework 功能 commits 後獨立 v0.3.0 commit/tag `67755d6`，已提出 [PR #7](https://github.com/cocobird231/r1_test_framework/pull/7)；待使用者 merge 才可更新 consumer pin，版本/Doxyfile/gitlink 未動。 |
| v0.8.15 | **更新 Agent:`coco-codex`**。T12 開工前核對現行 unit/integration 布局、framework v0.2.1 與 transport v0.1.1；補齊跨 package I10、K15 ASan、K10/I10 TSan、UBSan unit 分類、sanitizer fail-closed/子程序退出與隔離產物要求。打包須使內部 Debian Version 與檔名一致，處理 workspace-local 依賴並在無來源/build overlay 的乾淨容器驗證安裝與下游使用。先實作 framework 並預驗證，待 framework PR 經使用者 merge 才更新 consumer pin、正式驗收；不提前勾選或更改 package 版本、gitlink、rv2 Doxyfile。 |
| v0.8.14 | **更新 Agent:`coco-codex`**。使用者要求修正 transport lint 並確認 unit/integration 通過。先同步規範；複核後保留 flake8/pep257 的非重複檢查，flake8 相容設定只將 Jazzy 原設定的 inline-quotes 對齊 Ruff 雙引號，直接修正三份 launch module docstring 與 CMake 縮排。僅排除由既定 clang-format gate 取代的 uncrustify 註冊；保留 cppcheck/lint_cmake/xmllint、全部 10 個 gtest targets/134 案例與 labels。Docker framework lint、完整 test_run、unit 84/84、integration 50/50 均 PASS；cppcheck 原生 32 SKIP 仍揭露。不改 runtime 邏輯、Doxyfile、package 版本或 gitlink；證據見 T0.7，保留未提交 diff。 |
| v0.8.13 | **更新 Agent:`coco-codex`**。使用者同意使用 Ruff 修正剩餘 Python lint，並確認設定檔。沿用各 package submodule 的 `lint/ruff.toml` 與 Ruff 0.15.7，Docker 內對 owner 選中 Python 執行安全 `check --fix` 與 `format`，不放寬規則或啟用 unsafe fixes。先修文件，保留前輪未提交 C/C++ diff，使用 owner UID/GID 寫回並驗證 AST/非 Python 來源保留；不改 Doxyfile、package 版本、gitlink 或框架。共修正 23 Python，AST 僅 I04 unused `re` import 移除；對齊 gate cwd 後 transport/mocks/integration nested lint 全 PASS，interfaces SKIP。證據見 T0.7，本輪仍保留 diff 供檢視，不 commit/升版/PR。 |
| v0.8.12 | **更新 Agent:`coco-codex`**。使用者同意修正 package lint，先以 clang-format 修正一輪。本輪試行範圍為各 owner lint 選中的 C/C++ 檔案(含 transport legacy 程式碼)，Docker clang-format 18 使用既有 framework v0.2.1 設定，保持 UID/GID/mode；不加入框架自動修正功能、不改 Python/Ruff、Doxyfile、版本或 gitlink。先同步文件，再對 52 檔各格式化一次，實際改動 47 檔；nested lint 的 C/C++ 全過，mocks 整包 PASS，transport/integration 分別剩 3/22 個 Ruff failed checks，interfaces SKIP。本輪保留 diff 供檢視，不 commit、升版或提出 PR，證據見 T0.7。 |
| v0.8.11 | **更新 Agent:`coco-codex`**。使用者已合併 framework PR #6，主線 release SHA 重寫為 `f86fcd9`，其 tree 與既有 v0.2.1 tag commit `3dd3c27` 完全相同；不移動 tag，各 consumer 固定既有版本 commit。本輪保留前次本地 dependency commits 開新分支，四個 gitlink-only commits 已留本地，package.xml、來源與 rv2 Doxyfile 不動。Docker metadata PASS；實際 nested lint：transport 35、mocks 11、integration 26 個 failed checks，interfaces 無支援來源而 SKIP。未 push、附 release commit/tag 或提出 PR；證據及後續條件記於 T0.7。 |
| v0.8.10 | **更新 Agent:`coco-codex`**。依使用者新裁決，C/C++ lint 僅比對 clang-format 18 原生輸出，排除無法由 formatter 自動偵測/修正的額外規則：block comment 強制兩格、空 namespace 缺名、macro/條件編譯名稱推論、formatter-off 強制檢查及 Doxygen/多行註解結構。移除補充詞法檢查與記憶體間距正規化，以原生 formatter 正反例取代專屬回歸；一般格式、可修正 namespace 名稱、Python/Ruff、ShellCheck 與唯讀/錯誤傳遞不變。先修規範再改 framework，Docker 18 tests/入口/路徑與全檔 lint PASS；功能 commit `d3007d4` 後獨立版本 commit/tag v0.2.1 `3dd3c27`，已提出 [PR #6](https://github.com/cocobird231/r1_test_framework/pull/6)。consumer gitlink 與既有來源不動，transport override 預驗證仍有 35 個格式失敗，證據見 T0.7。 |
| v0.8.9 | **更新 Agent:`coco-codex`**。使用者已 rebase merge framework PR #5，並要求各 package 升級 framework。主線 release commit 為 `5316f3e`，既有 v0.2.0 tag 仍指向 `631a85b`，兩者 tree 完全一致；不移動 tag，四個 consumers 固定原 tag 的版本 commit。三個遠端 package 舊 PR 均已合併，本輪從最新 base 建新分支；interfaces 無 remote，維持本地流程。四個 gitlink-only dependency commits 已留本地；Docker lint 三個 package FAIL、interfaces 無支援來源而 SKIP，未 push、附 release commit/tag 或提出 PR。不批次格式化、修改 rv2 Doxyfile 或提前改 package.xml；結果與後續 PR 條件另記於 T0.7。 |
| v0.8.8 | **更新 Agent:`coco-codex`**。使用者確認目前 lint 格式並要求 commit/PR；沿用 120 欄、class 內短函式單行、註解與 Doxygen 規則。framework 先提交格式確認文件，再以獨立 `chore(release): v0.2.0` commit `631a85b` 僅更新 VERSION 與 README 安裝範例的 tag，建立同名 annotated tag，推送並提出 [PR #5](https://github.com/cocobird231/r1_test_framework/pull/5)。本輪全檔 Docker lint 與 release metadata 驗證通過；程式碼/測試未變，沿用 56 個回歸測試結果。T0.7 framework 驗收完成；待使用者以 merge commit 合併，才更新其他 package gitlink，本輪未改其他 package 或 rv2 Doxyfile。 |
| v0.8.7 | **更新 Agent:`coco-codex`**。增加多行區塊註解與 Doxygen JavaDoc-style 文件註解候選：一般說明用 `/* */`、class/function API 說明用 `/** */`，delimiter 獨立成行、星號對齊且區塊不得空白；文件首個非空內容行為有文字的 `@brief`。明訂這些為選自 Doxygen 支援語法的專案慣例，不是 Doxygen 唯一合法格式；lint 驗證結構，不宣稱驗證所有 API 均有文件或參數/回傳描述語意。沿用唯讀 Docker、不碰 rv2 Doxyfile、不定版與不更新 gitlink。 |
| v0.8.6 | **更新 Agent:`coco-codex`**。細化 C/C++ lint 候選：程式碼與行尾註解間兩格、不對齊註解欄；巢狀 namespace 同縮排且逐層標示正確結尾名稱。使用者裁決所有情況均需強制檢查，故增加 token-aware 補充檢查，涵蓋 `/* */` 與空 namespace，formatter-off 不豁免；formatter 的 block comment 間距衝突僅在記憶體比對時調整。120 欄與 class 內短函式單行仍待確認，不附 release commit/tag/PR、不改 package gitlink。 |
| v0.8.5 | **更新 Agent:`coco-codex`**。新增 T0.7 與 PR 前 lint 候選規範：framework 提供唯讀 Docker test_lint.sh、LLVM 基底 Allman .clang-format 與 C/C++ 範例，Python 採 PEP 8/Black 相容 Ruff，Shell 採語法檢查/ShellCheck。使用者要求先討論格式再定版，本輪不附 package 版本 commit/tag、不開 PR、不更新各 package gitlink、不批次格式化舊碼；integration header/source 布局維持不變。 |
| v0.8.4 | **更新 Agent:`coco-codex`**。依使用者裁決排除 rv2 Doxyfile：transport 版本 commit 由 e99c59c amend 為 8b45662，只保留 package.xml 0.1.0；Doxyfile 還原既有 0.0.0，並依本次 amend 同步 transport 的未合併 PR/tag，其他 packages 與 framework tag 不動。§1.4 明訂只同步同一 R1 release 範圍的版本欄位，版本變更不得提早混入功能 commit；mocks/integration 的首次空 release commit 僅本次獲准例外，後續仍遵守 PR-ready 才附獨立版本 commit。 |
| v0.8.3 | **更新 Agent:`coco-codex`**。framework v0.1.0 PR #4 經使用者 merge 後，四個 package 的 gitlink 更新為已發布 tag 所指 `12cc2dd`；GitHub rebase 後主線版本 commit 為 `0bb3228`，兩者 tree 完全相同，不移動既有 tag。transport 以獨立 release commit 同步 package.xml/Doxyfile 為 0.1.0；mocks/integration 的 package.xml 原已為 0.1.0，以空 release commit 記錄首次定版並各自加 v0.1.0 tag，與 gitlink 提交分開。interfaces 無 remote，僅本地更新 gitlink，release commit 依 §1.4 待 PR-ready。Docker 版本/XML、nested owner、shell 語法及框架路徑解析回歸通過；本輪未改腳本或測試、不重跑全功能測試。 |
| v0.8.2 | **更新 Agent:`coco-codex`**。依使用者裁決新增各 package 獨立定版規範：首次 v0.1.0，ROS2 package 同步 package.xml 與既有版本欄位，framework 採 VERSION；準備 PR 時才附獨立版本 commit 並加 vX.Y.Z tag，目前手動、未來由 GitHub Actions 接手。framework 版本 PR 經使用者 merge 後，才允許各 package 更新至該版本 commit；文件修訂版本不重設。 |
| v0.8.1 | **更新 Agent:`coco-codex`**。T0 布局修正完成：四個 package 的 framework gitlink 固定 `f436059`，移除 18 個根目錄腳本 symlink；測試分類、CMake labels 與 Handle H7–H8 拆分完成，既有案例 ID/斷言保留。framework 以實際 CTest discovery 防止 colcon 將空分類誤判成功。Docker T0 PASS、transport unit 84/integration 50 cases 全綠、T10 27-test/T11 39-test 彙總全綠、T1 build及10個介面解析通過；無 sibling framework 的 fresh clone 從其他 CWD 呼叫 nested 腳本亦完成 build。全部驗證容器卸載，T0.2/T0.5/T0.6 勾選；修正 helper 路徑與 T12.5 跨 package 指令。 |
| v0.8.0 | **更新 Agent:`coco-codex`**。先行修訂 T0 規範：依使用者裁決，每個 R1 相關 package 必須於根目錄內嵌 `r1_test_framework` git submodule，直接使用 `./r1_test_framework/*.sh`，取代 v0.2.0 的 sibling/symlink 布局。`test/` 統一分為 `unit/` 與 `integration/`，依單一合約或系統協作分類；新增 T0.6 搬移驗收。既有 T1–T11 通過紀錄保留為歷史證據，新布局須另行 Docker 重驗後勾選 T0.2/T0.5/T0.6。同步依據設計稿 v1.3.0。 |
| v0.7.0 | **更新 Agent:`coco-codex`**。T11.1–T11.5 完成:`r1_integration_tests` launch_testing 基架、I00 空場景/並行實證與 I1–I18 全場景；19 個 CTest targets 以獨立 ROS_DOMAIN_ID(可整段 relocation)及 parallel=2 執行。補齊 real-manager PENDING TTL、master lost-ACK 原 event 重送/冪等、manager/service readiness barrier、雙 ready snapshot gate、真 waiter armed barrier、MockMaster out-of-order/stale generation、process-model crash/restart、producer timestamp 週期/in-flight/backoff、fresh/raw status identity 證據。多輪對抗式查核發現全修，最終 3-agent 分區複核 0 must-fix；`./todo_check.sh t11` docker PASS(39-test 彙總,0 error/failure/skip,container 自動卸載)，受影響 I5/I6/I11/I12/I17 另各連跑 3 次全綠；mock 支援異動另經 t10 27-test regression 全綠。I10 sanitizer 組態依規劃保留至 T12。 |
| v0.6.0 | **更新 Agent:`coco-codex`**。T10.1–T10.6 完成:`r1_test_mocks` 五個可腳本化 nodes、23 個 smoke gtests、嚴格 `<10%` rate 驗證、接受但不回覆、ACK 串接固定序列與四種 CsmNotify/亂序/舊世代注入；修正 callback lifetime 與跨執行緒計數 race。docker t10 PASS(27-test 彙總),3-agent 最終對抗式複核 0 must-fix。同步修正 §1.3 跨 package 執行位置、T10/T11 的 pre-T1 舊依賴/框架文字與附錄案例數 |
| v0.5.1 | **更新 Agent:`coco-codex`**。新增 §1.4 文件修訂紀錄規範:每次更動 `r1_todo.md` 或 `r1_design_draft.md`,除同步更新文件版本號與版本歷史外,必須於該筆歷史明確標示實際更新 Agent；並補列 Codex 的 agent 身分命名 |
| v0.5.0 | T8.1–T8.4、T9.1–T9.9 完成:`test_handles.cpp`(H1–H8,含 in-flight unregister 不復活與 debug/release 雙模式 H3)、`csm_master.h`(status 唯一訂閱者、identity 配對、CSM 級雙閾值 polling、level reconciliation 含 v1.2.1 absence clock、可靠通知 pump)、`csm_master_node` 執行檔與 CM1–CM13(mock CSM 裸 node)。docker t8 / t9 閘門 PASS。4-agent 對抗式查核 27 項發現、14 must-fix 全修:實作面 6(DISCONNECTED record 之 status 復活防護、same-instance rebuild 保留 seq fence、pending 健康事件按 owner 區分取代、notify RPC in-flight deadline 防 budget 餓死、DISCONNECTED peer 不永久關閉 ready gate、event FIFO);測試面 8(H8 補真 in-flight、CM1 interval/grace 驗證、CM2 訂閱斷言、CM6 stale-status fence、CM11 grace 起點、CM12 STALE settle、CM13 變體 C 無幻影 TIMEOUT)。獨立複核逐項確認 |
| v0.4.0 | T6.1–T6.4、T7.1–T7.14 完成:`control_signal_factory.h` + `src/r1/`(singleton 單一定義、joy/twist/string 註冊)、`source_registration.h`、`control_signal_manager.h`(五階段 tick、兩階段註冊、retry 狀態機、master 互動、通知處理、黑白名單)與 F1–F5、M1–M26 全數實作;`control_signal_handles.h` 為 Manager API 相依提前實作(H1–H8 測試屬 T8)。docker t6 / t7 閘門 PASS。**裁決 §12 #6(D7)提案**:`RetryPolicy::Recommended()` = {initialDelayMs 200, maxDelayMs 5000, jitterRatio 0.2, maxInitialAttempts 3, maxInFlight 4, quarantineThreshold 3},`autoRetryInitial` 旗標歸 RetryPolicy(全域);依 §2.4,typed RETRYABLE_CONFLICT 之 D3 retry 為強制、不受 D7 旗標與 initial cap 約束。5-agent 對抗式查核 43 項發現、25 must-fix 全修:實作面 10(D3/D7 retry 治理、stale completion 世代防護、quarantine 未生效、三處鎖巢套、peer-health 世代驗證、FIFO 冪等快取、sink 清理競態、abort 路徑補 rollback UNREGISTER、tick 執行緒 callback guard、**解構 fence**——manager 中途銷毀時 in-flight async callback UAF,以 alive sentinel + callback 計數 drain 修復);測試面 15(M3 依 §2.4 改判 D3 強制 retry、M4 改 16 執行緒跨 4 真實 targets、M5 補 policy-off 分支、M7 補 in-flight、M8 補 PAIR_MISSING、M14 補 in-callback 半、M16 補 sink rate、M17 補 per-CSM 單筆與 degraded 進出、M18 補覆蓋語意、M24 補 established intent 無上限、M25 碰撞決定化)。M4 併 TSan、M10 併 ASan 維持 T12 |
| v0.3.0 | T3.1–T3.3、T4.1–T4.7、T5.1–T5.6 完成:`control_signal_info.h`(六規則驗證)、`control_signal_source.h`(雙模式、ResponseHealth、RateRecorder、terminal seal 雙 cause)、`control_signal_sink.h`(read / callback / waitForMessage、seal 交錯)與 V1–V11、S1–S16、K1–K16 全數實作。docker t3 / t4 / t5 三閘門 PASS(45 tests)。5-agent 對抗式查核:實作 0 must-fix;測試強度 4 must-fix(S5 遮蔽斷言空洞、S16a 缺 send 交錯、S16c 誤測 preamble 而非 response 路徑、K13/K14 無喚醒延遲上界)已修並複測綠。記錄之實作裁量:`INVALID_CONTEXT` 宣告未回傳(context 偵測待 T7 tick 執行緒);`rateWindowNs` 暫為建構參數(ManagerOptions 屬 T7);`calcHz` 依實際覆蓋時距正規化(消除 partial-bucket 稀釋);S14/S16 之 outcome 以 friend 通道決定性注入;S11 收斂單調性與 K16 TSan 子句移交 T12 sanitizer 矩陣 |
| v0.2.3 | T2.1–T2.6 完成:`liveness_state.h`(單寫者模型、activity-generation terminal seal、純計算 `calcState`)與 L1–L18 全數實作;docker t2 PASS、host TSan(L14 多執行緒)無 race、4-agent 對抗式語意查核 0 must-fix。閾值依 §4.3 為 `calcState` 逐呼叫參數(非建構參數,todo 原文以 §4.3 為準)。T0.5 勾選:framework PR #1 合併後 fresh clone workspace 實測 t0 PASS |
| v0.2.2 | Migrate 分支政策:`rv2_control_signal_transport` 以 `r1` branch 為 R1 新版主 branch(自 rv2 `master` 8bc3662 分出,master 凍結),階段 PR base 改為 `r1`;transport PR #1 與 framework PR 依此建立 |
| v0.2.1 | 新增 §1.4 Git 版控規範:agent 身分命名(`coco-claude` 等)、每階段獨立 branch(`<身分>/<項目>`)、完成後 push + PR + 回報;`r1_test_framework` remote 建立,T0.5 解除阻塞 |
| v0.2.0 | T1.1–T1.6 完成(docker t1 build 通過、`ros2 interface show` 10/10 解析、欄位↔條文逐欄查核通過)。**裁決 §12 #1 結案:新開 `r1_interfaces` package**——rosidl 型別名僅取檔案 basename(子目錄不入 namespace),`ControlSignalInfo`、`ControlSignalInfoReq`、`ControlSignalJoy`、`ControlSignalTwist` 與 `rv2_interfaces` legacy 型別同名衝突,無法照 §2.1 原文放置。框架佈局變更:`r1_test_framework` 自 package 內搬移至 workspace `src/r1_test_framework/`(獨立 repo 與各 package 平行,取代 §11.5.1 巢狀 submodule 模型),package 根目錄 symlink 改為相對路徑 `../r1_test_framework/*.sh`,腳本 `PKG_DIR` 解析順序改為 env → symlink 位置 → CWD;`todo_check.sh t1` 改查 `r1_interfaces`。t0 基線修復:legacy `csm_test_utils.h` `makeInfo()` 補上現行驗證必填之 `controller_name` / `priority` / `controller_priority_type`(t0 重驗 23 gtests 全綠) |
| v0.1.1 | T0.1–T0.4 查核完成勾選。t0 baseline 於 docker 實測通過(28 gtests 全綠,container 自動卸載,host 無殘留)；框架修正:container 內以空 tmpfs 遮蔽 `test_env/`(避免 ament linters 掃到產物之 418 筆誤報)、t0 篩選至既有 gtest 迴歸(legacy lint 一致性不在 R1 範圍;jazzy uncrustify 將 `.h` 以 C 解析致 `constexpr` 報錯,屬既有狀態) |
| v0.1.0 | 初版:大項 T0–T12、依賴序、逐小項查核條件、逐大項語意查核與 docker 實測指令；隨附 `r1_test_framework` 腳本組(test_build / test_deps / test_run / test_packages / test_clean / todo_check)與 package 根目錄接線(symlink、`test_depends.repos`、`.gitignore` 排除 `test_env/`) |

## 1. 使用方式與共通規範

**最新裁決優先(v0.8.25)**：使用者採 rebase 合併；framework 升版須遵守 §1.4 的「pull 後核對合併主線 SHA」流程。較舊歷史段落與已發布 framework README 中「只能 pin 原 tag／禁止 rebase」不再作為目前升版規則；保留歷史與原 tag，不為更新 README 改動本輪待固定的 framework tree。README 後續另行同步。

**Interfaces 進版裁決(v0.8.27)**：使用者現在要求補進版 commit；先前「維持 0.1.0、不附 release/tag」為歷史，不再適用本輪 PR。按現有 package.xml 0.1.0 正常升至 0.1.1，以獨立版本 commit/tag 記錄；不新增空 commit 或改寫原始版本歷史。

**文件位置與 snapshot(v0.8.28)**：本文件及設計稿改由 `rv2_project/docs/r1_design_docs/` 維護，適用範圍新增 `rv2_project`。其 `package.xml` 首版為 0.1.0，代表專案版本組合，不必是 release。新增 snapshot 依 §2.1.1 記錄各包已合併 release 的版本、精確 SHA 與原 tag tree 對照；不得從 dirty checkout 推定已發布內容，亦不自動更新 consumers 內部 framework pin。首次建立 ROS manifest 的 0.1.0 為使用者指定的 snapshot 初始值，不製造 0.0.0→0.1.0 回退／空 release commit；未要求 release 時不打 release tag。後續 snapshot 版本變更仍須獨立 commit，既有 snapshot 不覆寫。R1 packages 原獨立 release 規範不變。

**本輪裁決(v0.8.30)**：使用者要求先更新 project snapshot、進版並直接提出 PR／release tag；再將 transport `r1` 分支改為 R1-only、取消 legacy package 依賴，保留凍結 `master`，接續既有 I15/I18、T12/export 補強，最後同步 framework README。不得因移除 legacy 把 `rv2_interfaces::r1` C++ namespace 一併改名，或刪減 R1 113 cases。新的 framework 相容性變更也須獨立版本 PR，經使用者 merge 後才更新 consumer pins；開發 override 證據須明示不等於正式導入。Snapshot 升版先提交資料／gitlinks／文件，PR-ready 的候選只改 package.xml version，驗證後獨立提交該版本欄位並附同名 annotated tag，不混入其他來源，也不覆寫舊 snapshot。

### 1.1 清單結構

- **大項(T0–T13)**:一個可獨立驗收的里程碑,依 §2.1 檔案布局與編譯依賴排序。每個大項最後有「驗證」小節,分為兩部分:
  - **語意查核**:人工(或 code review)對照設計規劃書,確認測試案例所斷言的行為與 § 條文一致。這一步驗證「測試寫對了」,防止測試通過但語意偏離設計。
  - **實際測試**:在 docker 內執行該大項的測試集,以結束碼判定。這一步驗證「程式寫對了」。
- **小項(T*.n)**:一個可在單次工作階段內完成的實作單位。每個小項附**查核**條件:客觀、可觀察的完成判準。勾選 `[x]` 前必須滿足查核條件。
- 測試案例 ID(V/L/S/K/F/M/CM/H/I)沿用設計規劃書各章測試表,為**最低集合**；§11.3 另要求每個 class 的每個 function 皆有對應 unit test。

### 1.2 Docker 測試規範(host 零污染)

全部查核與測試一律在 docker container 內執行(§11.3),規則如下:

| 規則 | 內容 |
|---|---|
| Host 隔離 | 依賴安裝(apt / rosdep)、colcon build、測試執行全部發生在 container 內；host 僅存放原始碼與 `test_env/<distro>/` 產物目錄,不安裝任何測試依賴 |
| Image 共用 | 同一 distro 的所有項目共用**同一個官方 base image**(jazzy 為 `ros:jazzy-ros-base-noble`,§11.5.2),不建自訂 image；可以 `R1_TEST_BASE_IMAGE` 覆蓋 |
| Container 命名 | TODO 查核為 `r1_todo_<item>_<distro>`(例 `r1_todo_t2_jazzy`),標準流程為 `r1_test_<package>_<distro>`,便於識別與清理 |
| 測後卸載 | `todo_check.sh` 於查核結束(無論成敗)自動 `docker rm -f` 該 container；`-k` 可保留供除錯 |
| 產物 | 僅寫入 package 下 `test_env/<distro>/`(已列 `.gitignore`)；因 container 以 root 執行,清除產物用 `./r1_test_framework/test_clean.sh --purge-env`(經 docker 處理所有權),不需在 host 動用 sudo |
| 磁碟回收 | 需要釋放空間時 `./r1_test_framework/test_clean.sh --rmi` 移除 base image；下次查核會重新下載 |
| 跨容器 DDS 隔離 | **Docker 預設 bridge 不是 DDS 隔離**：未指定 domain 的容器同為 ROS_DOMAIN_ID=0，可互相 discovery／傳送同名 topic。不同 TODO 名稱或 owner/run 目錄也不隔離流量。在尚未提供並驗證獨立 ROS domain 或 network 前，所有會啟動 ROS nodes 的測試 job 必須串行，不只同 item 串行；純 lint／靜態查核可並行。不得只設定 host ROS_DOMAIN_ID 就宣稱已隔離，目前 test_build.sh 不會將該變數傳入容器。 |

### 1.3 查核執行指令

每個 R1 相關 package 均須將 framework 以 git submodule 引入至 `<package>/r1_test_framework/`，直接執行其中腳本。適用範圍包含 `rv2_control_signal_transport`、`r1_interfaces`、`r1_test_mocks`、`r1_integration_tests` 與未來的 R1 packages；framework 自身不必遞迴引入自己。不得依賴 workspace sibling checkout 或根目錄 shell symlink。

一般使用者只需以下四步，不必逐一知道 TODO item 或 sanitizer 選集：

```bash
./r1_test_framework/test_build.sh
./r1_test_framework/test_deps.sh
./r1_test_framework/test_run.sh
./r1_test_framework/test_clean.sh
```

無參數 test_run（或只指定 distro/TSan 開關）在步驟 1/2 的同一容器執行完整流程：一般完整 CTest（含全部 unit/integration 與既有註冊檢查）→適用 ASan→適用 UBSan→可選 TSan；owner 無定義的 sanitizer 明示 N/A。transport 適用三者、mocks 僅 UBSan、integration 僅 I10 ASan/TSan；interfaces 完成 build、無案例/無 sanitizer，不新增空測試。TSan 預設 off；完整流程中的 SKIP 不妨礙已啟用項目成功，但任何已啟用階段失敗仍使整體非零，不能宣稱 T12.2 通過。

完整流程新增持久 run-root 掛載，每次使用新 run/profile 的 build/install/log，不覆蓋前次證據或一般單項產物。來源維持唯讀、沿用既有 runtime/build/results gate、全程串行，不重建/清除容器或重裝依賴；清理由步驟 4 負責。run 摘要記錄各階段 PASS/FAIL/SKIP/N/A/NOT_RUN、exit code 與實際 log，失敗亦保留。

`-p/-s/-f/-c/-j/-k/-a` 為特殊單項執行參數；如 `test_run.sh -s all` 僅跑一般全測試、`-s unit` 僅 unit、`-a tsan -t on` 明確跑 TSan，保留非空選集與隔離驗證。`todo_check.sh` 保留給 agent/除錯的 TODO 映射，不再是使用者完整測試的必要入口。獨立 lint 仍只呼叫 `test_lint.sh`，不從 test_run 啟動其獨立 Docker；既有 ament CMake/XML/flake8/pep257/cppcheck 不因此刪除。Debian 打包/乾淨安裝暫維持 `test_packages.sh` 獨立（是否納入完整流程已詢問使用者，待裁決）。

從該 item 的目標 package 執行(附錄 B)：T0、T2–T9 從 transport、T1 從 `r1_interfaces`、T10 從 `r1_test_mocks`、T11 從 `r1_integration_tests`。

```bash
cd ~/Workspace/ros2_ws/src/<目標-package>
git submodule update --init --recursive
./r1_test_framework/todo_check.sh <item>          # 一鍵:建 container → 裝依賴 → build + test → 卸載
./r1_test_framework/todo_check.sh <item> -k       # 保留 container 供除錯
./r1_test_framework/todo_check.sh <item> -d humble  # 指定其他 distro
```

分步執行(等同 CI 腳本鏈,§11.3):`./r1_test_framework/test_build.sh` → `./r1_test_framework/test_deps.sh` → `./r1_test_framework/test_run.sh [-f <ctest 過濾>]` → `./r1_test_framework/test_clean.sh`。

`<item>` 對照表見附錄 B。

### 1.3.1 測試目錄與分類

- 所有 package 必須有 `test/unit/` 與 `test/integration/`；無案例的一側以 README 說明，不新增空殼測試。
- `unit/` 驗證單一 function/class 合約，例如 Info 驗證、LivenessState、Source、Sink、Factory、Handle 基本操作、StatusFaultNode 單一代理行為；使用 ROS 或裸 probe 不會自動變成 integration。
- `integration/` 驗證多元件的系統協作，包括單一 package 內的 CSM 註冊、heartbeat、callback 派送、master 對帳及 retry。M1–M26、CM1–CM13、Handle H7–H8、mock 控制/資料通訊 smoke、I00/I1–I18 放在此類。
- 共用 fixture/helper 可留於 `test/`，可執行測試案例必須放入上述兩類。混合單一合約與系統流程的檔案須拆開，保留既有 case ID 與斷言。
- CMake 更新來源/include 路徑，CTest 標示 `unit` / `integration` labels；預設執行兩類，`./r1_test_framework/test_run.sh -s unit` 或 `-s integration` 可分開驗證，指定類別空匹配必須失敗。
- 遷移先修文件，再改各 package；框架先完成版本 PR 並經使用者 merge，再由本地 framework master pull 並核對合併後版本 SHA，package 固定該 SHA(§1.4)。不得以 rebase 前的 tag SHA 代替核對；workspace sibling framework 可保留作開發 checkout，但不可作 package 執行依賴。

### 1.3.2 PR 前 lint(格式已確認)

TSan 的人工停用規範另見 §1.3.3，不得將其 SKIP 當成 lint 或 T12 完成證據。

- 採用含 lint 的 framework 版本後，每次準備 PR 必須在目標 package 執行 `./r1_test_framework/test_lint.sh`，通過後才附獨立版本 commit；不得把版本欄位提早混入開發 commit。framework 版本 PR 須先經使用者 merge，各 package 才可更新 gitlink。
- lint 為獨立 Docker 唯讀流程，不需先 build/deps，不重用或清除既有測試容器。固定官方 Jazzy base image 與 clang-format 18/Ruff 0.15.7/ShellCheck 工具環境；不安裝 host 依賴、不建客製 image、不自動修正來源。詳細命令與適用範圍見 framework README。
- C/C++ 以 LLVM 為基底，採 Allman、4 spaces、namespace 不縮排、保留 include 順序、120 欄與 class 內短函式單行。Python 為 PEP 8/Black 相容 Ruff format/check；Bash/sh 為語法檢查與 ShellCheck。這不是 C/C++ 編譯或語意分析的替代。
- transport 僅排除 `ament_cmake_uncrustify` 註冊：C/C++ 格式由既定 clang-format gate 負責，不另維護不同 formatter 的規則。保留 flake8/pep257 的額外檢查，因 Ruff E4/E7/E9/F/I 不涵蓋全部 builtins/comprehensions/docstring 規則；`test/ament_flake8.ini` 保留 Jazzy 原有設定，只將 `inline-quotes = double` 對齊共用 Ruff，不新增 rule ignores。三份 launch module docstring 的 raw string/句尾標點與 CMake 縮排直接修正。`cppcheck`、`lint_cmake`、`xmllint` 均保留，工具原生 SKIP 如實回報。`test_run.sh` 與獨立 `test_lint.sh` 都必須成功；不得因此刪減 unit/integration targets、labels 或斷言。
- C/C++ lint 依 v0.8.10 使用者裁決，**僅比對 clang-format 18 原生輸出**，不再加註解/namespace 詞法檢查或修改 formatter 輸出。`//` 前兩格、不對齊註解欄、巢狀 namespace 同縮排不合併、`FixNamespaceComments: true` 與 `ShortNamespaceLines: 0` 保留；formatter 能修正的間距與 namespace 名稱仍須通過。這取代先前「所有情況強制檢查」裁決，不是略過整份含註解或 macro 的檔案。
- 排除 clang-format 無法自動處理的額外要求：`/* */`/`/**< */` 前強制兩格(改採原生間距)、完全空 namespace 缺少結尾名稱、macro/token-paste/跨條件編譯的 namespace 語意推論與額外括號/詞法驗證、`clang-format off` 或 formatter 原生略過區段內的額外檢查、多行 block 的強制星號/獨立 delimiter/非空內容與 Doxygen `@brief`/限定註解型態。formatter 自己仍會調整的部分照常比對，執行失敗仍回傳非零；不額外豁免 C/C++ 一般格式，也不放寬 Python/Ruff 或 ShellCheck。
- lint 失敗時由開發者決定修正，例如明確指定檔案執行 `clang-format-18 --style=file:./r1_test_framework/.clang-format -i <file>`，檢查 diff 後重跑 lint。框架不得自行批次格式化、修改 legacy rv2 文件或改測試斷言。
- v0.8.12 本輪使用者明確授權 clang-format 修正一次：只格式化各 package owner lint 清單內的 C/C++(含 transport legacy)，不碰 generated、vendored、symlink、nested repo 或 submodule。格式化工具仍在 Docker 內執行，以 owner UID/GID 寫回，保留 Python/Shell、Doxyfile、package.xml 與 gitlink；完成後重跑唯讀 lint，剩餘非 C/C++ 違規另行回報，不擴張本輪修改範圍。這是開發者主動修正，不改 `test_lint.sh` 的唯讀性；試行結果先保留 diff，不進行 release/PR。
- v0.8.13 使用者另行授權接續 Python 修正：各 package 使用 `./r1_test_framework/lint/ruff.toml`，相當於 Python 的共用格式/lint 設定；語法目標 `py310`、88 欄、4 spaces、雙引號、LF，啟用 E4/E7/E9/F/I。Ruff 版本由 `lint/requirements.txt` 固定；設定不由 owner 的其他檔案覆蓋。Docker 內明確選定 owner Python 檔案，執行 `ruff check --fix --no-unsafe-fixes --config <共用設定>` 再 `ruff format --config <共用設定>`，之後重跑原唯讀 lint。此為使用者要求的來源修正，不改框架的唯讀合約或先前 C/C++ diff；設定、Doxyfile、package.xml 與 gitlink 不動，本輪保留未提交 diff。
  手動 Ruff 修正須與現有 lint gate 同在 container 的 `/` 工作目錄執行，設定與來源使用絕對路徑，並加 `--no-cache`。顯式 `--config` 下 Ruff 預設以 cwd 推定 first-party imports；若切到 owner 根目錄，transport 的 `launch/` 會改變 import 分組。不另加設定覆蓋來掩蓋差異。
- 多行說明仍建議使用對齊星號的 `/* */`，class/function API 文件仍建議 Doxygen JavaDoc-style `/** */` 與 `@brief`、`@param`、`@return`；這些 formatter 無法保證的文件慣例暫不作 lint gate。`ReflowComments: false` 保留，不產生或改寫文件內容。API 文件覆蓋與描述正確性仍由 review 判斷，不修改 rv2 Doxyfile。
- Framework PR #5 已由使用者 rebase merge，T0.7 framework 驗收完成。已驗證主線 `5316f3e` 與 v0.2.0 tag 所指 `631a85b` 內容一致；consumer gitlink 使用原 tag commit，不重打 tag。package 自身版本與 integration header/source 布局不因本輪 gitlink 升級改動；新版 lint 必須如實回報，未通過時不得自行批次格式化或跳過 PR 閘門。本輪不新增 CI workflow，也不自行合併 PR。
- 本版能力限縮的 framework v0.2.1 [PR #6](https://github.com/cocobird231/r1_test_framework/pull/6) 已由使用者 merge；驗證主線 `f86fcd9` 與既有 tag commit `3dd3c27` tree 相同後，consumer 固定後者，不重打 tag。各 package 必須使用自己的 nested 入口重新驗證，不能用 framework 自身 PASS 或先前 override 預驗證替代；導入結果見 T0.7。

### 1.3.3 TSan 明確開關

- 使用者最新裁決取代 v0.8.20：`todo_check.sh <item> -t on|off` 與 `test_run.sh ... -t on|off` **預設 off**；明確 on 才啟用 TSan。完整流程的 on 加入該 owner TSan 階段；特殊單項仍需 `-a tsan`／`t12-tsan`。
- 單獨 TSan job 為 off 時，stdout 明示 `SKIP`、owner/原因與 TSan 未執行，exit `77`（不是 PASS），在 Docker 存取、產物建立/清除與 cleanup trap 前返回。完整流程則記錄 TSan 為 SKIP/77，繼續其他已啟用項目；一般、ASan、UBSan 與打包不因 off 被略過。
- 不接受 on/off 以外的值、缺值或多餘參數；無效 owner/item、sanitizer 與互斥參數仍失敗。不得在 runtime 失敗後自動改為 off，也不得以未 instrument 的重跑冒稱 TSan 成功。
- 排程若選擇繼續其他 jobs，須單獨記錄 exit 77 為 SKIP，其他非零仍中止；不能用 `|| true` 吞掉所有錯誤。SKIP 不滿足 T12.2，該項保留未完成，需支援環境以 on 真正驗收。
- 不自動更改 host sysctl/ASLR、Docker seccomp/capabilities 或加入 suppressions。新旗標依 §1.4 先完成 framework PR/merge 才能導入 consumer；開發期使用明確 owner override，不修改已發布 tag 或 nested gitlink。

### 1.4 Git 版控規範(v0.2.1;v0.2.2 增列 migrate 分支政策;v0.5.1 增列文件修訂署名;v0.8.2 增列 package 定版)

適用於本案全部 repos(`rv2_control_signal_transport`、`r1_test_framework`、`r1_interfaces`,以及日後的 `r1_test_mocks`、`r1_integration_tests`):

| 規則 | 內容 |
|---|---|
| Commit 身分 | AI agent 產出之 commit 以 repo-local `git config user.name` 標示身分,命名 `coco-<agent>`:Codex 為 `coco-codex`、Claude 為 `coco-claude`、ChatGPT 為 `coco-gpt`,依此類推 |
| 文件修訂紀錄 | 每次更動 `r1_todo.md` 或 `r1_design_draft.md` 時,必須同步更新該文件的版本號、於 §0「版本歷史」新增一筆紀錄,並在該筆說明或摘要開頭以 `更新 Agent:coco-<agent>` 明確標示實際更新者(例如 `coco-codex`、`coco-claude`)；不得只修改內文,也不得省略版本號、版本歷史或更新 Agent 中的任一項 |
| 分支模型 | 每個階段(一個或連續數個 TODO 大項)之新增、修改、刪除一律開新 branch,不直接 commit 至主 branch。branch 命名 `<身分>/<項目>`,如 `coco-claude/T0-T1`、`coco-claude/T2` |
| **Migrate 分支政策(v0.2.2)** | 既有 rv2 packages 處於 migrate 階段:R1 新版程式碼以 **`r1` branch 為新版主 branch**,rv2 既有版本(`master`)凍結不動。`rv2_control_signal_transport` 之階段 PR 一律以 `r1` 為 base;純 R1 新 repos(`r1_test_framework`、`r1_interfaces` 等)無 rv2 包袱,主 branch 即 `master` |
| Package 版本 | 每個 R1 package 獨立管理版本，首次定版從 `v0.1.0` 開始，不要求 packages 同步升版。ROS2 package 以根目錄 `package.xml` 的 `<version>` 為來源，僅同步屬於同一 R1 release 範圍的其他版本欄位；`rv2_control_signal_transport/Doxyfile` 屬於 rv2，維持原內容，不隨 R1 定版修改。非 ROS package 的 `r1_test_framework` 使用根目錄 `VERSION`，不為定版新增 ROS manifest，也不修改測試 fixture 版本。檔案內版本不含 `v` 前綴。文件自身的修訂版本沿用原序列，不屬 package release、不重設 |
| 版本 commit 與 tag | 功能、測試、文件變更先提交，版本欄位不得提前混入這些 commit；完成驗證、準備提出 PR 時才附獨立版本 commit，只含版本欄位變更，訊息包含 `vX.Y.Z`(如 `chore(release): v0.1.0`)，並建立同名 Git tag 指向該 commit。目前手動執行，未來才由 GitHub Actions 產生；本輪不實作 workflow。mocks/integration 已提前有 0.1.0 而使用空 release commit，僅為使用者准許的首次定版例外，不作為後續慣例。合併方式由使用者決定，採 rebase 時預期 commit SHA 改變；版本提交仍應可在合併後歷史辨識。不得自行移動或覆寫既有 tag，也不能以保留 tag 為由繼續 pin 合併前 SHA；依下列流程核對新的主線版本 SHA |
| 完成流程 | 階段完成(該大項查核與實測通過)後:附版本 commit/tag → push branch 與 tag → 對主 branch 提出 PR → 回報使用者。PR 合併由使用者裁決；無 remote 的 repo 暫存本地，待具備 PR 條件才附 release commit |
| Framework 升版順序 | 先提交 framework 版本 PR，等待使用者 merge。檢查本地 framework 工作樹乾淨，再切 master 執行 `git pull --ff-only origin master`；不能只 fetch 或沿用記憶中的 SHA。核對本地 HEAD、origin/master、即時遠端主線 SHA 一致，並確認 PR 已合併、VERSION、主線版本 commit 與預期 release 內容。rebase 後 consumer 必須固定此已核對的合併主線版本 SHA，而非合併前 tag；記錄舊／新 SHA 與 tree 比較。若 pull 不能 fast-forward、工作樹不乾淨或主線有超出欲導入版本的額外變更，先查核／回報，不 reset、force pull 或直接追最新開發內容。各 nested repo fetch 後 checkout 該精確 SHA，以 gitlink-only commit 保存；測試／一般 clone 不得自動追 HEAD，仍用 submodule update 還原固定 SHA。package PR／獨立定版另依完成流程 |
| Remote | `r1_test_framework`(private):`git@github.com:cocobird231/r1_test_framework.git`；`r1_test_mocks`:`git@github.com:cocobird231/r1_test_mocks.git`；`r1_interfaces`:`git@github.com:cocobird231/r1_interfaces.git`（v0.8.22 已確認 SSH/API 權限恢復）。Interfaces 自 v0.8.27 使用者新裁決起恢復正常獨立進版，本輪 0.1.0→0.1.1，附只改版本欄位的 commit/tag 並更新原 PR；先前暫緩定版例外僅為歷史，不製造版本回退或空 commit。 |

### 1.5 前置裁決(開工前決定)

| 裁決點 | 影響大項 | §12 編號 | 暫定預設 |
|---|---|---|---|
| msg/srv 放置於 `rv2_interfaces/msg/r1/` 或新開 `r1_interfaces` | T1 | #1 | **已裁決(v0.2.0):新開 `r1_interfaces`**。rosidl 型別名僅取 basename,四個型別與 legacy 衝突,暫置方案不可行 |
| retry 參數數值與 policy(initial/max delay、initial cap、`auto_retry` 歸屬) | T7.7 | #6 | 實作時提案預設值,寫入 `RetryPolicy` 預設建構並回饋規劃書 |
| `registerSource` async 版本 | T7.4 | #3 | 首版僅同步版,介面預留擴充 |
| 使用者層 forced disconnect API | T8 | #5 | 首版不開放,內部保留 forced 路徑 |

---

## 2. 里程碑總覽與依賴序

```mermaid
graph LR
    T0["T0 測試框架"] --> T1["T1 介面定義"]
    T1 --> T3["T3 Info 驗證"]
    T0 --> T2["T2 LivenessState"]
    T2 --> T4["T4 Source"]
    T3 --> T4
    T2 --> T5["T5 Sink"]
    T3 --> T5
    T4 --> T6["T6 Factory"]
    T5 --> T6
    T6 --> T7["T7 Manager"]
    T7 --> T8["T8 Handles"]
    T7 --> T9["T9 CsmMaster"]
    T1 --> T10["T10 mocks"]
    T8 --> T11["T11 整合測試"]
    T9 --> T11
    T10 --> T11
    T11 --> T12["T12 Sanitizer 與打包"]
```

| 大項 | 內容 | 產出位置 | 測試案例 |
|---|---|---|---|
| T0 | 測試框架與 docker 環境 | `r1_test_framework/` + package 根目錄 | —(框架自身查核) |
| T1 | msg/srv 介面定義 | `r1_interfaces/msg/`、`srv/`(§12 #1 裁決) | —(build + 欄位對照) |
| T2 | `r1::LivenessState` | `include/.../r1/liveness_state.h` | L1–L18 |
| T3 | Info 與驗證 | `include/.../r1/control_signal_info.h` | V1–V11 |
| T4 | `r1::ControlSignalSource` | `include/.../r1/control_signal_source.h` | S1–S16 |
| T5 | `r1::ControlSignalSink` | `include/.../r1/control_signal_sink.h` | K1–K16 |
| T6 | Factory 與型別註冊 | `include/.../r1/control_signal_factory.h` + `src/r1/` | F1–F5 |
| T7 | `r1::ControlSignalManager` | `include/.../r1/control_signal_manager.h`、`source_registration.h` | M1–M26 |
| T8 | Handles | `include/.../r1/control_signal_handles.h` | H1–H8 |
| T9 | `r1::CsmMaster` + node | `include/.../r1/csm_master.h`、`src/r1/csm_master.cpp` | CM1–CM13 |
| T10 | `r1_test_mocks` package | `ros2_ws/src/r1_test_mocks/` | —(mock 行為 smoke) |
| T11 | `r1_integration_tests` package | `ros2_ws/src/r1_integration_tests/` | I1–I18 |
| T12 | Sanitizer 矩陣、迴歸、打包 | —(建置組態與 `.deb`) | §11.4 矩陣 |
| T13 | 專案 snapshot ROS2 package | `rv2_project/`、`snapshots/v0.1.0.json` | snapshot unit／integration |

### 2.1 總驗收前未完成清單(2026-09-13 盤點)

以下與舊里程碑的歷史測試結果分開管理；本輪沒有重跑全部 R1 測試。

| 項目 | 狀態／完成條件 |
|---|---|
| transport PR #8／新 snapshot | 已確認合併，主線 `r1` 為 cc7cec22043f80b1a4179ae9acdf5a0e6b98105e／v0.1.2；與原 tag 8f56a55 tree 相同。T14.1 實際 pull 後納入 project v0.1.1，其他四包仍為最新已合併版本，不混入後續尚未合併 PR。 |
| transport T12/export 補強 | 已在乾淨分支獨立提交 423ff10：r1_interfaces export、L14/S11/K12/K15/K16/M22；原工作樹保持不動。尚不屬已合併 v0.1.2，正式新版 nested 驗證／定版／PR 待 framework #9 merge。 |
| integration I15/I18 | 已在乾淨分支原樣提交 6a36157；移除 legacy local dependency 另作 58e167d。尚待本輪 clean-dependency 驗證與定版；I10 shutdown 已隨 v0.1.1 合併，不重複列為欠項。 |
| legacy rv2_interfaces | Transport 664a1a4 已移除 17 份 legacy 檔案與對應 build/install/dependencies；R1 production/API、Doxyfile、master／舊 tags／legacy repo 原使用者改動皆保留。新測試 workspace 只有 R1 dependencies，未掛載 legacy repo；正式 release 與 closure 驗收仍待 T14.2。 |
| T12.2 | TSan runtime 平台阻塞；須在支援環境由兩個 owner 明確 `-t on` 通過。預設 SKIP/77 不算完成，不更動主機安全設定。 |
| framework README／R1-only 相容性 | 已完成並發布 v0.5.1／[PR #9](https://github.com/cocobird231/r1_test_framework/pull/9)，版本 commit/tag a058498；README 對齊 §1.4。UBSan 保留五個 R1 floor，未篩選 CTest discovery 的全部 unit 必須實跑；legacy 若仍註冊或建出亦必須跑。T0 改為全部功能 targets，正反例／既有回歸與 lint 通過。Consumer 正式導入仍待使用者 merge、literal pull／新 SHA 核對。 |
| 總驗收 | T13 snapshot metadata 自身驗收已完成，不代表整體 R1 完成。上述已提交版本、依賴缺口與待發布補強收斂後，才對精確 snapshot 串行跑各 owner 四步／lint 及另列的打包、TSan；現有 dirty PASS 不代替最終驗收。 |

§12 的 HA、async API、adapter、durable fencing 等未來政策不自動擴張成此次 v0.1.0 的必做實作。

---

## T0 測試框架與 docker 環境(§11.5)

**目標**:建立全案共用的 docker 化測試流程,後續所有大項的「實際測試」都經由本框架執行。
**依賴**:無(最先執行)。

- [x] **T0.1** `r1_test_framework/` 腳本組:`test_build.sh`、`test_deps.sh`、`test_run.sh`、`test_packages.sh`(§11.5.3 四支標準腳本)加上 `test_clean.sh`(卸載)與 `todo_check.sh`(TODO 查核執行器),以獨立 git repo 版控。
  查核:`bash -n` 全數通過；每支腳本有用法說明；`git log` 存在初始 commit。
- [x] **T0.2** 各 R1 package 根目錄以 `.gitmodules` + gitlink 引入 `r1_test_framework/`；保留各自 `test_depends.repos` 的 local dependency 宣告，`.gitignore` 排除 `test_env/`，移除舊根目錄腳本 symlink。
  查核：四個現有 R1 packages 的 `git ls-files --stage r1_test_framework` 均為 mode `160000` 且 pin 同一經驗證 commit；`git submodule status` 無未初始化/髒版本；由 package 內直接執行框架腳本可解析正確 PKG_DIR。✅ v0.8.3 四者均固定 framework `v0.1.0` tag 所指 `12cc2dd`，已核對與 merge 後主線 tree 相同；nested 入口、明確 override 與其他 CWD 均經驗證。v0.8.1 移除的 18 個舊 symlink 保留 Git 歷史可供還原。
- [x] **T0.3** Container 生命週期驗證:base image 下載、container 建立、掛載(原始碼唯讀、`test_env` 一對一)、卸載。
  查核:`./r1_test_framework/test_build.sh` 後 `docker ps` 可見 container；container 內 `ls /root/ros2_ws/src/` 見本 package 與 `rv2_interfaces`；`./r1_test_framework/test_clean.sh` 後 `docker ps -a` 無殘留；host 上除 `test_env/` 外無任何新檔案。
- [x] **T0.4** Baseline 全鏈:以現有 rv2 package 走完 build → deps → run,證明框架可獨立完成一次完整測試。
  查核:`./r1_test_framework/todo_check.sh t0` 結束碼 0,輸出含 `colcon test` 結果與 `PASS: t0`。
- [x] **T0.5** 框架獨立版控與可重現引入：framework 維持獨立 remote，各 package 以內嵌 submodule 固定 commit；`git clone` + `git submodule update --init --recursive` 後即可使用。
  查核：在無 sibling framework 的驗證 checkout 中執行 nested 腳本，確認從 package 內及其他 CWD 均解析相同 package；Docker build/test 與測後卸載成功，不自動追遠端 HEAD。✅ `r1_interfaces` fresh clone 從 GitHub 還原框架 gitlink，從 `r1_test_mocks` CWD 以絕對 nested 路徑執行 build→deps→run，容器只掛該 clone 與其 `test_env`；build PASS且測後卸載。
- [x] **T0.6** 全 package 測試分層：依 §1.3.1 搬移測試與更新 CMake/include/helper/文件，保留既有案例覆蓋與 TODO filter；混合 Handle 檔拆分 unit H1–H6 與 integration H7–H8。
  查核：`test/` 頂層無 executable test cases；CTest unit/integration labels、T0–T11 篩選與案例 ID 都保留；transport 兩類、mock 兩類、I00–I18 及 interfaces build/interface gate 均在 Docker 通過。✅ transport 6 unit targets/84 cases與4 integration targets/50 cases全綠；mocks 1 unit/3 integration targets、23 cases(T10彙總27)全綠；T11 19 integration targets(彙總39)全綠；T1 build及10個介面解析通過。框架自身Docker回歸涵蓋精確分類、名稱交集、無CTest與空CTest、失敗傳遞；實際 interfaces `-s unit` 明確拒絕空匹配。
- [x] **T0.7** PR 前 lint gate 與格式定版：獨立 `test_lint.sh`、`.clang-format`、Python/Shell 規則與正反例回歸；使用者已確認並合併 framework PR #5。consumer 導入的 lint 結果與 PR 條件另列下方，不與 framework 自身驗收混為一談。
  查核：Docker 內證明合規 PASS、違規非零、來源唯讀不變、nested/standalone/override 路徑正確、generated/submodule/symlink 排除及工具失敗傳遞；使用者確認格式後才附 framework 版本 commit/tag 與 PR。候選階段不視為已正式啟用於所有 packages。v0.8.5 候選實測：framework 自身 `./test_lint.sh` PASS(C/C++ 2、Python 2、Shell 13 files)；11 個 lint unit regressions、入口整合回歸與既有 package 路徑回歸全過。`.clang-format-ignore` 靜默跳過先實證失敗再以 stdin 修正；ShellCheck 共用來源解析及單一 source annotation 消除跨檔變數誤報，未關閉任何整體規則。當時仍待使用者確認格式，故未勾選。
  v0.8.6 補驗：Docker 內 33 個註解/namespace 詞法測試與 14 個 lint 回歸測試全過，入口整合與既有 package 路徑回歸通過；framework 全檔 lint PASS(C/C++ 2、Python 4、Shell 13 files)。涵蓋兩類註解、連續註解、empty/nested/inline/anonymous namespace、字串/raw string、formatter-off、條件分支、line splice 與可見 token-paste macro；格式違規/名稱缺漏回傳非零，唯讀來源不變。外部 macro 展開語意不在詞法證明範圍。
  v0.8.7 補驗：Docker 內 41 個註解/namespace 測試、15 個 lint 回歸測試、入口整合及 framework 全檔 lint 通過。新增多行 block/Doxygen 正反例、星號縮排、CRLF、空 placeholder、缺少/偽造摘要、inline member doc、formatter-off 與保留 code/list 縮排；空區塊/錯位星號先實證未被舊 lint 攔下，再補規則通過。既有 normalizer 仍只處理行內間距，不掩蓋 block 結構違規；獨立複核無 must-fix。
  v0.8.8 定版：本輪重新執行 framework `./test_lint.sh` PASS(C/C++ 2、Python 4、Shell 13 files)；格式確認只改文件/註解，lint 程式與測試仍為 v0.8.7 已驗證內容，沿用 56 個回歸結果。Docker release metadata 驗證通過。獨立版本 commit/tag `v0.2.0` 指向 `631a85bce7d4b6f1826b06244f9c77b33c6e6f8f`，已推送 [PR #5](https://github.com/cocobird231/r1_test_framework/pull/5)；使用 merge commit 保留 SHA，不 squash/rebase、不移動 tag。各 package 仍 pin 原有 v0.1.0，待使用者 merge 後才升級。

  v0.8.9 consumer 導入：四個 package 均於新分支 `coco-codex/framework-v0.2.0` 建立下列本地 dependency commit，只將 framework gitlink 由 `12cc2dd` 更新至 v0.2.0 的 `631a85b`。各 package 根目錄實際執行 `env -u R1_TEST_PKG_DIR ./r1_test_framework/test_lint.sh`，確認解析自身 package；結果如下，失敗數為檢查數而非檔案數或功能測試案例數。

  | Package | Dependency commit | Docker lint 結果 | 本地 log(相對各 package 根目錄) |
  |---|---|---|---|
  | `rv2_control_signal_transport` | `9dddb72` | FAIL(exit 1)：C/C++ 32、Python 3、Shell 1 files；66 failed checks | `test_env/lint-framework-v0.2.0.GEb4HC.log` |
  | `r1_test_mocks` | `9bb6a65` | FAIL(exit 1)：C/C++ 16 files；11 failed checks | `test_env/lint-framework-v0.2.0.TLzvrv.log` |
  | `r1_integration_tests` | `059da43` | FAIL(exit 1)：C/C++ 4、Python 20 files；28 failed checks | `test_env/lint-framework-v0.2.0.Dh5fVq.log` |
  | `r1_interfaces` | `aaacf4a` | SKIP(exit 0)：無支援的來源檔案；不代表 msg/srv、XML 或 CMake 已通過 lint | `test_env/lint-framework-v0.2.0.GejZwy.log` |

  既有來源不符合新版規則：transport 包含 legacy 與 R1 的 C/C++ 格式、註解間距、Doxygen `@brief`、namespace macro 無法驗證及 Python 格式；mocks 為 C/C++ 格式；integration 為 C/C++ 格式/註解與 Ruff 格式、import 排序及 unused import。namespace macro 限制不是單跑 clang-format 即可解決，後續修正範圍須由使用者裁決。本輪不修來源、不豁免規則；三個 FAIL packages 尚未達 PR-ready，interfaces 另因無 remote 留本地，故四者均未 push、附 package release commit/tag 或提出 PR。

  官方 Jazzy Docker metadata 驗證通過：四個 framework `VERSION=0.2.0`、nested lint 入口存在、四個 `package.xml=0.1.0`。唯讀複核確認各 commit 僅修改 gitlink、來源與 rv2 Doxyfile 未變；v0.1.0 至 v0.2.0 既有 build/test 執行腳本內容相同，本輪未重跑完整功能測試。lint 與 metadata 驗證容器均自動卸載。若需回退，此 gitlink-only commit 可獨立 revert 回原 pin，不涉及格式或資料遷移。

  v0.8.10 原生能力邊界修訂：官方 Jazzy Docker 的 clang-format 18.1.3 以 14 個 stdin 案例盤點能力。新增 5 個 lint 測試方法的 16 個子案例先在舊 checker 證明 FAIL：來源已是 formatter 固定點，仍被補充規則/normalizer 拒絕。移除不再適用的補充 checker 與其 41 個專屬測試，改以實際 formatter 的正反例驗證；完整 `test/unit/test_lint.py` 18 tests PASS，入口整合、package 路徑回歸與 Ruff format/check PASS。framework `./test_lint.sh` 全檔 PASS(C/C++ 2、Python 2、Shell 13 files，0 failed checks)，獨立複核無 must-fix；工具錯誤、唯讀、排除清單及 Python/Shell 規則未放寬。

  transport 以 `R1_TEST_PKG_DIR` 指向原 package、使用 framework 開發 checkout 的 `test_lint.sh` 唯讀預驗證，gitlink 不動：仍 FAIL(exit 1)，C/C++ 32、Python 3、Shell 1 files，35 failed checks(原 v0.2.0 為 66)。已無補充 comment/macro 診斷，剩下 clang-format 與 Ruff 格式差異；本地 log 為 transport `test_env/jazzy/lint-native-framework.383BiG.log`。其他 consumers 不重跑，不能推論已通過；四者來源/版本/gitlink 均未改，本輪未重跑完整功能測試。

  framework 功能 commit `d3007d4` 後，才以獨立 `chore(release): v0.2.1` commit `3dd3c27d1147e96b0c902ffdfa04fff3244a8fab` 更新 VERSION 與 README 安裝 tag，並加同名 annotated tag；已推送 [PR #6](https://github.com/cocobird231/r1_test_framework/pull/6)。Docker release metadata 驗證通過，測試 fixture 維持原有 `0.0.0`，未新增 ROS manifest。所有驗證容器已卸載；等待使用者 merge，才可更新 consumer gitlinks，既有 PR 前 lint 與獨立版本 commit 條件不變。

  v0.8.11 consumer 導入：PR #6 經使用者合併後，四個 package 在新分支 `coco-codex/framework-v0.2.1`，保留前次 v0.2.0 dependency commit，再將 gitlink 由 `631a85b` 更新為 v0.2.1 的 `3dd3c27`。各 package 根目錄實際執行 `env -u R1_TEST_PKG_DIR ./r1_test_framework/test_lint.sh`，確定新版 nested 入口解析自身 package；結果如下，failed checks 不等於檔案數或功能測試案例數。

  | Package | 本地 dependency commit | Docker lint 結果 | 本地 log(相對各 package 根目錄) |
  |---|---|---|---|
  | `rv2_control_signal_transport` | `45c2444` | FAIL(exit 1)：C/C++ 32、Python 3、Shell 1 files；35 failed checks | `test_env/jazzy/lint-framework-v0.2.1.EROzb5.log` |
  | `r1_test_mocks` | `608f2ee` | FAIL(exit 1)：C/C++ 16 files；11 failed checks | `test_env/jazzy/lint-framework-v0.2.1.GYus6B.log` |
  | `r1_integration_tests` | `e2ea1b0` | FAIL(exit 1)：C/C++ 4、Python 20 files；26 failed checks | `test_env/jazzy/lint-framework-v0.2.1.ey24Ov.log` |
  | `r1_interfaces` | `ccfe565` | SKIP(exit 0)：無支援來源，不代表 msg/srv、XML 或 CMake 已通過 lint | `test_env/jazzy/lint-framework-v0.2.1.knzjdC.log` |

  舊補充 comment/namespace gate 已不再啟用，剩餘失敗為既有 C/C++ 格式及 Python/Ruff 格式、import 排序與 unused import；不批次修正來源、不跳過既有 gate。三個 FAIL packages 未達 PR-ready，interfaces 另無 remote，故四者均未 push、附 package release commit/tag 或提出 PR，需使用者裁決後續修正範圍。

  官方 Jazzy Docker metadata PASS：四個 nested framework 的 `VERSION=0.2.1`、lint 入口存在且補充 checker 已移除，四個 `package.xml=0.1.0`。唯讀 audit 確認 consumer 僅此四個、既有 build/deps/run/clean/packages/todo_check/_common 腳本在兩版間內容相同；本輪不重跑完整功能測試。各 dependency commit 僅更動 gitlink，所有來源、Doxyfile 與布局保留，驗證容器均自動卸載。可獨立 revert 本輪 gitlink commit 回原 v0.2.0 pin，不改動既有開發紀錄。

  v0.8.12 clang-format 單輪試行：三個有 C/C++ 的 package 與本文件 repo 開新分支 `coco-codex/clang-format-pass`，interfaces 無 C/C++，保留原分支。以各 owner 的 NUL Git manifest 與原 `select_files()` 選出 32/16/4/0 個 C/C++ 檔；generated、vendored、symlink、nested repo/submodule 均排除。官方 Jazzy Docker 內使用 clang-format 18.1.3、各 package 的既有 `.clang-format`，以 host UID/GID 對每個選中檔案執行一次原生 `-i`。先確認路徑上沒有 `.clang-format-ignore`，逐檔驗證寫回內容等於格式化前來源經 stdin 產生的原生輸出，UID/GID/mode 均保留；沒有額外手動改 C/C++。

  | Package | C/C++ 選檔 / 實際改檔 | 實際 nested lint 結果 | 本地 log(相對各 package 根目錄) |
  |---|---|---|---|
  | `rv2_control_signal_transport` | 32 / 32 | C/C++ 全過；整包 FAIL(exit 1)，只剩 3 個 Python/Ruff 格式檢查 | `test_env/jazzy/lint-clang-format-pass.cfdcpn.log` |
  | `r1_test_mocks` | 16 / 11 | PASS(exit 0)，0 failed checks | `test_env/jazzy/lint-clang-format-pass.VqTiOw.log` |
  | `r1_integration_tests` | 4 / 4 | C/C++ 全過；整包 FAIL(exit 1)，剩 22 個 Python/Ruff 檢查 | `test_env/jazzy/lint-clang-format-pass.SBUXsG.log` |
  | `r1_interfaces` | 0 / 0 | SKIP(exit 0)：無支援來源，不視為介面格式已驗證 | `test_env/jazzy/lint-clang-format-pass.3VcV5X.log` |

  transport 剩下三個 `launch/*.py` 的 Ruff format 差異；integration 剩下 20 個 Python 格式檢查，另 `r1_itest.py` 的 import 排序與 `scenario_i04_confirmed_death_rebuild.py` 的 unused `re` import，共 22 failed checks(不是 22 個檔案)。本輪未執行 Ruff 修正，也未修改 Python/Shell、Doxyfile、CMake、package.xml、.gitmodules 或 gitlink；框架仍 pin v0.2.1、各 package 版本維持 0.1.0。

  所有 C/C++ 差異來自原生 formatter；除空白、換行及註解間距外，formatter 亦依既有預設排序 5 檔的 `using` 宣告(transport 4、integration 1)，不宣稱只變更空白。兩個 agent 分區唯讀詞法/人工 diff 複核無 must-fix：字串/字元內容保留，兩個 factory macro 的函式式定義、token paste 與續行範圍未變，`using` 宣告集合不變；這不是完整編譯或執行期語意證明。`git diff --check` 通過，測試斷言與檔案布局未手動修改；本輪未重跑編譯或功能測試。格式化及四個 lint 容器均已自動卸載；所有改動保留 unstaged diff，不 commit/push、不附 release commit/tag、不開 PR，待使用者檢視試行結果與決定是否接著處理 Ruff。

  v0.8.13 Ruff 接續修正：transport、integration 與本文件 repo 在保留前輪 diff 下開新分支 `coco-codex/ruff-pass`。沿用 owner NUL Git manifest 與 framework `select_files()`，選中 transport 3、integration 20 Python；mocks/interfaces 無 Python。官方 Jazzy Docker 內用固定 Ruff 0.15.7、各自共用 `lint/ruff.toml` 執行安全 `check --fix --no-unsafe-fixes` 與 `format`，未更改規則或 framework。首次在 owner cwd 執行使 transport 的 `launch/` 影響 import 分組，AST guard 偵測後停止；改為現有 gate 的 cwd `/` 重跑，3 個 launch 的 import 順序恢復與修正前一致。

  | Package | 本輪 Python 改檔 | 實際 nested lint 結果 | 本地 log(相對各 package 根目錄) |
  |---|---|---|---|
  | `rv2_control_signal_transport` | 3 | PASS(exit 0)：C/C++ 32、Python 3、Shell 1，0 failed checks | `test_env/jazzy/lint-ruff-fix.gOEQ6z.log` |
  | `r1_test_mocks` | 0 | PASS(exit 0)：C/C++ 16，0 failed checks | `test_env/jazzy/lint-ruff-fix.SELLZt.log` |
  | `r1_integration_tests` | 20 | PASS(exit 0)：C/C++ 4、Python 20，0 failed checks | `test_env/jazzy/lint-ruff-fix.jMcGDE.log` |
  | `r1_interfaces` | 0 | SKIP(exit 0)：無支援來源，不代表 msg/srv、XML 或 CMake 已通過 lint | `test_env/jazzy/lint-ruff-fix.YJRrPN.log` |

  修正前 23 Python 均與 HEAD 相同；Docker 比對修正前後 AST，22 檔完全相同，I04 僅移除已確認未使用的 `import re`。`r1_itest.py` 的 I001 修正為 import 區空行與換行，未改 import 順序；字串值、測試斷言與控制流程均保留。UID/GID/mode 與 93 個非 Python manifest 檔案的內容/metadata 比對通過，前輪 47 個 C/C++ diff 未再變動；證據為 integration 的 `test_env/jazzy/ruff-fix-run.Fp4Mn8.log`。另一 agent 唯讀 diff 複核無 must-fix，`git diff --check` 通過。Doxyfile、CMake、package.xml、.gitmodules、gitlinks 與所有 framework 設定維持原狀；container 均自動卸載，host 未安裝依賴。本輪未重跑 ROS 編譯/功能測試，來源與文件仍為未提交 diff，不 commit/push、升版/tag 或提出 PR。

  v0.8.14 transport lint 修正：前輪完整查核 `test_env/jazzy/full-test.5LpOo6/` 證明 134 個功能案例全過，但舊 flake8/pep257/lint_cmake/uncrustify 使完整 test_run exit 1。transport 與文件 repo 保留既有 diff 開新分支 `coco-codex/transport-lint-gate`；本輪僅新增 flake8 相容 ini、調整 CMake 與三份 launch docstring，不修改 C/C++ 邏輯或測試斷言。獨立複核後採最小保留方案：只排除 uncrustify，以既定 clang-format 取代；flake8/pep257 額外檢查繼續執行。

  本輪證據位於 transport 的 `test_env/jazzy/lint-gate-fix.JvfvRM/`：

  | 驗證 | 結果 | Log / 機器證據 |
  |---|---|---|
  | 新 Docker、deps、乾淨 build | 全 exit 0；3 packages build 33.4s | `01-build-docker.log`、`02-deps.log`、`05-full-build-test.log` |
  | Framework lint | PASS(exit 0)：C/C++ 32、Python 3、Shell 1 | `04-framework-lint.log` |
  | 預設完整 test_run | PASS(exit 0)：15 CTest targets，134 功能案例；flake8/lint_cmake/pep257/xmllint 全過 | `05-full-build-test.log`、`all-proof.json`、`all-results.json` |
  | 獨立 `test_run.sh -k -s unit` | PASS(exit 0)：6 targets、84/84 cases，20.6s | `06-unit.log`、`unit-proof.json` |
  | 獨立 `test_run.sh -k -s integration` | PASS(exit 0)：4 targets、50/50 cases，46.6s | `07-integration.log`、`integration-proof.json` |
  | Config/AST 比對 | PASS：flake8 五項既有設定完全相同、只增加雙引號；launch runtime AST 相同，module doc 只增加 summary 句點 | `03-config-ast-proof.log` |
  | 卸載與保留 | container 已移除；舊產物保存於 `previous/`，原 C/C++ diff 不變 | `08-cleanup.log`、`preserved-cpp-before.diff` / `preserved-cpp-after.diff` |

  與前輪 CTest discovery 比較，僅移除 `uncrustify` target；全部 gtest 案例名稱與 unit/integration labels 相同，分類執行亦核對當次 CTest XML，非空匹配假成功。完整 colcon 彙總為 189 records、0 errors、0 failures、32 skipped，包含 wrappers 與 xUnit，不能視為 189 個功能案例。cppcheck 的 32 SKIP 仍來自既有 2.13.0 效能問題，不宣稱靜態分析通過。分類使用 `-k`，colcon 彙總包含先前未選中測項的 XML，實際分類數量以各 `*-proof.json` 為準。初次臨時 focused helper 未 source ROS setup 而找不到 ament executable；補上環境後三個 focused linters 全 PASS，未以刪除規則處理。完整流程與分類測試皆無失敗或重試。既有 compiler warnings 保留不擴張修復；framework v0.2.1、package.xml 0.1.0、Doxyfile 及 gitlink 不動，未 commit/push、升版/tag 或提出 PR。

**驗證**
- 語意查核:逐條對照 §11.5.3 腳本職責表(distro 解析、container 重建、`~/ros2_ws` 結構、唯讀掛載、rosdep `--ignore-src`、結束碼語意、`.deb` 命名)與 §11.5.2 環境策略表；確認 `test_depends.repos` 為宣告式輸入而非流程客製(§11.5.4)。✅ 分區複核確認搬移未遺失案例，Handle斷言保留、跨binary前綴隔離、labels與文件引用一致；框架的空測試成功漏洞經回歸修正。
- 實際測試:`./r1_test_framework/todo_check.sh t0`(container:`r1_todo_t0_jazzy`)。✅ 新布局 T0 PASS(21 gtests/彙總23)，另依 T0.6 執行全部受影響測試；本輪使用 `-k` 保留供分類及介面檢查，完成後均以 nested `test_clean.sh` 卸載，clone 驗證容器亦已卸載。
- v0.8.3 定版補驗：官方 Jazzy Docker 內驗證四個 package 的 XML 版本 `0.1.0`、transport Doxyfile 版本、四個 nested framework 的 VERSION 與不同 CWD 解析、全部框架腳本語法及路徑解析 unit regression；全數通過且驗證容器自動移除。與 v0.8.1 的 framework `f436059` 比對，版本 tag 只多 README/VERSION；各 package 僅變更 gitlink 與版本資料，因此沿用上述功能測試證據，本次未重跑完整功能測試。

---

## T1 介面定義(§2.1、§2.5.1、§2.5.2、§3.1)

**目標**:建立全部 msg/srv 介面,供後續各章編譯。
**依賴**:T0;前置裁決 §12 #1——**已裁決(v0.2.0):新開獨立 `r1_interfaces` package**(`ros2_ws/src/r1_interfaces/`)。rosidl 型別名僅取檔案 basename(子目錄不入 namespace),`ControlSignalInfo` / `ControlSignalInfoReq` / `ControlSignalJoy` / `ControlSignalTwist` 與 `rv2_interfaces` legacy 型別同名衝突,§2.1「暫置 `rv2_interfaces/msg/r1/`」原文不可行;獨立 package 亦免除日後 migrate 搬移。

- [x] **T1.1** `msg/ControlSignalInfo.msg`:8 欄位依 §3.1。
  查核:欄位名稱、型別、順序與 §3.1 表逐欄一致;`ros2 interface show` 輸出正確。✅ 逐欄查核通過;另含 MODE_*(§3.1 要求)與 TYPE_* 常數(加值,§7 型別鍵)。
- [x] **T1.2** `msg/EntryStatus.msg` 與 `msg/ManagerStatus.msg`:依 §2.5.1(EntryStatus 含 manager identity 欄位;ManagerStatus 含 instance / sequence 與完整 entry snapshot)。
  查核:欄位與 §2.5.1 定義逐欄一致;master 對帳所需之 identity(§9.3)欄位齊備。✅ 含 v1.2.1 之 `source_csm_instance_id`;phase / state 常數依 §2.5.1 編號。
- [x] **T1.3** `srv/ControlSignalManage.srv`(op = REGISTER | UNREGISTER)與 `srv/ControlSignalInfoReq.srv`:依 §2.5.2,含 identity 三元組與 typed error(RETRYABLE_CONFLICT、STALE 等)。
  查核:欄位與 §2.5.2 一致;回覆碼列舉涵蓋 §8.3 引用的全部結果類別。✅ 七類回覆碼齊備。
- [x] **T1.4** `srv/CsmRegister.srv`、`srv/CsmHeartbeat.srv`、`srv/CsmNotify.srv`:依 §2.5.2 與 §9.2(CsmRegister 攜帶 CSM 雙閾值、status interval、registration grace;CsmHeartbeat request 攜帶 `csm_name`;CsmNotify 含 kind、event ID、identity、ACK 語意)。
  查核:欄位與 §2.5.2 / §9.2 一致;四種 kind 與 ALREADY_APPLIED / STALE 回覆可表達。✅ kind 編號依 §2.5.2(0–3);heartbeat 非匿名 Trigger。
- [x] **T1.5** 資料通道 srv:`srv/ControlSignalJoy.srv`、`srv/ControlSignalTwist.srv`;String 型別之 service 模式配套依 §7 型別註冊需求確認,若需要則補齊並回饋 §2.1 清單。
  查核:與 §7 註冊型別集合(Joy / Twist / String)對齊,service 模式可用型別無缺漏。✅ §7.2:string 為 topic-only(SrvT = void),無需 ControlSignalString.srv;回覆常數名取 §6.3 字面 `SRV_RES_*`。
- [x] **T1.6** `r1_interfaces` 之 rosidl 產生設定(CMakeLists / package.xml)納入上述檔案。
  查核:`r1_interfaces` 於 docker 內 build 通過。✅ `./r1_test_framework/todo_check.sh t1` PASS;10/10 介面 `ros2 interface show` 解析正確。

**驗證**
- 語意查核:製作「msg/srv 欄位 ↔ § 條文」對照表逐欄打勾;重點確認三處易錯點——CsmHeartbeat 非匿名 Trigger(v1.0.0 修正)、ManagerStatus 含 PENDING 交易(§2.4)、EntryStatus 可在單側 snapshot 定位預期配對(CM10)。✅ 逐檔對抗式查核完成(0 must-fix),三處易錯點逐一確認。
- 實際測試:`./r1_test_framework/todo_check.sh t1`(container:`r1_todo_t1_jazzy`;build 驗證,無 gtest)。✅ PASS。

---

## T2 `r1::LivenessState`(§4)

**目標**:純邏輯活性核心:記錄、純計算、被動狀態寫入、terminal seal。無 ROS 依賴,可完整單元測試。
**依賴**:T0(不依賴 T1,純 C++)。

- [x] **T2.1** `liveness_state.h` 骨架:4 態 enum(INITIAL / ACTIVE / TIMEOUT / DISCONNECTED)、雙閾值建構參數(`timeout_ns`、`disconnect_timeout_ns`,0 = 停用,§2.3.1 變體 A–D)。
  查核:單獨 TU 編譯通過且不含任何 rclcpp include；變體 A–D 之閾值組合皆可建構。✅ host `g++ -std=c++17` 單獨 TU 編譯通過,`grep rclcpp` = 0;L11–L13 覆蓋四變體(閾值依 §4.3 為 `calcState` 逐呼叫參數,建構子僅取 `nowNs`)。
- [x] **T2.2** `recordActivity()`:hot path 原子記錄——timestamp 單調不倒退、activity generation 遞增、seal 後拒絕並回傳 false(§4.3、§4.4)。
  查核:對照 §4.3 簽名與回傳型別；L14 之多 writer 亂序語意可滿足。✅ CAS-max timestamp 先於 generation 以 release 發布;L14 以 8 執行緒 × 2000 筆亂序驗證。
- [x] **T2.3** `calcState()` 純計算:依記錄與雙閾值回傳應處狀態,過程不改動任何欄位；嚴格大於判定；「從未活動」規則(停留 INITIAL,僅越過 disconnect 閾值才 DISCONNECTED,L6/L7)；單次跨越兩閾值直接 DISCONNECTED(L5)。
  查核:連續呼叫結果一致(純函數性,L10)；四變體判定表與 §2.3.1 圖一致。✅ const 純函數,現行狀態不參與計算;語意查核逐 cell 枚舉通過。
- [x] **T2.4** `applyState()`:唯一狀態寫入路徑(CSM tick 專用),回傳舊狀態(§4.2 單寫者模型)。
  查核:state 欄位無 CAS(D8:結構上不需要)；與 §4.3 簽名一致。✅ 無條件 exchange 回舊值,無 CAS(L9)。
- [x] **T2.5** Terminal seal:activity-generation CAS——計算期間有新活動則 seal 失敗；seal 勝出後 `recordActivity()` 拒絕(§4.2、L15–L17)。
  查核:seal 只保護活動接受與 terminal linearization,不寫 state(§4 開頭定義)。✅ `trySealActivity(g)` 單發 CAS、失敗零改動(L16);`sealActivity()` 冪等(L17)。
- [x] **T2.6** `test/unit/test_liveness_state.cpp`:L1–L18 全數實作,含假時鐘注入(以參數傳入 now,不依賴系統時鐘)。
  查核:18 案例與 §4.5 表逐列對應,無合併、無跳過。✅ 18/18 PASS;純假時鐘,無系統時鐘、無 rclcpp。

**驗證**
- 語意查核:L 表逐列檢查 assert 內容——特別是 L8(邊界不觸發)、L14(generation = 成功記錄數)、L16(seal 失敗後下一 tick 回 ACTIVE)、L18(INITIAL 直接 apply TIMEOUT 之例外)是否忠實轉譯 §4.4/§4.5 敘述。✅ 4-agent 對抗式查核(介面、memory order、判定表、L 表逐列)0 must-fix;5 nits(註解措辭)已修。
- 實際測試:`./r1_test_framework/todo_check.sh t2`(container:`r1_todo_t2_jazzy`)；L14 另納入 T12 TSan job。✅ PASS(host TSan 已先行全綠)。

---

## T3 Info 與驗證(§3)

**目標**:`r1::ControlSignalInfo` 別名與 `validateControlSignalInfo()` 六條規則。
**依賴**:T1(msg 型別)。

- [x] **T3.1** `control_signal_info.h`:Info 別名、mode / type 字串常數、驗證結果型別(錯誤訊息含欄位名)。
  查核:除 msg 標頭外無 ROS 依賴；錯誤訊息可定位到具體欄位。✅ 別名指向 `r1_interfaces`(§12 #1);錯誤訊息逐欄具名;除 msg 標頭外零 ROS 依賴。
- [x] **T3.2** `validateControlSignalInfo()`:六條規則依 §3.2,含 priority 0–100 之外拒絕、`timeout_ns = 0` 於 service 模式 invalid、`disconnect_timeout_ns` 須嚴格大於 `timeout_ns` 或為 0、規則 6(`target_manager_name` 於 registerSource 路徑必填)。
  查核:規則逐條與 §3.2 對照；`ManagerOptions` 之 CSM 閾值不混入本驗證(§3.2 末段)。✅ 六規則逐條實作;CSM 閾值驗證未混入。
- [x] **T3.3** `test/unit/test_info_validation.cpp`:V1–V11 全數實作(V5 含 4 子案例)。
  查核:11 案例與 §3.3 表逐列對應。✅ 11 案例(V5 含 4 子案例);docker t3 PASS。

**驗證**
- 語意查核:V 表逐列對照 §3.2 規則來源；確認 V7 的雙面性(topic valid、service invalid)與 V10(變體 C 合法)未被寫成單面 assert。✅ 對抗式查核通過;V7 雙面、V10 變體 C 皆為雙向斷言。
- 實際測試:`./r1_test_framework/todo_check.sh t3`(container:`r1_todo_t3_jazzy`)。✅ PASS。

---

## T4 `r1::ControlSignalSource`(§5)

**目標**:Source 模板:topic publisher 與 service client 雙模式、send 即活動、ResponseHealth、rate 記錄。
**依賴**:T2、T3。

- [x] **T4.1** `BaseControlSignalSource` 介面:`msgType()`、`sendErased()`、`getState()` / `getStatus()`、`sendRateHz()`、per-state callback slot 註冊(§5.2)。
  查核:介面與 §5.2 宣告一致；`getStatus()` 回 {state, rate} 整合查詢。✅ Base 依 §5.2 程式塊;`getStatus()` 回 {state, rate}。
- [x] **T4.2** `ControlSignalSource<msgT, srvT>` topic 模式:publisher 建立、`send()` 即記錄活動(v1.1.0 自驅語意)。
  查核:send 路徑僅記錄,不寫 state(D8)；shutdown 後回 `NO_TRANSPORT`。✅ send 即記錄,不寫 state;shutdown 後 `NO_TRANSPORT`。
- [x] **T4.3** Service 模式 `send()`:單調 `requestSequence`、`service_is_ready()` 檢查、`async_send_request` + `timeout_ns` 等待(無隱藏 fallback)、逾時呼叫 `remove_pending_request()`、ResponseHealth failure streak / `failureEpoch` 轉換語意、亂序 outcome 只採較新者(§5.3)。
  查核:§5.3 send(service) 段逐句對照——response 到達(含 REJECTED)先清 streak 再 `recordActivity()`；seal 勝出時回 `DISCONNECTED`；`failureEpoch` 僅於 healthy↔failure 轉換遞增。✅ §5.3 逐句:單調 seq、無隱藏 fallback、`remove_pending_request`、response 先清 streak 再 recordActivity、seal 勝出回 DISCONNECTED、epoch 僅轉換時遞增、亂序防護(S14)。`INVALID_CONTEXT` 宣告保留、偵測待 T7。
- [x] **T4.4** `RateRecorder`:N-bucket 環形 rolling window,窗長由 `ManagerOptions.rateWindowNs` 配置(§5.2)。
  查核:視窗行為與 S10/S13 預期一致(停止 1 窗後歸 0)。✅ 8-bucket 環形、單 atomic 打包 {bucketNum,count};calcHz 依實際覆蓋時距正規化;窗長建構參數(ManagerOptions 待 T7)。
- [x] **T4.5** Shutdown 與 RAII:冪等 shutdown、解構釋放 transport entities(§1.5)。
  查核:S6 語意；shutdown 後無殭屍活動(§0.1 定義)。✅ 冪等 shutdown、解構呼叫 shutdown(S6)。
- [x] **T4.6** 測試通道:`_calcStatus()` / `_applyStatus()` 經 `ManagerTestAccess` friend 暴露(§5.2、§8.2)。
  查核:測試不必啟動真 Manager tick 即可驅動狀態轉移。✅ `ManagerTestAccess` 於 `test/r1_test_utils.h`,僅編入測試 target。
- [x] **T4.7** `test/unit/test_transport.cpp` Source 部分:S1–S16(gtest suite 以 `SourceTest` 命名,與 Sink 區分)。
  查核:16 案例與 §5.4 表逐列對應；S5 涵蓋 NO_TRANSPORT 與 TIMEOUT 兩分支。✅ 16 案例 suite `SourceTest`;S5 三分支(NO_TRANSPORT / TIMEOUT / 遮蔽)全覆蓋。

**驗證**
- 語意查核:S 表逐列對照 §5.3/§5.4——重點 S5(failure streak 不被高頻 send 掩蓋)、S14(epoch 亂序防護)、S15/S16(seal 與活動、與 response-failure 的兩類競合)是否逐字忠實。✅ 5-agent 查核;S5 / S16 測試強度 must-fix 已修(遮蔽斷言以假時鐘置於 cadence-ACTIVE 窗、S16a 補 send 交錯、S16c 改測 in-flight response 路徑)。
- 實際測試:`./r1_test_framework/todo_check.sh t4`(container:`r1_todo_t4_jazzy`)；S11 併入 T12 TSan。✅ PASS;S11 併入 T12 TSan。

---

## T5 `r1::ControlSignalSink`(§6)

**目標**:Sink 模板:subscription 與 service server 雙模式、收訊記錄、read / callback / waitForMessage。
**依賴**:T2、T3。

- [x] **T5.1** `BaseControlSignalSink` + `ControlSignalSink<msgT, srvT>`:subscription / service server 建立、收訊即記錄(§6.2)。
  查核:介面與 §6.2 宣告一致；service 模式 round-trip 回 SUCCESS(K7)。✅ 雙模式;service round-trip 回 SRV_RES_SUCCESS(K7)。
- [x] **T5.2** `read()` 與訊息 callback:read 之狀態粒度語意(tick 前 read false,K2)、callback replace 語意、無鎖呼叫 callback(K6 之死鎖回歸)。
  查核:§6.3 行為細節逐句對照。✅ read 之 tick 粒度(K2);callback replace 語意、無鎖呼叫(K6)。
- [x] **T5.3** `waitForMessage()`:僅等「呼叫後」新訊息、逾時版 ≈ timeoutNs 返回 false、shutdown 中斷等待且無 UAF(K13–K15)。
  查核:喚醒語意與 §6.3 一致；並發多等待者全部喚醒。✅ 序號 pred、shutdown 持 msgMtx_ 置旗(v1.2.1)、解構 drain waiters_(K15 實測 destroy-while-waiting)。
- [x] **T5.4** 收訊 rate 記錄:rolling window 同 T4.4。
  查核:K11 預期(∈ [18, 22] @ 20 Hz)。✅ 同 T4.4;K11 ∈ [18,22]。
- [x] **T5.5** Terminal seal 與收訊交錯:seal 勝出後不存訊息、不喚醒、不呼叫 callback；活動先勝出則取消本輪 terminal(K8/K16)。
  查核:與 §4.2 seal 語意及 §8.3 同 tick 註銷順序一致。✅ K8 / K16 兩交錯皆斷言(不存訊息、不喚醒、不呼叫 callback)。
- [x] **T5.6** `test/unit/test_transport.cpp` Sink 部分:K1–K16(suite `SinkTest`)。
  查核:16 案例與 §6.4 表逐列對應。✅ 16 案例 suite `SinkTest`;docker t5 PASS。

**驗證**
- 語意查核:K 表逐列對照——重點 K2(粒度語意非 bug 而是設計)、K8(seal 成功才 apply + 註銷)、K14(舊訊息不觸發)是否忠實。✅ K2 粒度、K8 seal 順序、K14 舊訊息不觸發皆忠實;K13/K14 補喚醒延遲上界。
- 實際測試:`./r1_test_framework/todo_check.sh t5`(container:`r1_todo_t5_jazzy`)；K10 併入 T12 ASan、K12/K16 併入 TSan。✅ PASS;K10 併入 T12 ASan、K12/K16 併入 TSan。

---

## T6 Factory 與型別註冊(§7)

**目標**:singleton registry、`R1_REGISTER_CONTROL_SIGNAL`、Joy / Twist / String 具體型別。
**依賴**:T4、T5(Create 需 Source / Sink 模板)。

- [x] **T6.1** `control_signal_factory.h`:registry、`Register()`(重複註冊回 false)、`CreateSource()` / `CreateSink()`(未註冊型別回 nullptr + errOut 字串,不拋例外)(§7.2)。
  查核:與 §7.2 介面一致；errOut 參數存在(v1.0.0 補完項)。✅ 與 §7.2 一致;errOut 存在;加值 `serviceCapable()` 與 rateWindowNs 參數(ManagerOptions 相依)。
- [x] **T6.2** `R1_REGISTER_CONTROL_SIGNAL` macro 與 typeKey 反查(joy / twist / string)。
  查核:F3 之反查語意；macro 於 header 使用不產生 ODR 問題。✅ macro 以匿名 namespace TU-local static 註冊,header 使用無 ODR 問題;typeKey 反查(F3)。
- [x] **T6.3** `src/r1/control_signal_factory.cpp` + `control_signal_types.cpp`:singleton 單一定義於 shared library、三型別註冊(topic 與 service 模式配套)。
  查核:F5(跨 TU 可見)之結構前提成立；service 模式配套 srv 與 T1.5 對齊。✅ singleton 定義於 shared library `r1_control_signal_transport`;三型別註冊,string topic-only(SrvT=void)。
- [x] **T6.4** `test/unit/test_factory.cpp`:F1–F5。
  查核:5 案例與 §7.3 表逐列對應。✅ 5 案例;F2 同斷 nullptr 與不拋例外。

**驗證**
- 語意查核:F 表對照 §7.3；確認 F2 同時斷言「回 nullptr」與「不拋例外」兩件事。✅ 對抗式查核通過。
- 實際測試:`./r1_test_framework/todo_check.sh t6`(container:`r1_todo_t6_jazzy`)。✅ PASS。

---

## T7 `r1::ControlSignalManager`(§8)

**目標**:CSM 本體。全案最大的大項,小項依 §8.2 類別架構與 §8.3 行為細節拆分,建議按序實作並隨做隨測。
**依賴**:T1–T6；T7.7 需前置裁決 §12 #6(retry 參數)。

- [x] **T7.1** `source_registration.h`:identity 三元組(`csm_instance_id`、`registration_id`、`attempt_generation`)、registration lifecycle(PENDING / REGISTERED / RETRY_WAIT / REMOVING / ABSENT,§1.3.1)、`SourceRegistrationSlot`(stable slot、`desired` 旗標、slot mutex)。
  查核:namespace-scope 型別定義與 §8.2 一致；lifecycle 與 §1.3.1 三層狀態模型第二層對應。✅ namespace-scope 定義(§8.2/v1.2.1 循環相依考量);lifecycle 對應 §1.3.1 第二層(ABSENT = map 移除)。
- [x] **T7.2** `ManagerOptions` + `RetryPolicy`:含 `statusIntervalMs`、`rateWindowNs`、`maxRegisterTimeoutMs`、CSM 級雙閾值、master 名稱；自身驗證規則(§8.2,不混入 Info 六規則)。
  查核:欄位與 §8.2 宣告一致；非法組態於建構期拒絕。✅ 欄位與 §8.2 一致;`validate()` 建構期拒絕非法組態(含 v1.2.1 heartbeat deadline 規則);D7 提案入 `Recommended()`。
- [x] **T7.3** 本地註冊表:雙鍵(controller_name + channel_name)查重、一律 `emplace` 禁用 `operator[]`(§1.3 對策)、PENDING 佔位原子插入(§2.4)。
  查核:M2 語意(本地重複不發遠端呼叫)；TOCTOU 結構性消除(§1.3 表第一列)。✅ 雙鍵查重、emplace、PENDING 原子佔位(M2/M4 16 執行緒實測)。
- [x] **T7.4** `registerSource()` 兩階段 + rollback + `unregisterSource()`:§8.3 registerSource 段逐句實作——PENDING 佔位、放鎖後同步 REGISTER、成功後 slot lock 下驗證 desired / phase / identity 才轉正、RETRYABLE 轉 RETRY_WAIT 回 `RETRY_SCHEDULED`、永久錯誤移除 slot；unregister 對三種狀態的語意(M7)。
  查核:`timeoutMs` 區間檢查與 registration grace 宣告公式(§8.3)；callback 內呼叫觸發 precondition error(M14)。✅ 兩階段 + slot lock 轉正 + rollback UNREGISTER(含 abort 路徑);D3 conflict 強制 RETRY_WAIT(§2.4);M14 precondition。
- [x] **T7.5** `_onManage()`(REGISTER / UNREGISTER):驗證 → 查重 + 冪等判定 → PENDING emplace → 放鎖建 Sink → unique lock 轉正；PENDING TTL 回收；stale / matching UNREGISTER 處理(§8.3)。
  查核:與正常完成路徑以同一把 unique lock 競爭(§8.3)；M23 stale 語意。✅ 流程逐句;PENDING TTL 與完成路徑同鎖競爭;stale → STALE、清理路徑重驗 identity。
- [x] **T7.6** Status tick 五階段(§8.3,D8 單寫者):snapshot / calculate(鎖外 `_calcStatus`)→ validate / commit non-terminal → terminal seal + 同 tick 註銷 → status 發布 + heartbeat → retry / maintenance。`tickRunning_` 重入防護。
  查核:五階段順序與 §8.3 條列一致；DISCONNECTED 在 seal 前不污染 table；所有 callback / shutdown / ROS 呼叫在 map lock 外；M19(單 tick 跨兩閾值)與 M9(同 tick 完成移除 + Handle 失效 + notification callback)語意成立。✅ 五階段依序;DISCONNECTED seal 前不入 table;callback/shutdown/ROS 呼叫皆鎖外;M19/M9 語意成立;`tickRunning_` 重入防護。
- [x] **T7.7** Retry 佇列:completion queue、bounded `maxInFlight`、exponential backoff + jitter、per-intent 去重、成功 response 只在 desired && identity 相符時替換 endpoint、已成功過的 intent 不設次數上限、`maxInitialAttempts` 僅限 optional initial retry(§8.3 第 5 階段、D2–D4/D7)。
  查核:M24 全部子句；延遲成功不復活已取消 intent(M7)。✅ completion queue、bounded maxInFlight、backoff+jitter、registrationId 去重、desired+identity 才替換、成功後無次數上限、initial cap 僅限 INITIAL_UNREACHABLE(cap 耗盡發 RETRY_FAILED 移除 slot,無殭屍);quarantine 於 enqueue 生效 + SUSPECTED_DATA_PATH_FAULT。
- [x] **T7.8** Master client:`CsmRegister`(宣告雙閾值 + grace)、`CsmHeartbeat` 單筆 in-flight、無回應進 degraded、回線後 UNKNOWN_CSM 觸發 re-register(§2.5、§9.2、M17)。
  查核:heartbeat 舊 completion 不清除新 attempt(M17)；degraded 期間 entity 狀態零影響(§12 結案紀錄)。✅ CsmRegister 攜雙閾值+grace;heartbeat 單筆 in-flight + deadline 釋放 + 世代防護;無回應僅 degraded;UNKNOWN_CSM → re-register(M17 實測含 degraded 進出)。
- [x] **T7.9** `get_notifications` server:四 kind 處理——STATE 僅事件、CSM_TIMEOUT / ACTIVE 只改 peerHealth、DISCONNECTED / PAIR_MISSING 對 matching identity 排一次 removal 由下一 tick 執行；重送回 ALREADY_APPLIED、舊世代回 STALE(§8.2 通知接收、M8)。
  查核:非 tick 來源的狀態變更一律先轉 table 註記(§2.6 單寫者)。✅ 四 kind 處理;peer-health 世代驗證、無匹配回 STALE;removal 一律 table 註記由 tick 執行;event FIFO 冪等快取。
- [x] **T7.10** `ManagerStatus` 發布與 `InfoReq`:完整 snapshot 含 PENDING / RETRY_WAIT phase、endpoint_present、identity、rate(取自 lastStatus table)；InfoReq 僅列已註冊 endpoints(M13/M16)。
  查核:snapshot 欄位足以支撐 master 對帳(§9.3 之資料來源)。✅ 完整 snapshot 含 PENDING/RETRY_WAIT、endpoint_present、identity、rate;InfoReq 僅列已註冊(M13/M16)。
- [x] **T7.11** Callbacks:`registerCallback`(template 與字串版、兩種註冊順序)、per-state callback(`registerSourceStateCallback` / `registerSinkStateCallback`,一律 tick 執行緒觸發)(M12/M18)。
  查核:覆蓋與 nullptr 清除語意；state callback 內 re-enter read API 不死鎖(M21)。✅ template/字串版、兩種順序、覆蓋與 nullptr(M12/M18);state callback 一律 tick 執行緒。
- [x] **T7.12** 黑白名單:雙向套用、enable / disable、空白名單 = 全擋(M11,承襲 rv2 案例組)。
  查核:register 與 _onManage 兩側都過濾(§8.3)。✅ 雙向套用、空白名單全擋(M11)。
- [x] **T7.13** 執行緒模型:tick 於 MutuallyExclusive `tickGroup_`；manage / info_req / get_notifications servers 與 master clients、retry response callback 於 Manager 自建 Reentrant group(§2.6)。
  查核:與使用者 node 預設 group 隔離；同步 registerSource 於 callback 內呼叫之防護(M14)。✅ tick 於 MutuallyExclusive、management 於 Reentrant;tick 執行緒亦設 callback guard(M14 in-callback);解構 fence 防 in-flight callback UAF。
- [x] **T7.14** `test/integration/test_manager.cpp` + `r1_test_utils.h`:M1–M26 全數實作(短週期參數壓縮時間,§8.4；mock master 以裸 service 實作)。
  查核:26 案例與 §8.4 表逐列對應；M4 以 16 執行緒實測。✅ 26 案例;mock master 裸 service;M4 16 執行緒跨 4 targets。

**驗證**
- 語意查核:M 表逐列對照 §8.3/§8.4,重點四處——M6(response 丟失之三層回收)、M8(四 kind 的「只做什麼、不做什麼」)、M20(D3 retry-until-success 含 disconnect=0 不承諾收斂)、M22(activity 與 seal 競合唯一結果)；另確認每個 public function 皆有測試覆蓋(§11.3 要求)。✅ 5-agent 查核 43 項發現、25 must-fix 全修並複核;M6 三層回收之整合部分留 I8。
- 實際測試:`./r1_test_framework/todo_check.sh t7`(container:`r1_todo_t7_jazzy`,涵蓋 test_manager 與 test_transport)；M4 併入 TSan、M10 併入 ASan。✅ PASS;M4 併 TSan、M10 併 ASan。

---

## T8 Handles(§10)

**目標**:`SourceHandle` / `SinkHandle`:使用者側穩定引用,slot weak 綁定。
**依賴**:T7。

- [x] **T8.1** `SourceHandle`:綁定 `SourceRegistrationSlot`、`valid()` / `ready()` / `state()`(optional)、`send()` 轉發、endpoint 缺席回 `RETRYING`(§10.2/§10.3)。
  查核:retry 期間 valid 恆真、ready 隨 endpoint 起伏(H7)；型別不符依 build 型態回錯誤碼或 assert(H3)。✅ weak slot 綁定、RETRYING 語意(H7);型別不符 debug assert / release NO_TRANSPORT(H3 雙模式)。
- [x] **T8.2** `SinkHandle`:`read()` / `state()` / `waitForMessage()` 轉發。
  查核:與 §10.2 介面一致。✅ read/state/waitForMessage 轉發(H2);erased wait 經 Base 虛擬。
- [x] **T8.3** 失效語意與拷貝:erase / unregister 後全操作失效、拷貝共享失效狀態、in-flight response 不復活已銷毀 slot(H4/H5/H8)。
  查核:§10.3 slot 生命週期逐句對照。✅ H4/H5/H8;in-flight response 不復活以延遲 service 實測。
- [x] **T8.4** `test/unit/test_handles.cpp`(H1–H6) 與 `test/integration/test_handles_lifecycle.cpp`(H7–H8)。
  查核:8 案例與 §10.4 表逐列對應。✅ 8 案例;H6 併 T12 ASan/TSan。

**驗證**
- 語意查核:H 表對照 §10.3/§10.4；重點 H7 的三段式(true→false→true)與「同一 Handle 換 endpoint 不換 Handle」承諾。✅ 對抗式查核;H7 三段式與「同 Handle 換 endpoint」逐項斷言。
- 實際測試:`./r1_test_framework/todo_check.sh t8`(container:`r1_todo_t8_jazzy`)；H6 併入 T12 ASan/TSan。✅ PASS;H6 併入 T12 ASan/TSan。

---

## T9 `r1::CsmMaster` 與 `csm_master_node`(§9)

**目標**:集中式通知架構:CSM 註冊 / heartbeat、status 訂閱、配對、雙閾值 polling、level reconciliation、可靠通知。
**依賴**:T1(srv)、T7(協定對手方；master 單元測試用 mock CSM 裸 node,可與 T7 平行開發)。

- [x] **T9.1** `csm_master.h` 骨架:`MasterOptions`、CSM record(instance、雙閾值、interval、grace)、retired instance set(§9.2)。
  查核:與 §9.2 宣告一致；record 欄位覆蓋 CM1 斷言。✅ MasterOptions、CsmRecord(instance、雙閾值、interval、grace)、retired set(CM1)。
- [x] **T9.2** `csm_register` / `csm_heartbeat` servers:instance 取代 → 舊 ID 進 retired set、retired 之 heartbeat / 遲到 register 回 STALE；黑白名單(CM1/CM2)。
  查核:同名新 instance 之 STALE_INSTANCE 全重建路徑(§9.3,v1.2.1 修正項)。✅ 取代 → retired、STALE 語意、黑白名單(CM1/CM2);same-instance DISCONNECTED re-register = 全量重建且保留 seq fence(v1.2.1)。
- [x] **T9.3** Status 訂閱管理:per-CSM 訂閱 `<name>/status`、instance / sequence 驗證、完整 snapshot 原子替換、omission 語意(seq N+1 缺項即移除)、重複 / 逆序 / 舊 instance 拒絕(CM10)。
  查核:§9.2 表 status subscriber 列逐句對照。✅ instance/seq 驗證、整份原子替換、omission、重複/逆序/舊 instance 拒絕(CM10);DISCONNECTED record 之 status 一律丟棄。
- [x] **T9.4** 配對與 STATE 通知:以 controller 配對 Source–Sink、變化偵測、one-shot(同狀態不重發,恢復後再發)、STATE best-effort(CM3/CM4)。
  查核:STATE 不改變 peer local state(§2.5)。✅ identity 配對、edge 偵測、one-shot、tombstone 合成(CM3/CM4/CM10)。
- [x] **T9.5** CSM 級雙閾值 polling:heartbeat 停止 > csm_timeout 發 peerHealth TIMEOUT、> csm_disconnect 發 lifecycle DISCONNECTED + tombstone、僅新 instance register 可恢復(D6,CM5/CM6)。
  查核:polling 於 master tick,判定與通知非阻塞(CM9)。✅ 獨立 HeartbeatTracker、嚴格大於、disconnect 優先(CM5/CM6/CM13);判定與通知非阻塞(CM9)。
- [x] **T9.6** Level reconciliation:ready snapshot gate、registration grace(PENDING 期間暫停 missing grace,CM11)、PAIR_MISSING 判定與重送至 ACK、缺席 CSM 之 per-name absence clock(v1.2.1,§9.3)。
  查核:§9.3 reconciliation 段逐句對照；master 重啟首輪不產生 STATE storm(CM7)。✅ ready gate、PENDING 抑制、per-name absence clock、DISCONNECTED peer 不關閉 gate、PAIR_MISSING level + delivered-awaiting-observation(CM7/CM8/CM11)。
- [x] **T9.7** 通知發送器:`get_notifications` client per CSM、STATE async best-effort、control event 帶 event ID 非阻塞重送至 ACK、duplicate 回 ALREADY_APPLIED / 舊世代回 STALE(CM9/CM12)。
  查核:重送不阻塞 master tick 與 heartbeat polling。✅ per-CSM notify client、STATE best-effort、control event 非阻塞重送至 ACK、per-owner 取代、in-flight deadline(CM9/CM12)。
- [x] **T9.8** `csm_master_node` 執行檔(`src/r1/csm_master.cpp`):參數載入 `MasterOptions`,host `CsmMaster`。
  查核:`ros2 run` 可啟動；參數與 §9.2 對齊。✅ csm_master_node 參數載入 MasterOptions,`ros2 run` 可啟動。
- [x] **T9.9** `test/integration/test_csm_master.cpp`:CM1–CM13,mock CSM 以裸 node 實作(status publisher + get_notifications server + heartbeat / register clients,§9.4)。
  查核:13 案例與 §9.4 表逐列對應,不依賴真 ControlSignalManager。✅ 13 案例,mock CSM 裸 node,不依賴真 Manager。

**驗證**
- 語意查核:CM 表逐列對照 §9.2/§9.3；重點 CM7(ready gate)、CM8(快速重啟 + 空 snapshot)、CM13(disconnect=0 不承諾收斂)三個曾在審核修正的行為。✅ 4-agent 查核 14 must-fix 全修並複核;CM7 ready gate、CM8 空 snapshot、CM13 不承諾收斂逐一確認。
- 實際測試:`./r1_test_framework/todo_check.sh t9`(container:`r1_todo_t9_jazzy`)。✅ PASS。

---

## T10 `r1_test_mocks` package(§11.1)

**目標**:整合測試所需的可腳本化故障注入 nodes。獨立 package,置於 workspace(`ros2_ws/src/r1_test_mocks/`)。
**依賴**:T1(介面)；與 T7–T9 平行開發可行。

- [x] **T10.1** Package 骨架:ament_cmake、`test_depends.repos` 宣告(`r1_interfaces`)、package 內嵌 `r1_test_framework` submodule。
  查核:`./r1_test_framework/todo_check.sh t10` 可 build；框架未經客製即可運作。✅ 既有 local dependency 掛載與五個 executables 已於原框架流程 build 成功；v0.8.0 新布局重驗列 T0.2/T0.5/T0.6。
- [x] **T10.2** `MockManagerNode`:`control_signal_manage` service 之可腳本化行為——接受、拒絕(指定 reason)、延遲 N ms、**不回覆**、回覆後立刻斷線。
  查核:五種行為逐一可由參數 / service 切換觸發(smoke test)。✅ 五種行為全覆蓋；reject code/reason 與不落 state、delay 先套用、service 真斷線/恢復均有斷言；no-reply REGISTER 先接受後抑制 response。
- [x] **T10.3** `MockSourceNode` / `MockSinkNode`:裸 rclcpp pub / sub / client / server,可設定頻率、突發停止、亂序型別。
  查核:三種擾動逐一可觸發；頻率誤差 < 10%。✅ Joy/Twist/String topic、Joy/Twist service、pause/resume、錯型別隔離均覆蓋；以三秒實際 elapsed 嚴格斷言相對誤差 `< 10%`。
- [x] **T10.4** `MockMasterNode`:register 拒絕、heartbeat 不回應、注入四種 CsmNotify kind、重送 / 亂序 / 舊 generation、攔截 ACK。
  查核:腳本項逐一可觸發；可回放固定序列供 I12/I16 使用。✅ heartbeat future 真 timeout；四種 kind、stable event resend、非單調 generation、舊 instance 與飽和舊世代均覆蓋；具名 immutable sequence 以前一筆 ACK 串接下一筆,並記錄 ACK code。
- [x] **T10.5** `StatusFaultNode`:以代理方式暫停 / 恢復 / 降頻某 CSM 的 status 發布。
  查核:三種操作逐一可觸發且可觀察(`ros2 topic hz`)。✅ pass/pause/resume/throttle 逐項驗證,forwarded/dropped 計數可觀察且跨執行緒安全。
- [x] **T10.6** 各 mock 之 smoke tests(gtest 或 launch_testing)。
  查核:`./r1_test_framework/todo_check.sh t10` 全綠。✅ 4 個 gtest targets、23 個 cases 全綠。

**驗證**
- 語意查核:mock 能力清單逐項對照 §11.1 表；確認 M5/M6 之整合版(I8)所需行為(接受但不回覆)確實可腳本化。✅ 多輪對抗式查核之 must-fix 全修,3-agent 最終複核 0 must-fix；ASan 定位並修復短生命週期 probe callback UAF,100 次 targeted regression 全綠。
- 實際測試:`cd ~/Workspace/ros2_ws/src/r1_test_mocks && ./r1_test_framework/todo_check.sh t10`(container:`r1_todo_t10_jazzy`)。✅ PASS:23 個 gtests / 4 個 CTest targets,彙總 27 tests、0 error/failure/skip；container 自動卸載。

---

## T11 `r1_integration_tests` package(§11.2)

**目標**:launch_testing 場景集 I1–I18,含 `csm_master_node` in loop。獨立 package(`ros2_ws/src/r1_integration_tests/`)。
**依賴**:T8、T9、T10。

- [x] **T11.1** Package 骨架與工具:launch_testing 基架、狀態收斂等待 helper、`ros2 topic` / `service` 探測工具、每場景獨立 `ROS_DOMAIN_ID` 配發(§11.3)；`test_depends.repos` 宣告 transport package、`r1_test_mocks`、`r1_interfaces`。
  查核:單一空場景可於 docker 內 launch_test 通過；兩場景並行不互擾。✅ CMake 自動註冊 I00 + I1–I18 共 19 個 launch targets；I00 無 ROS node 的 keepalive 場景驗證 launch ready、domain 配發與 parallel live-PID overlap；domain 30–48 唯一且可由 `R1_ITEST_DOMAIN_BASE` 整段 relocation；`todo_check.sh t11` 固定 CTest parallel=2。
- [x] **T11.2** I1–I4:全流程、多型別多通道、斷線恢復(disconnect=0 不誤移除)、確認死亡 + 重建(同 tick 註銷三要件)。
  查核:各場景驗證欄逐句轉為 assert。✅ I1 的 read/callback/payload/雙側 ACTIVE/InfoReq exact list、I2 的 joy/twist/string 與 topic/service 隔離、I3 的 TIMEOUT→ACTIVE 且 disconnect=0 entry 以 2 秒/至少 8 筆 fresh snapshots 證明留存、I4 的雙側各自 terminal、proxy gate、callback-before-notification、同 tick absent snapshot、舊 Handles 失效、無 retry與 App 顯式重建均為機器斷言。
- [x] **T11.3** I5–I8:CSM 失聯(master 雙閾值 + RETRY_WAIT + Handle 恢復)、target 快速重啟(空 snapshot 對帳)、註冊風暴(100 組並發,成功數 = 唯一名數)、response 丟失(三層回收)。
  查核:同上；I5/I6 使用真 `csm_master_node` 而非 mock。✅ I5 以 producer timestamp 驗 600ms/2.5s 雙門檻，並逐筆 fresh snapshot及 state-edge 證明中間 Source 持續 ACTIVE/REGISTERED；I6 以 raw status 精確觀察同 identity 的 RETRY_WAIT/endpoint absent、驗 5.2s dynamic grace下界，且對 PAIR_MISSING 首 ACK 丟失驗證同 event 重送、APPLIED→ALREADY_APPLIED、ACK quiet及 App exactly-once。I7 以 barrier 同時送出 60+40=100 attempts、producer interval overlap，並驗成功數=60 unique names、三側無 PENDING。I8 先 warm subscription，再以 integration-only blocking Sink 在真 Manager 決定性驗證 PENDING producer-time 0.35–1.0s、500ms TTL 回收與 late completion STALE，另驗已 REGISTERED entry 由 matching UNREGISTER 回收及舊世代不傷 successor。
- [x] **T11.4** I9–I13:錯誤 payload、壓力 + sanitizer(拉長版 I1)、status 觀測(與 InfoReq 互證)、master 通報鏈(丟包重送 + 冪等)、waitForMessage 端到端。
  查核:同上；I10 之 sanitizer build 由 T12 組態提供。✅ I9 DDS 型別隔離、I10 manager/service readiness 後執行三型別 100Hz×8s 壓力、I11 readiness 後以 status/InfoReq/Handle exact metadata/state/rate互證、I12 readiness 與明確 proxy arm 後驗 STATE exact payload/雙方 local row 不受 peer observation 改寫及 reliable lost-ACK same-event APPLIED→ALREADY_APPLIED、I13 即時/約1s timeout/真 waiter-count armed 後 unregister 喚醒均為機器斷言；I10 sanitizer build 依原規劃明確留待 T12。
- [x] **T11.5** I14–I18:master 失聯 degraded(回線無風暴)、terminal activity race、stale generation、retry 非阻塞與 storm 控制、service response failure 先於 master。
  查核:同上；I15/I16 需 MockMasterNode 之亂序 / 舊 generation 腳本(T10.4)。✅ I14 以雙 status proxy 分段放行 post-restart ready snapshots、驗第二側前零對帳及回線後 bounded STATE burst/次窗零新增；I15 以 MockMaster 將 DISCONNECTED 與舊 STATE 亂序送入高頻接收，逐列核對 Source ownership並驗 seal 後零資料；I16 對 late G+1 response、G UNREGISTER/DISCONNECTED 逐項驗 STALE/ignore 且 G+2 持續；I17 三 targets process-model crash/restart、producer steady timestamp 量測 bounded in-flight/週期/backoff+jitter，以新 instance/fresh snapshots/完整 identity及 settle 後重驗封住 stale cache，並對相異 event immediate replay驗 whole-history dedup；I18 response epoch terminal、matching G 在 RETRY_WAIT 回 APPLIED並觸發 matching UNREGISTER、唯一 G+1 mandatory retry及晚到 G 回 STALE且不重複 enqueue。

**驗證**
- 語意查核:I 表 18 列逐列對照 §11.2 之「步驟 / 驗證」欄；確認每列的驗證欄位全部轉為機器斷言,無「人工觀察」殘留。✅ 多輪對抗式查核修正 PENDING TTL 空洞、DDS arrival-time 偽時序、ready/startup gate、waiter pre-call race、late exact-one、stale status cache、門檻間暫態與 status/InfoReq partial compare；全部發現修正後由 3 agents 依 T11.1/I1–I6、I7–I12、I13–I18 分區重審，最終 0 must-fix。
- 實際測試:`./r1_test_framework/todo_check.sh t11`(container:`r1_todo_t11_jazzy`；單 container 內多 node,ROS_DOMAIN_ID 隔離 + docker network 第二層保障)。✅ 最終 clean PASS:19 個 CTest launch targets、39 筆 xUnit 彙總,0 error/failure/skip；CTest parallel=2，I00 machine-assert 實際 overlap；container 自動卸載。受影響 I5/I6/I11/I12/I17 另以 `--repeat until-fail:3` 全綠；I10 startup gate另連跑 5 次全綠。另因 T11 擴充 mock crash/restart 與 producer timestamp，`./r1_test_framework/todo_check.sh t10` regression PASS(27 tests)。

---

## T12 Sanitizer 矩陣、迴歸與打包(§11.4、§11.5)

**目標**:三種 sanitizer build 全綠、`.deb` 打包驗證、全量迴歸。
**依賴**:T11。

**Lint 修正與 interfaces 進版(v0.8.27)**：使用者授權接續前輪未完成的兩包 lint 與測試，並要求 interfaces 補進版。先修文件再實作；以 mocks/integration 已提交 HEAD 的乾淨候選在官方 Docker 執行 clang-format 18、Ruff 0.15.7 `check --fix --no-unsafe-fixes`／`format`，沿用 nested 設定與 gate 的 cwd／路徑，不變更規則。只把 formatter 產物的 scoped patch 提交，保留原工作樹 bytes，I10 額外授權另列下段。正式 nested lint PASS：mocks 16 C/C++ files、integration 4 C/C++／20 Python files；格式 commits 分別 5af25b8／46e7116。Python AST 僅 I04 unused re import 移除，C++ 另有原生 formatter 排序同一組 using declarations；獨立複核 0 must-fix。

本輪追加裁決：使用者明確允許 I10 程序退出測試補強另做獨立 commit。Framework sanitizer gate 已要求 `TestI10ProcessShutdown.test_clean_shutdown`，因此在 lint commit 後只另提交既有 `scenario_i10_stress_extended.py` 的三個 sanitized nodes 暴露與 post-shutdown 檢查（exit 0、無 sanitizer diagnostics），再一起驗證；不將其混入格式 commit，也不連帶納入 I15/I18 或其他 T12 差異。

I10 獨立 commit `07d8a13` 後，兩包均以乾淨候選自己的 nested 四步流程、官方 Jazzy Docker、ROS jobs 全域串行驗證，build／deps／無參數 run／clean 全 exit 0 且確認容器卸載：mocks unit 3／integration 20（共 23）與 UBSan 3 cases PASS，ASan/TSan N/A；integration 19 targets／21 unique cases、I10 ASan/LSan 2 cases PASS，controls／instrumentation／results gates 通過，UBSan N/A、TSan SKIP/77。40 colcon records 非 40 個功能案例，TSan 不滿足 T12.2。Integration 的 R1 dependencies 為乾淨 interfaces 5bef9c0／mocks 5af25b8／transport 8f56a55，但 legacy rv2_interfaces 沿用原唯讀 dirty workspace，重現限制已於 PR 揭露，不改該 repo。

驗證後補獨立版本 commit/tag：interfaces `5bef9c013128ee31005a4967d6d0229e428426b1`、mocks `37d6e7f3f9c27427b03d55807e02bfcb12b3372c`、integration `5adecce4986b386ee4f75ff1f2b02fa273d1fd41`，皆只改 package.xml 0.1.0→0.1.1；Docker metadata PASS，不在 metadata-only release 後重跑 ROS。Interfaces 沿用前輪完整入口／lint SKIP 證據；已更新 [interfaces PR #1](https://github.com/cocobird231/r1_interfaces/pull/1)，提出 [mocks PR #4](https://github.com/cocobird231/r1_test_mocks/pull/4)／[integration PR #3](https://github.com/cocobird231/r1_integration_tests/pull/3)，base 皆 master、branch/tag atomic push，不自行 merge。Framework pin 仍 f5952a8，transport v0.1.2／Doxyfile 與原有差異不動。

Mocks 原格式化工作樹已全部提交；integration 僅 I15/I18 非格式啟動／診斷修正仍未提交，本輪測試候選不包含它們，不能據此宣稱驗收其 code=10 修正。16 份 mocks／24 份 integration source SHA256 前後全部一致。逐項 logs、XML、版本與依賴證據：[lint-and-test-report.md](../../../r1_integration_tests/test_env/jazzy/lint-fix.x9QvJk/lint-and-test-report.md)。docs 無 remote 保留本地；先前未過／尚待授權段落為歷史。

**Consumer PR 前驗證(v0.8.26)**：使用者授權推 PR。各 package 在自身 `test_env/jazzy/framework-pr.*/checkout` 建立已提交 HEAD 的乾淨副本，submodule 由 GitHub 還原 f5952a8；使用該副本自身的 `./r1_test_framework/test_lint.sh`，不納入主工作樹未提交的格式化、I15/I18 或 T12 差異。interfaces build→deps→無參數 run→clean 全 exit 0，0 executable tests、sanitizer N/A，lint 無支援來源 SKIP；已更新 [PR #1](https://github.com/cocobird231/r1_interfaces/pull/1) 至 4f6176b，base master，保持 0.1.0、不附 release/tag。

Transport committed-source lint PASS(C/C++ 32／Python 3／Shell 1)，一般 unit 84／integration 50、ASan 64、UBSan 84 cases PASS，TSan off SKIP/77；正常 colcon 197 records 非唯一案例數，cppcheck 原生 32 SKIP。四步完整流程全 exit 0 且確認容器卸載。首次乾淨 rv2_interfaces HEAD 8a9d995 因缺 legacy controller 欄位而 normal build exit 2；其失敗 logs 保留，重驗使用原 workspace 唯讀 dirty dependency，transport／framework 仍為乾淨精確 HEAD。故不能宣稱全依賴 committed HEAD 可重現，PR 已明示限制。通過後獨立 `chore(release): v0.1.2` commit/tag `8f56a551368a4c8838420f0efde1313e0efcabd8` 僅改 package.xml；相對實測來源無其他差異，Docker metadata PASS，branch/tag atomic push，已提出 [PR #8](https://github.com/cocobird231/rv2_control_signal_transport/pull/8)(base r1)。rv2 Doxyfile 與既有來源 diff 不動。

Mocks／integration 已提交版本 lint 分別 FAIL 11／26，未 push／附版本／PR；已詢問是否允許另外提交既有格式化修正，尚待回覆，不以 draft 規避 gate 或自行納入 I15/I18/T12。docs 無 remote 保留本地。完整結果、各原始 log 與依賴限制：[consumer-pr-report.md](../../../rv2_control_signal_transport/test_env/jazzy/framework-pr.U074Jd/consumer-pr-report.md)。T12.2 保持未完成，未自行 merge。

**Rebase 後 pull／pin 更正(v0.8.25)**：依使用者最新裁決，在乾淨 standalone framework 本地 master 實際執行 `git pull --ff-only origin master`，exit 0，確認 HEAD／origin/master／即時遠端主線均為已合併 v0.5.0 `f5952a8d2d1f834870283494e22173d8511e5d69`。與原 tag `af386de` tree 一致，但 consumer 不再沿用合併前 SHA；tag 不移動。四個 nested repos 各自 fetch、核對並 checkout 此 SHA，新增 gitlink-only 更正 commits：interfaces `4f6176b`、mocks `0cbf2c8`、integration `61332a0`、transport `f4ff1e0`，皆在 `coco-codex/framework-rebase-pin`。前輪 commits／分支保留，不 amend；既有來源 diff SHA256、package 版本、rv2 Doxyfile 與獨立 rv2_project 不變，未 push／新 PR／release。

官方 Jazzy Docker 重驗四個 nested owner/version/shell syntax 與 CLI 入口；toggle 8＋full-run orchestration 6 回歸每份皆 PASS，共 4×14 次（14 個不同 framework 案例，非 ROS 測試）。TSan off 明示 SKIP/77，不勾選 T12.2；本輪未重跑 ROS 全套、sanitizer runtime、lint、打包或 test_build 掛載查核。獨立複核確認各提交僅一個 mode 160000 變更，nested clean，0 must-fix。實際 pull 與入口原始 logs 見 [rebase-pin-report.md](../../../rv2_control_signal_transport/test_env/jazzy/framework-rebase.nZ4iXh/rebase-pin-report.md)。以下 v0.8.24 與更早段落為歷史，現行 pin 及規範以 v0.8.25 為準。

**Framework v0.5.0 submodule 導入(v0.8.24)**：framework PR #8 已由使用者 merge；主線 release `f5952a8d2d1f834870283494e22173d8511e5d69` 與原 tag `af386dee731ec13448a344e9f64ed0978bd6cfba` tree 一致，四個頂層 consumers 固定原 tag，未移動既有標記。gitlink-only commits：interfaces `85b893b`、mocks `edc7dda`、integration `257413f`、transport `77b77dc`，皆在 `coco-codex/framework-v0.5.0` 分支，僅一個 mode 160000 路徑變更。先前 I15/I18、格式化、export／其他測試差異仍保留未提交，排除 gitlink 的 diff SHA256 前後相同；package.xml、rv2 Doxyfile 與獨立初始化中的 rv2_project staged workspace 不變。

四個 nested checkout 的 owner/version/shell syntax、既有 toggle 8＋full-run orchestration 6 回歸各自 PASS（共 4×14 次，不是 56 個不同功能案例）；官方 Jazzy Docker 內 CLI 查核，TSan off 明示 SKIP/77。另逐 package 執行 nested test_build，真實驗證來源/framework RO 與 owner/run-root 掛載，再以 nested test_clean 卸載本輪容器，logs 保留。本輪未執行 test_deps／ROS build/test、sanitizer 矩陣、package lint 或打包，不冒稱 nested 全套正式驗收或勾選 T12.2。依本次 submodule 更新範圍，四個 commits 僅留本地，未 push／新開 PR／附 package release commit/tag；後續 PR-ready 才依 §1.4 獨立定版，interfaces 仍維持 0.1.0 例外裁決。完整紀錄：[submodule-update-report.md](../../../rv2_control_signal_transport/test_env/jazzy/framework-v0.5.0.yKzumw/submodule-update-report.md)。

**I15 診斷與修正(v0.8.23)**：依使用者授權先修文件，再僅修改 `r1_integration_tests/test/integration/scenario_i15_terminal_activity_race.py` 的 `_register_and_activate` 與 teardown 診斷。精確接受初始 OK(0)／RETRY_SCHEDULED(10)，source 須 REGISTERED＋endpoint 且有完整 identity triple，10 另須 matching-generation RETRY_SUCCEEDED(kind=7)；sink readiness 與兩側 ACTIVE gates 均匹配同 identity。整段 `test_activity_and_seal_outcomes` 本體完全不變，保留 120 Hz、1.2 秒 disconnect、activity/seal、terminal 恰一次、seal 後零資料與亂序 master 控制斷言；獨立 review 0 must-fix，nested lint C/C++ 4／Python 20 PASS。

一般舊測試 baseline 1/1 PASS，並未自然重現；app-only 首次 manage-client-not-ready 受控注入，舊測試實際收到 code=10→kind=7／G=2 成功，卻只等 code=0 而不送資料，最終 FAIL。相同 C++ binaries／注入條件下，修正後 c15_live 以 G=2 建立、其餘兩 channel 以同步 code=0 建立，完整 I15 PASS。原歷史失敗未記事件，不能以受控結果宣稱其確切根因已證實；baseline、RED、GREEN 與 teardown 事件均留獨立原始 log。

本輪無參數完整入口 `full-20260912T155344.yOpCrA` 已 PASS／exit 0：同一 invocation/container 完成一般 19 targets／21 cases（包含 I15/I18）及 I10 ASan 2 cases；ASan clean/defect controls、instrumentation、精確 results／子程序 shutdown gates 均通過，UBSan N/A、TSan SKIP/77。framework lint C/C++ 3／Python 10／Shell 14 PASS。build/deps 成功、test_clean 已卸載本輪容器，所有 logs/build/install 保留。逐項 XML 計數另存 `normal-cases.tsv`，不把 colcon 40 records 說成 40 個獨立案例，也不將 SKIP 算入 T12.2。

接續原暫緩 PR：framework 功能仍為 `976007b`，驗證後以僅改 VERSION／README 安裝 tag 的獨立版本 commit/tag **v0.5.0 `af386dee731ec13448a344e9f64ed0978bd6cfba`** 定版，Docker metadata 查核 PASS，branch/tag 已 atomic push，[PR #8](https://github.com/cocobird231/r1_test_framework/pull/8) 已移除 DO NOT MERGE、供使用者審核。既有 v0.4.0 `dbef3f4` 不移動；使用者 merge 後才更新所有 consumer gitlink，不能 squash/rebase 已標記版本。其他 owner 沿用 v0.8.21 同功能來源的成功證據，本輪未重跑三包或獨立 Debian 打包；interfaces PR #1 仍保持 0.1.0、不新增 release commit/tag。

其他既有 diff（包含 I18 修正）排除 I15 後 SHA256 保持 `ad4423b55de164a1edd90980f0089506bc63eb94c5aa01d93d2c2f53edbea69d`；I15 測試本體前後 SHA256 亦相同，I15/I18 修正保留未提交差異，待 consumer 後續一併處理。不改 runtime、consumer 版本/gitlink 或 rv2 Doxyfile。逐項證據：[I15-fix-report.md](../../../r1_integration_tests/test_env/jazzy/I15-fix.A7ODxO/I15-fix-report.md)。

**I18 診斷與修正(v0.8.22)**：依使用者授權先修訂文件，再只修改 `r1_integration_tests/test/integration/scenario_i18_service_response_failure.py` 的啟動前置條件與診斷輸出。初始同步回覆精確接受 SUCCESS(0)／RETRY_SCHEDULED(10)，但兩者皆須唯一 wire REGISTER 與 matching identity、endpoint ready 的 REGISTERED status；10 另須 matching-generation RETRY_SUCCEEDED(kind=7)。ACTIVE、response-failure epoch、matching UNREGISTER、恰一次 terminal／G+1 mandatory retry、late-event 去重斷言均保留，未修改 runtime 或 timeout。teardown 輸出既有 timed events 與最後 status，使往後失敗留下實際事件。

原未修改 I18 連續 5 次一般診斷皆 PASS；app-only 的初次 manage-client-not-ready 受控注入，在相同 C++ binaries 下證實舊測試因 code=10（其後已收到 kind=7／G=2 成功）而 FAIL，新測試 PASS 且完成故障後 G=3 retry。原歷史失敗缺少事件，不能以此次受控結果反推其確切根因。首次廣域 LD_PRELOAD 注入碰到 Python dynamic-symbol 問題，該工具失敗明示 INVALID，不計入產品驗收；所有原始 logs 均保留。

無參數完整入口本輪 `full-20260912T152358.7p2n8Z`：19 個 launch targets／21 個案例，I18 PASS，另有 **I15 FAIL**，故一般測試 20 PASS／1 FAIL，整體 exit 1、ASan NOT_RUN、UBSan N/A、TSan SKIP/77。I15 在首次 `_register_and_activate` 等待 code=0 失敗，尚未開始 send／terminal-activity 斷言；log 未記實際回覆碼，不能定因，本輪不擴大修正 I15。integration nested lint PASS（C/C++ 4、Python 20）。完整流程失敗不以單項通過取代；framework PR #8 保持 DO NOT MERGE，下一版 release/tag 繼續暫緩。

另外以獨立隔離 run `i18_fix_i10_asan_20260912_1531` 補跑 `test_run.sh -a asan -f '^scenario_i10_stress_extended$' -j 1`：I10 壓力與子程序 shutdown 共 2 cases PASS，ASan clean/defect controls、build instrumentation 與 results gate PASS；此單項結果不改寫前述完整流程 ASan NOT_RUN／整體 FAIL。本輪 build/deps 均成功，兩個測試容器皆已由 test_clean 卸載，logs/build/install 保留。

本輪不改任何 consumer gitlink／package.xml 或 rv2 Doxyfile；integration 其他既有未提交差異經 SHA256 比對完全保留，I18 修正亦先保留 diff。interfaces API 權限已恢復並已提出 [PR #1](https://github.com/cocobird231/r1_interfaces/pull/1)，保持 0.1.0、不新增 release commit/tag；新版 framework merge 後才更新各 owner submodule。診斷與逐項原始證據：[I18-fix-report.md](../../../r1_integration_tests/test_env/jazzy/I18-fix.Sz2iPl/I18-fix-report.md)。

**四步完整入口開發驗證(v0.8.21)**：framework 功能 commit `976007b` 將無參數 test_run 串接一般完整測試與 owner 適用 sanitizer，TSan 預設 off；沿用既有 runtime/build/results gate，按 run/profile 隔離，失敗不繼續後續已啟用階段。使用官方 Jazzy Docker，以明確 owner override 依序跑四個 packages，未更新 nested v0.3.0 gitlink。transport 一般 134（unit 84／integration 50）、ASan 64、UBSan 84 PASS；mocks 一般 23、UBSan 3 PASS；interfaces build PASS、0 cases。transport 既有 cppcheck 32 SKIP 仍揭露。

integration 一般測試為 20 PASS／1 FAIL：I18 在 `scenario_i18_service_response_failure.py:123` 等待 `register_result controller=c18 code=0` 15 秒未符合；完整流程 exit 1，ASan 正確標為 NOT_RUN，TSan SKIP/77。原始事件只在記憶體，log 無實際失敗回覆碼，不能定因；同一已編譯來源另做一次事件輸出診斷，I18 收到 code=0 並 PASS，**不覆蓋原失敗、不當成完整驗收通過**。不修改 consumer 測試或 runtime，後續修正待使用者授權。各測試容器已卸載、證據保留。

framework 本輪 51 個具名 Python cases（21 sanitizer、16 packaging、8 toggle、6 full-run）與 owner/selector/sanitizer/lint-entry shell suites PASS；framework lint C/C++ 3、Python 10、Shell 14 PASS。報告與逐項原始 log：[R1-full-entry-report.md](../../../rv2_control_signal_transport/test_env/jazzy/full-entry.rbdHfE/R1-full-entry-report.md)。本輪未重跑獨立 Debian 打包/乾淨安裝。已推送功能 commit，更新既有 framework [PR #8](https://github.com/cocobird231/r1_test_framework/pull/8) 的標題與說明為 **DO NOT MERGE／I18 validation pending**；目前 token 拒絕 convertPullRequestToDraft，GitHub draft 狀態仍為 false，需使用者手動轉草稿。完整驗證未全過前不新增下一版 release commit/tag；既有 v0.4.0 tag 不移動。所有 consumer pin 與版本保持不變，interfaces 另依使用者裁決不新增 release commit/tag，其 API 404 仍阻塞 PR。

**TSan 平台查證與開關(v0.8.20)**：本機 Linux 6.17.0-35／官方 Jazzy image，`vm.mmap_rnd_bits=32`、ASLR=2、stack 8192 KiB、virtual memory unlimited。原 GCC 的 unexpected memory mapping 與 Clang 18 的 personality CHECK，符合 [LLVM #78351](https://github.com/llvm/llvm-project/pull/78351) 描述的高 entropy mapping 衝突及嘗試停用 ASLR 的恢復路徑；[Docker seccomp 文件](https://docs.docker.com/engine/security/seccomp/) 說明 personality 參數限制。這是與證據相符的原因判斷，不宣稱已用變更安全設定的 A/B 實驗證實。本輪新 clean probe 仍 BLOCKED（stderr 空白），不以此推稱新的 mapping 訊息；原錯誤 log 保留。查證 log：transport `test_env/jazzy/T12-formal.6Gxz4q/tsan-research-preflight.log`，Clang 舊 log：`test_env/jazzy/runs/framework-T12-check/clang-tsan-diagnostic.log`。目前安全邊界下無可靠修法，依 §1.3.3 增加顯式開關；開關驗證與 TSan runtime 驗收分開。

開關實作結果：framework 功能 commit `0f11798` 後，另附只改 VERSION/README 安裝 tag 的 `chore(release): v0.4.0` commit/tag `dbef3f40818081756d147ce7b064b4e6e7917916`，已推送 [PR #8](https://github.com/cocobird231/r1_test_framework/pull/8)（base master，待使用者 merge）。Docker 7 組新 CLI integration 回歸、21 sanitizer unit、既有 owner/selector/sanitizer integration 全 PASS；後者包含真實 ASan/UBSan 正反控制，但不是 TSan runtime 驗收。另對 transport/integration 兩個真實 owner 以唯讀掛載、開發 framework 明確 override 驗證兩入口，共 4 次 SKIP/exit 77，沒有執行 TSan。完整 lint C/C++ 3、Python 9、Shell 14 檔全過，獨立複核無 must-fix。原始 log 在 transport `test_env/jazzy/T12-formal.6Gxz4q/`：`tsan-toggle-full-regression.log`、`tsan-toggle-final-check.log`、`tsan-toggle-lint.log`；新 Python 檔只以 Docker Ruff 格式化。consumer 四個 pins 仍是 `67755d6`，各 package 版本、rv2 Doxyfile 與既有來源差異保留；不提前導入或勾選 T12.2。

**目前狀態(v0.8.19，2026-09-12)**：framework v0.3.0 已導入四個 consumers，gitlink-only commits 為 transport `3026c16`、mocks `1bf34dc`、integration `703d29c`、interfaces `2c7815b`，皆固定 `67755d663922c55a15d50933ef083def4d92c964`。以下 v0.8.15–v0.8.18 為開發／查證歷史，目前只剩 T12.2 平台驗收阻塞。

| 正式 nested 查核 | 結果 | 證據（transport 的 test_env/jazzy/T12-formal.6Gxz4q/） |
|---|---|---|
| T12.1 ASan/LSan | transport 3 targets／64 cases、integration I10 1 target／2 cases PASS，無 report，三個 C++ 子程序正常退出 | `serial-t12-asan.log`、`integration-asan.log` |
| T12.2 TSan | **BLOCKED**：transport/integration clean runtime probe 均 unexpected memory mapping、exit 1，未執行 race 矩陣 | `transport-tsan.log`、`integration-tsan.log` |
| M22 補強 | test-only forwarding probe 驅動真實 Manager/Source；activity 先勝出取消註銷、seal 先勝出拒絕 hot path、callback→shutdown→removal 各一次。一般/ASan 過，ASan 額外五次皆過；不是 TSan 替代 | `m22-asan-repeat.log`、`serial-t7.log` |
| T12.3 UBSan | transport 6 unit targets／84 cases、mocks 1 target／3 cases PASS，無 report | `serial-t12-ubsan.log`、`mocks-ubsan.log` |
| T12.4 Debian | 三包內外版本/檔名、dpkg、discovery、公開 headers 下游 compile/link 與 master 啟停 PASS；全量回歸 134 cases（unit 84、integration 50）PASS，cppcheck 原生 32 SKIP | `serial-t12-pkg.log`；產物 `../runs/t12-pkg-20260912T110017-823051/packages/run.LfZk0s/` |
| T12.5 完整鏈 | t2→t3→t4→t5→t6→t7→t8→t9→t10→t11 連續且串行，十項 exit 0；mocks 23 cases、T11 19 targets／21 cases PASS | `serial.log`、`serial-exit-codes.tsv`、`serial-t2.log` 至 `serial-t11.log` |
| 各 owner lint／interfaces | transport/mocks/integration lint PASS；interfaces 無適用來源 SKIP，T1 build PASS | `transport-lint.log`、`mocks-lint.log`、`integration-lint.log`、`interfaces-lint.log`、`interfaces-t1.log` |

原平行 UBSan K11 的 23.935 Hz 失敗與 t5 同 topic 重疊 265 ms；獨立官方容器 probe 證實 domain 0 可跨 default bridge 收到訊息。全域串行重驗保持 K11 18–22 Hz 斷言及 runtime 不變後通過；失敗、互通證據與新 run 分開保留。總報告為 `T12-formal-report.md`。本輪 ROS 測試容器全部卸載，logs/build/deb 保留。

打包 manifest 的 `validation_mode` 由現行框架固定為 `development-validation`；此處「正式」指已合併 tag 的 nested TODO gate，不代表 timestamp/hash 測試 deb 可當正式 release。manifest 保留 transport 與既有 dirty `rv2_interfaces` 的 source-tree SHA256，不修改後者。consumer 的測試/export 差異與前輪 mocks/integration 格式化差異保持未提交；package.xml、rv2 Doxyfile 與 runtime headers/src 不動。T12.2 尚缺支援 TSan 的環境，整體 T12 未完成，未附 consumer release commit/tag 或提出 PR。

**正式導入開工(v0.8.17)**：framework PR #7 已合併；主線 `6a04bfe913f9a07862020e270d263b8db7d6f08f` 與原 tag commit `67755d663922c55a15d50933ef083def4d92c964` 的 tree 同為 `e50f516813aa5701cb5137ae360db259be85ff67`。依既有 rebase 處理方式，四個 consumer pin 原 tag commit，不移動 tag。以下 v0.8.15–v0.8.16 為歷史預驗證紀錄，不代表目前仍待 framework 合併。本輪從各 owner nested 入口重跑並保留獨立產物；先補 M22 calc→activity→commit 的確定性交錯，再執行 transport 矩陣/完整鏈。不得把前輪預驗證當本輪結果；TSan 平台阻塞如實保留。前輪 mocks/integration 格式化差異不因 pin 升級自行丟棄或混入 gitlink-only commit。

**現況校準(v0.8.15)**：transport PR #7 已合併，來源版本為 0.1.1；各 consumer 仍 pin framework v0.2.1 tag `3dd3c27`，不移動既有 tag。舊 T12 入口只有 CXX/EXE flags，沒有跨 package I10、runtime fail-closed、隔離產物或乾淨安裝驗證，故不可視為已實作。mocks/integration 前輪格式化 diff 保留，不混入框架變更。

**導入順序**：先修 framework 並以明確 `R1_TEST_PKG_DIR` 作開發預驗證，產物需標示未發布框架與來源 SHA/dirty 狀態；consumer 的既有 nested checkout/gitlink 不動。framework 自身回歸與 lint 通過後，依 §1.4 獨立版本 commit/tag → PR → 等待使用者 merge → 本地 master pull／核對合併後版本 SHA。之後 consumer 固定此 SHA（rebase 時不同於原 tag），從各 owner nested 入口正式執行下列查核。預驗證不等同正式驗收；未完成的小項保持未勾選。

**開發進度(v0.8.16)**：framework 的 `73798d2`(sanitizer)、`3514ccb`(packaging)、`2f0af43`(README) 後，附只改 VERSION/安裝 tag 的版本 commit `67755d663922c55a15d50933ef083def4d92c964`／annotated tag `v0.3.0`；[PR #7](https://github.com/cocobird231/r1_test_framework/pull/7) base 為 `master`，尚待使用者 merge。consumer 仍固定 v0.2.1 `3dd3c27`，不移動 tag；本節全部結果均為開發 checkout 預驗證，並非新版 nested 入口的正式驗收。

| 開發預驗證 | 結果 | 證據(相對 owner 的 test_env/jazzy/) |
|---|---|---|
| Framework 回歸與 lint | sanitizer unit 21、packaging unit 16 PASS；實際 CMake/入口/失敗傳遞及既有 owner/selector 回歸 PASS；lint C/C++ 3、Python 8、Shell 14 PASS | transport `runs/framework-T12-check/framework-new-regression.log`、`framework-matrix-final.log`、`framework-existing.log`、`framework-lint-final.log` |
| transport ASan/LSan | 3 targets、64 cases PASS，無 report | transport `runs/framework-T12-check/transport-asan.log`、`log/sanitizer-build.json`、`log/sanitizer-results.json` |
| I10 ASan/LSan | 1 target、2 cases PASS(原壓力案例 + 新增三個 C++ 子程序正常 shutdown gate) | integration `runs/i10-T12-check/i10-asan.log`、`log/sanitizer-results.json` |
| transport UBSan | 6 unit targets、84 cases PASS | transport `T12-ubsan-development.50GyoJ.log`、`runs/t12-ubsan-20260911T095418-3712962/log/sanitizer-results.json` |
| mocks UBSan | 1 unit target、3 cases PASS | mocks `T12-ubsan-development.oWKiKk.log`、`runs/t12-ubsan-20260911T095806-3733003/log/sanitizer-results.json` |
| transport 一般全量回歸 | 15 targets、134 功能 cases PASS；原生 cppcheck 32 SKIP，colcon 彙總 189 records 非唯一案例數 | transport `runs/package-T12-check/full-regression.log`、`export-fix-regression.log` |
| Debian build + 乾淨安裝 | 三包 metadata/檔名一致、dpkg/discovery/公開 header 下游編譯連結/master 啟停 PASS；修正前因缺少 r1_interfaces export 明確 FAIL | transport `runs/package-T12-check/packages/run.limlfN/`；負例 `packages/run.yVaSsH/verify.log` |
| TSan | **BLOCKED**：GCC clean probe unexpected memory mapping；Clang 18 clean 第一次 0、第二次 139(personality runtime CHECK)，未將偶發啟動當成功 | transport `runs/framework-T12-check/log/preflight-tsan/`、`clang-tsan-diagnostic.log` |

consumer 保留待提交差異：transport 補 `ament_export_dependencies(... r1_interfaces)`，並補 L14 真 activity/seal 並發、S11 停流收斂、K12 非空 intake、K15 真 waiter fence、K16 receive/seal 競爭；integration 僅新增 I10 三個實際子程序的正常退出與 diagnostic gate，前輪格式化 diff 仍保留。未更改 runtime 邏輯、package.xml、Doxyfile 或任何 gitlink。既有 M22 是真 Manager 的週期並發，尚非 calc→activity→commit barrier 證據，T12.2 驗收前須補足，不宣稱已完成決定性交錯驗證。

v0.8.16 當時尚未完成：framework merge 後的 consumer pin/新 nested 入口正式矩陣、支援的 TSan runner 與 M22 補驗、T12.5 指定 t2–t11 連續鏈。當時沒有以部分/歷史結果勾選 T12.1–T12.5；歷史報告見 transport `runs/framework-T12-check/T12-development-report.md`。目前結果以本節 v0.8.19 為準。

- [x] **T12.1** ASan + LSan job:H6 / K10 / K15 / M10 / I10(UAF、shutdown 與 leak 回歸)。
  查核：transport 執行 `./r1_test_framework/todo_check.sh t12-asan`；`r1_integration_tests` 執行相同 item 跑 I10，且實際 instrument transport 與 C++ 場景 nodes。兩份皆全綠、正常 shutdown、無 sanitizer/leak 報告。
- [ ] **T12.2** TSan job:LivenessState 並發活動與 terminal seal(L14–L18)、Source / Sink hot path(S11/K10/K12/K16)、tick commit(M22)、Handle replacement(H6)、M4 註冊風暴及 I10。
  查核：transport 與 `r1_integration_tests` 各執行 `./r1_test_framework/todo_check.sh t12-tsan -t on`，覆蓋以上案例，無 race 報告。runtime/平台不支援須回非零並記為阻塞，不可跳過後宣稱 PASS；不得更改 host sysctl 或自動加入 suppressions。
  人工停用：新版框架預設 off，`./r1_test_framework/todo_check.sh t12-tsan [-t off]` 僅產生 SKIP/exit 77，**不滿足本項查核**；須明確 `-t on` 開啟。兩個 owner 都適用，正式導入仍須先完成 framework merge/pin。
- [x] **T12.3** UBSan job:全部單元測試。
  查核：transport 與 `r1_test_mocks` 各執行 `./r1_test_framework/todo_check.sh t12-ubsan`，精確匹配 `unit` label 且實際測試非空，diagnostic 必須使 job 非零。interfaces/integration 無 unit cases，明示不適用，不用空集合充當成功。
- [x] **T12.4** `.deb` 打包:`test_packages.sh` 產出命名符合 §11.5.3 規則(version 段附 timestamp + short hash)之套件,並於乾淨 container 內 `dpkg -i` 安裝驗證。
  查核：transport 的 `./r1_test_framework/todo_check.sh t12-pkg` 產出檔名匹配 `ros-<distro>-<pkg>_<version>.<YYYYMMDDHHMMSS>.<hash>_<arch>.deb`，且 `dpkg-deb -f` 的 Package/Version/Architecture 完全相符。建置並攜帶必要 workspace-local 依賴；以同官方 base 的新容器安裝外部依賴及產出 deb，不掛載來源/build/install overlay，驗 `dpkg -i`、ROS package discovery、公開 R1 header/link 與 node 啟動。禁止只改檔名、忽略未解析依賴、複製整個含 test_env 的 repo、或只驗 dpkg metadata。timestamp/hash 是測試產物版本，不修改 package.xml、不代替 PR 前版本 commit。
- [x] **T12.5** 全量迴歸:t2–t11 連續執行一輪全綠(CI 腳本鏈)。
  查核:從 workspace 根目錄依目標 package 分派以下指令，全部結束碼為 0：

  ```bash
  (cd src/rv2_control_signal_transport &&
    for i in t2 t3 t4 t5 t6 t7 t8 t9; do
      ./r1_test_framework/todo_check.sh "$i" || exit
    done) &&
  (cd src/r1_test_mocks && ./r1_test_framework/todo_check.sh t10) &&
  (cd src/r1_integration_tests && ./r1_test_framework/todo_check.sh t11)
  ```

**驗證**
- 語意查核:§11.4 矩陣三列的目標測試 ID 與 T12.1–T12.3 覆蓋集合一致。
- 實際測試:如各小項查核指令；container 依項目命名(`r1_todo_t12-asan_jazzy` 等)，同 item 的不同 owner 依序執行，逐一自動卸載。每次查核使用 `test_env/<distro>/` 下獨立 run 目錄保留 build/install/log、來源與工具組態、測試選集與結果；不覆蓋先前一般/其他 sanitizer 產物。ASan/TSan/UBSan 分開乾淨建置，不能混用或沿用 unsanitized build；Python orchestration 與 distro 預編譯 ROS/DDS 不宣稱已 instrument。I10 需檢查 C++ 子程序正常退出及 sanitizer diagnostics，不能只憑 Python assertions PASS；無案例、runtime 啟動失敗、diagnostics、異常退出均須失敗。不關閉 leak detection 或以 suppressions 掩蓋失敗，第三方報告亦保留並另行裁決。

---

## T13 rv2_project snapshot package(§2.1.1)

**目標**：以 ROS2 `ament_cmake` package 安裝與查詢專案版本組合，不新增 runtime node，不宣稱已完成所有 R1 packages 的總驗收。

- [x] **T13.1** 依新文件位置完成版本／歷史／Agent 署名與所有已合併 R1 版本對照；保留搬遷前文件 Git 歷史與既有 staged submodules，不建立缺少可取得 remote 的 docs gitlink。
- [x] **T13.2** 新增 `package.xml` 0.1.0、CMake/ament 註冊、README、`snapshots/v0.1.0.json`；安裝文件與 snapshot 至 `share/rv2_project`。每個 component 記錄 release 版本、合併主線 SHA、原 tag SHA/tree；固定來源不跟隨 HEAD。
- [x] **T13.3** 在乾淨 checkout 實際 pull 並核對遠端，再更新 project gitlinks。根目錄另有自身 `r1_test_framework/`；保留使用者的 `ros2_ws/src/` 五個 gitlinks，兩處 framework 同 SHA。既有 dirty 開發 checkout／consumer 內部 pins／rv2 Doxyfile 不動。
- [x] **T13.4** `test/unit/` 驗證 manifest 合約正反例，`test/integration/` 驗證真實 package.xml、gitlinks、checkout、release tree、文件對照與安裝結果；兩個 CTest labels 均非空。ROS discovery 不把 nested packages 混入 owner 測試。
- [x] **T13.5** 自己的 nested `test_build`→`test_deps`→無參數 `test_run`→`test_clean` 與獨立 lint 全過，保留逐項 log／exit code；本 package 無 native runtime，sanitizers 為 N/A，不冒充整體 R1 驗收。

完成證據(v0.8.29)：功能 commit `3ba0b4d71f074aaabefab5551b9dc1f5afb6252e`，乾淨已提交 owner 的 run `full-20260912T193350.LGU34Y` 一般 PASS/exit 0；unit 131、integration 9 unique pytest cases，另 CMake/XML 各 1 檢查與 4 CTest wrappers，colcon 彙總 146，不能誤算成 146 個功能案例。Lint 三份 Python PASS，無 C/C++／Shell 來源。乾淨 recursive clone 透過本地 Git object transport（非主機來源 overlay、不使用未提交檔）亦通過同組測試與原歷史祖先查核；Git ownership／ROS setup 診斷失敗僅屬一次性驗證 harness，原 logs 保留。四步與獨立 lint、clone 最終均 exit 0，容器已清除。

初輪 unit 131／integration 6 PASS、3 FAIL 是 project 舊 checkout 未取得 rebase 前 release tags，`pull` 不保證帶回不在新主線祖先中的 tags；補取明確原 tag 並核對 tree 後通過，不移動 tag、不更改固定 release。README 取得／升版流程已補明確取 tags，測試自身仍唯讀、不連網。文件歷史 merge／backup 與三份既有 tracked dirty diff SHA256 均另經獨立複核。完整 [T13 測試報告與逐案例 logs](../../test_env/jazzy/project-snapshot.sPrkip/T13-report.md)。

**驗證**：`rv2_project` 的 ROS discovery、安裝 metadata 與兩類測試一致性；錯誤版本／SHA／path／缺失 component 必須失敗。整個 R1 workspace 的依賴 closure 與 runtime 驗收仍受 §2.1 缺口限制，另行安排。

---

## T14 總驗收前版本與來源收斂(v0.8.30)

- [x] **T14.1** Project 五個 workspace submodules 與 root framework 實際 pull／核對最新已合併版本；新增 v0.1.1 snapshot，保留 v0.1.0 bytes。獨立版本 commit／annotated tag、lint、unit/integration／安裝一致性通過後提出 PR 至 project master。
  已推 [PR #1](https://github.com/cocobird231/rv2_project/pull/1) 與 v0.1.1 tag；fddcccd 只改 package.xml。候選 `full-20260912T200125.qaqv1q` 與乾淨 release `full-20260912T200305.dEK5vQ` 皆 PASS/0：unit131／integration9、CMake/XML 各1＋CTest wrappers4=146 colcon records，無 error/failure/skip；lint 三份 Python PASS，cleanup 已卸載容器。證據目錄：`rv2_project/test_env/jazzy/snapshot-v0.1.1.FzqtBB/`。本輪後續文件另在工作分支，不修改已發布 v0.1.1 tree/tag；元件合併後另做新 snapshot。
- [ ] **T14.2** Transport 只在新 `r1` 工作分支移除 legacy 程式、測試、keyboard launch/config 與 rv2_interfaces／rclcpp_components 依賴，保留 R1 namespace／API／113 cases 與 master。既有 T12/export 補強另外 commit；乾淨依賴 normal 113／ASan 64／UBSan 72 及 Debian downstream export 證據齊備才定版／PR。若 framework 相容版本尚未 merge，先保留開發預驗證與待導入狀態。
  開發預驗證已 PASS：乾淨 source 423ff10／framework a058498，明確 owner override，run `full-20260912T201802.B6Q82f` 一般 unit72／integration41、ASan64、UBSan72 及 runtime/build/results gates 通過；TSan SKIP/77。功能案例零 skip，cppcheck 另有22原生 SKIP，不能算靜態分析 PASS。Lint C/C++22／Shell1 PASS。`packages/run.xs0sLd` 只建 interfaces c25fcc1 與 transport 423ff10 兩包，來源與 framework 均 clean；新官方容器只 RO 掛載 deb artifacts，dpkg／discovery／公開 headers/link／node 啟停全 PASS，來源 package.xml 版本未動。build/deps/clean exit0，驗證及 owner 容器均卸載。完整 logs／逐案例位置見 [R1-closure-report.md](../../../rv2_control_signal_transport/test_env/jazzy/r1-only.HmGv6E/R1-closure-report.md)。尚非新 nested pin 的正式驗收，不提前定版。
- [ ] **T14.3** Integration 以 merged clean base 原樣移入 I15/I18 ready／identity／code=10 補強，保留原場景本體與 timeout；移除僅供 legacy transport 的 local dependency。Focused I15/I18＋normal 21／I10 ASan 2、lint 及 clean-dependency 證據通過後獨立進版／PR。
  乾淨 source 58e167d、nested framework f5952a8 四步與 lint 均 PASS；dependencies 為 clean interfaces c25fcc1／mocks de847ef／transport 423ff10，無 legacy repo。Focused I15/I18 各1 PASS；無參數 `full-20260912T202647.yqG8vk` 一般19 targets／21 cases、I10 ASan2（含子程序 clean shutdown）與 controls/instrumentation/results gates 全過，零 error/failure/skip；UBSan N/A，TSan SKIP/77。Lint C/C++4／Python20 PASS。Focused 本輪初始 code0，另在同一 normal overlay 以既有 scoped shim 重建四組 code10 正反證據：原 merged-master 測試 I15 RED／I18 RED 均因舊 code0 gate FAIL/1，log 已證明 code10 後 kind7 背景成功；新測試兩組 GREEN 均 PASS/0，I15 live gen2、I18 gen2→3，原完整場景不放寬。Fixture／raw logs 位於同 owner runs/controlled.1Tkddi、i15-red.Q00ZXy、i15-green.FXHXQb、i18-red.0V8Oqx、i18-green.q6N2Ny；僅 app_a 首次 manage readiness 注入，不對 Python 全域 preload、不改 tracked source。Owner container 已卸載，logs 保留且可由使用者讀取。因新 transport／framework 尚未正式合併／導入，版本及 PR 留待 T14.2 收斂，不把此 clean candidate 充作已發布依賴。
- [x] **T14.4** 最後更新 framework README 的 rebase／pull／merged SHA／舊 tag tree 規範；必要的 R1-only 相容性實作另外 commit，不降低原 sanitizer gate。Docker 正反例／既有回歸與 lint 過後獨立版本 commit／tag／PR；等待使用者 merge 才導入。
  v0.5.1／PR #9 已推，consumer 尚未提前 pin。官方 Jazzy Docker：sanitizer unit32、packaging unit16、lint unit18、TSan toggle8、full orchestration6、T0 integration4 全 PASS；另 owner/selector/lint wrapper/sanitizer instrumentation 四套 shell PASS，含真實 ASan/UBSan clean/defect controls。Lint C/C++3／Python11／Shell14 PASS，獨立複核無 must-fix。初次 packaging 自測因誤用 Ruff venv Python 缺 yaml，改用容器 system Python 後 16 全過；兩份 log 均保留，未因此改產品。版本 commit 後 sanitizer32 再驗 PASS。證據：transport `test_env/jazzy/r1-only.HmGv6E/framework-*.log`；完整 submodule 盤點見同目錄 `submodule-audit.md`。

TSan 預設 off 不變；T12.2 仍須支援平台實測。T14 不自行合併任何 PR；project 後續版本只能納入已合併、重新 pull 核對的 releases。

**接續導入(v0.8.33)**：Framework #9 已於 2026-09-13 合併，主線 pull／release tree 證據見 transport `test_env/jazzy/r1-release.V0XQM8/`。T14.2/T14.3 的待 framework merge 前置條件已解除，以下工作完成前仍不勾選：四個 ROS repo 分開 gitlink-only 更新至 ae47906；interfaces build/無案例、mocks23/UBSan3、transport113/ASan64/UBSan72、integration21/I10ASan2 及各自 lint 全程官方 Docker、ROS jobs 全域串行。使用每包自己的 nested 入口，不沿用 override 作正式結果。Transport Debian 另核對無 legacy dependency／乾淨安裝／public export。版本欄位僅在 PR-ready 時獨立更新，舊 release tags 與原工作樹 dirty bytes 保留。Project root／workspace 的 frozen snapshot pins 不直接改写；待 component releases 與 project #1 合併再建立新 snapshot。

---

## 附錄 A:TODO 項目 ↔ 測試案例對照

| 大項 | 測試檔(§2.1) | ctest target | 案例 ID | 案例數 |
|---|---|---|---|---|
| T2 | `test/unit/test_liveness_state.cpp` | `test_liveness_state` | L1–L18 | 18 |
| T3 | `test/unit/test_info_validation.cpp` | `test_info_validation` | V1–V11 | 11 |
| T4 | `test/unit/test_transport.cpp`(suite `SourceTest`) | `test_transport` | S1–S16 | 16 |
| T5 | `test/unit/test_transport.cpp`(suite `SinkTest`) | `test_transport` | K1–K16 | 16 |
| T6 | `test/unit/test_factory.cpp` | `test_factory` | F1–F5 | 5 |
| T7 | `test/integration/test_manager.cpp` | `test_manager` | M1–M26 | 26 |
| T8 | `test/unit/test_handles.cpp`、`test/integration/test_handles_lifecycle.cpp` | `test_handles`、`test_handles_lifecycle` | H1–H8 | 8 |
| T9 | `test/integration/test_csm_master.cpp` | `test_csm_master` | CM1–CM13 | 13 |
| T10 | `r1_test_mocks/test/integration/test_mock_{manager,source_sink,master}.cpp`、`test/unit/test_status_fault.cpp` | 4 smoke targets | — | 23 |
| T11 | `r1_integration_tests/test/integration/`(launch_testing) | 19 launch targets | I1–I18(+I00 harness smoke) | 21（I08/I10 各兩案例） |

設計最低案例集合合計 154（不含 I00 與額外案例）；本輪上述 R1 targets 實際為 157 cases，加上 transport legacy 21 cases，共 178 個功能案例。T12.5 會重複執行部分 targets，不以鏈的加總冒充唯一案例數；colcon 另含 wrapper/lint records。

## 附錄 B:`todo_check.sh` item 對照

| item | 查核內容 | container 名稱 |
|---|---|---|
| `t0` | 框架 baseline(現有 package 全量 build + test) | `r1_todo_t0_jazzy` |
| `t1` | `r1_interfaces` build(msg/srv 定義,§12 #1 裁決) | `r1_todo_t1_jazzy` |
| `t2`–`t9` | 對應大項之 ctest 過濾執行(附錄 A) | `r1_todo_t2_jazzy` 等 |
| `t10` | `r1_test_mocks` build + smoke | `r1_todo_t10_jazzy` |
| `t11` | `r1_integration_tests` 全場景 | `r1_todo_t11_jazzy` |
| `t12-asan` / `t12-tsan` | transport 核心測試 + integration owner 的 I10，分別執行 | `r1_todo_t12-asan_jazzy` 等 |
| `t12-ubsan` | transport / mocks owner 的全部 unit，分別執行 | `r1_todo_t12-ubsan_jazzy` |
| `t12-pkg` | build + test + `.deb` 打包 | `r1_todo_t12-pkg_jazzy` |
