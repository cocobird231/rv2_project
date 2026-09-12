# rv2_project

RV2 專案總目錄與 ROS2 `ament_cmake` snapshot metadata package。首版 **v0.1.0**
記錄各 R1 package 的已合併 release 版本、精確 commit 及原 tag 的相同 tree。
它沒有 runtime node，也不是所有 child packages 的自動 build／測試代理。

目前 snapshot 為 development，總驗收 pending。Transport PR #8/v0.1.2 已合併，
新版 snapshot 納入它；I15/I18、T12 補強與 legacy `rv2_interfaces` 依賴移除
仍待後續 PR 收斂。完整限制見 [snapshots](snapshots/) 中 package.xml 所選版本與
[TODO](docs/r1_design_docs/r1_todo.md) §2.1。不要把 metadata 測試通過當成整體 R1 驗收。

## 取得與布局

```bash
git clone --recurse-submodules git@github.com:cocobird231/rv2_project.git
cd rv2_project
# 已 clone 的 checkout：
git submodule update --init --recursive
# 補齊既有 release tags，供離線 tag/tree 核對；不使用 --force 或 --remote：
git submodule foreach --recursive 'git fetch --tags origin'
```

`ros2_ws/src/` 保留五個 component gitlinks；根目錄 `r1_test_framework/` 是此 package
自己的測試入口，與 workspace 內的 framework 固定相同 SHA。Framework 不是 ROS package，
不寫入 ROS runtime dependencies。各 component 自己的 nested framework 維持該 release
原本的 pin；不為了 project snapshot 改寫已發布內容。

`package.xml` 是 project 版本的唯一來源，選擇 `snapshots/v<version>.json`。
完整版本對照見 [設計稿 §2.1.1](docs/r1_design_docs/r1_design_draft.md)。
文件、snapshot 與 README 安裝到 `share/rv2_project/`，可在已 source 的 ROS 環境查詢：

```bash
ros2 pkg prefix --share rv2_project
```

本 package 不引入 child packages 作為 runtime dependencies。要明確列出 project 與
nested ROS packages，可在測試 Docker／開發容器內由本目錄執行：

```bash
colcon list --paths . ros2_ws/src/*
```

此列表不等於依賴已齊備；尤其 legacy `rv2_interfaces` 尚未納入可重現 snapshot。

## 測試

所有 build、依賴安裝、測試均使用 framework 的官方 ROS Docker，host 不安裝依賴。
由本 package 根目錄執行：

```bash
./r1_test_framework/test_build.sh
./r1_test_framework/test_deps.sh
./r1_test_framework/test_run.sh
./r1_test_framework/test_clean.sh
```

無參數 `test_run.sh` 驗證 manifest unit 與真實 Git/ROS 安裝 integration，並保留
`test_env/jazzy/runs/full-*/summary.tsv`、逐案例 pytest log、JUnit XML 與 build log。
此 metadata-only package 沒有 native runtime，ASan/UBSan/TSan 均為 N/A。
TSan 預設關閉不影響其他 owners 的 T12.2 未完成事實。

PR 前獨立執行 lint：

```bash
./r1_test_framework/test_lint.sh
```

特殊情況可用 `test_run.sh -s unit` 或 `-s integration` 分開執行，兩個分類均非空。
測試 fixture 寫入容器內暫存／產物區，不改來源或自動拉取遠端。
整體 R1 總驗收需對每個 component 使用自己的 nested 四步流程與 lint，ROS jobs 全域串行，
且先解決 TODO 中的 release／依賴缺口；不得將本 package 的測試結果代替它們。

## 新增 snapshot

1. 確認各 component PR 已合併；在乾淨主線 checkout 實際 `git pull --ff-only origin master`
   （transport 使用 `r1`），再 `git fetch origin tag vX.Y.Z` 取得欲固定的原 release tag，
   核對遠端、release 版本 commit 與原 tag tree。不能用 dirty 內容
   或僅沿用合併前 SHA；不能移動既有 tag。
2. 新建 `snapshots/vX.Y.Z.json`，記錄五個 releases 的版本／SHA／tree／來源及限制；
   同步 gitlinks 與設計稿對照表。已提交 snapshot 不覆寫，版本相同亦不能偷換 commit。
3. 資料／gitlinks／文件先提交，再以只有 `package.xml` version 差異的 PR-ready 候選執行
   lint／測試；通過後以獨立版本 commit 保存該欄位變更。Snapshot 不必是 release，
   不自動附 release tag；使用者要求 release 時依 TODO §1.4 建立同名 annotated tag。

首次 v0.1.0 是使用者指定的初始化版本，不製造版本回退或空版本 commit。
未來 snapshot 可以繼續是 development／pending；通過總驗收後如何擴充認證狀態，須先更新
schema 與測試，不能自行把 pending 改為 passed。

## 文件歷史保存

原 `r1_design_docs` 歷史透過 merge 納入本 repo，舊 commits 可由 `git log --all` 查閱；
文件現在是一般 tracked files，clone 不依賴不存在的 docs remote。後續只在 project branch
修改／提交文件，仍須更新文件版本、歷史及 Agent 署名。

本次遷移的本機備份位於 `.git/migration-backups/`：

- `r1_design_docs.bundle`：原所有 refs 的完整歷史備份。
- `r1_design_docs.git/`：原 Git metadata，包含原 branches 及完整 stash reflog。
- `bootstrap.index`／`bootstrap.gitmodules`：使用者原 staged workspace。

上述備份不隨 clone 發布；可用 `git clone <bundle 的絕對路徑> <新目錄>` 回復原文件 repo，
完整 stash stack 則保留在 metadata 備份。回復時使用新的明確目錄，不覆蓋現有 project。
