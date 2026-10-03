# rv2_project

RV2 專案總目錄與 ROS2 `ament_cmake` snapshot metadata package。首版 **v0.1.0**
記錄各 R1 package 的已合併 release 版本、精確 commit 及原 tag 的相同 tree。
它沒有 runtime node，也不是所有 child packages 的自動 build／測試代理。

最新 snapshot **v0.1.2** 納入已合併 framework v0.5.1、interfaces/mocks/integration
v0.1.2 與 R1-only transport v0.2.0；I15/I18、T12/export 補強及 legacy 依賴移除均已收錄。
舊 v0.1.0/v0.1.1 保持原內容。Snapshot 仍為 development／acceptance pending，
總驗收由使用者手動逐包執行；TSan 因環境限制本次暫時 SKIP，不算 PASS，
也不阻擋其餘項目驗收。Docker image／外部 apt 依賴仍未鎖定為不可變版本。
完整限制見 [snapshots](snapshots/) 中 package.xml 所選版本與
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

`ros2_ws/src/` 包含七個 component gitlinks；根目錄 `r1_test_framework/` 是此 package
自己的測試入口，與 workspace 內的 framework 固定相同 SHA。Framework 不是 ROS package，
不寫入 ROS runtime dependencies。各 component 自己的 nested framework 維持該 release
原本的 pin；不為了 project snapshot 改寫已發布內容。

目前 workspace 另納入以下兩個已合併的 R1 consumers，固定合併後的 SHA；它們尚未
列入歷史 v0.1.2 snapshot。本次只更新 workspace submodules，不新增 snapshot 或 project
release；`package.xml` 仍為 0.1.2，schema 1 的五個 components 與既有 JSON 均保持原內容。

| Consumer | 版本 | 固定 r1 commit | 原 v0.1.0 tag commit（tree 相同） |
|---|---|---|---|
| rv2_csm_topic_bridge | 0.1.0 | `78ba1a94825eb9790f23a3be5dbfb31df5162ec7` | `c3f2b4b6dc669d98552b801b5bc68858aec4da61` |
| rv2_server_control | 0.1.0 | `ae457eacd3f0e56e6cec53fec2c7b61773d52f6b` | `d8921b2123ff9c3216e35718047329d1ef1308c9` |

Server 的來源依賴還需要在 `ros2_ws/src/` 準備 `joy_interpreter`（已驗證 `test` 分支
`944306b61746dcdaa932a404994b8f829a2a9611`）及 `unitree_api`（官方 `unitree_ros2`
`5204e6e098ee53f4bd929bd77eb1d387cd0fa842` 的 `cyclonedds_ws/src/unitree/unitree_api`，
可用 symlink）。這兩個外部來源不是本 project 的 submodules；recursive clone 後仍須
準備，才能建置 server 或執行其 nested 測試。具體布局見
[server 建置依賴](ros2_ws/src/rv2_server_control/README.md#建置依賴)，不需整個 Unitree workspace。

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

v0.1.2 的 R1-only 來源不再依賴 legacy `rv2_interfaces`。此列表不會安裝外部 ROS／apt
依賴，也不等於完整執行環境已鎖版。

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
目前 workspace 的兩個額外 consumers 也驗證 gitlink、checkout、原 tag tree、版本、remote
與 nested framework；這些檢查不擴充歷史 snapshot 的 schema。
其他 owners 的 T12.2 本次依使用者裁決暫時 SKIP；未取得 TSan 無 race 證據，
未來支援平台仍須明確 `-t on` 驗證。

PR 前獨立執行 lint：

```bash
./r1_test_framework/test_lint.sh
```

特殊情況可用 `test_run.sh -s unit` 或 `-s integration` 分開執行，兩個分類均非空。
測試 fixture 寫入容器內暫存／產物區，不改來源或自動拉取遠端。
整體 R1 總驗收由使用者對精確 snapshot 的每個 ROS component 使用自己的 nested
四步流程與 lint，ROS jobs 全域串行；不得將本 package 的測試結果代替它們。

本次手動驗收的 ROS component 目錄為 `ros2_ws/src/r1_interfaces/`、
`ros2_ws/src/r1_test_mocks/`、`ros2_ws/src/rv2_control_signal_transport/` 與
`ros2_ws/src/r1_integration_tests/`；新增 consumers 為
`ros2_ws/src/rv2_csm_topic_bridge/`、`ros2_ws/src/rv2_server_control/`。
準備好各包 source dependencies 後，逐一切入目錄執行上述四步與獨立 lint。
Framework 本身不是 ROS package，其自測方式見 workspace framework README；
不要對它套用 ROS owner 的四步流程。自動逐包執行腳本暫不新增。

請保留各 owner 的 `test_env/jazzy/runs/full-*/summary.tsv`、`execution.log`，
以及摘要指向的 profile build、逐案例 log／JUnit XML；另保留四步 exit codes 與獨立 lint log。
回報時附 source/framework SHA，區分 PASS、FAIL、SKIP、N/A。Interfaces 無 executable
測項，TSan 預設 SKIP/77 與工具原生 SKIP 不算 PASS；任何已啟用階段失敗仍須處理。
收到手動結果前，總驗收保持 pending；本次豁免記錄不回寫已發布 snapshot JSON。

## 打包與測試分工

`test_run.sh` 跑測試，`test_packages.sh` 打包 `.deb`，兩者保持獨立。
目前各 owner 的打包流程是 `test_build.sh` → `test_deps.sh` → `test_packages.sh`
→ `test_clean.sh`，不必先跑 test_run；PR 的測試與 lint gates 仍須另外完成。
打包使用 nocheck，不執行 unit/integration；現有流程另建乾淨容器驗證 deb 安裝，
transport 額外驗公開 headers、下游連結及 node 啟停，這不等同完整功能測試。

`.deb` 格式不要求 Docker，但現行 framework 強制 Docker 隔離，尚無 host backend。
「一個指令自動管理短生命週期容器」與「完全不用 Docker、自備 host 編譯環境」
是不同選項，目前僅討論、尚未實作；詳見[設計稿 §11.5.3](docs/r1_design_docs/r1_design_draft.md)。

## 新增 snapshot

1. 確認各 component PR 已合併；在乾淨主線 checkout 實際 `git pull --ff-only origin master`
   （transport／bridge／server 使用 `r1`），再 `git fetch origin tag vX.Y.Z` 取得欲固定的原 release tag，
   核對遠端、release 版本 commit 與原 tag tree。不能用 dirty 內容
   或僅沿用合併前 SHA；不能移動既有 tag。
2. 新建 `snapshots/vX.Y.Z.json`，記錄五個 releases 的版本／SHA／tree／來源及限制；
   同步 gitlinks 與設計稿對照表。已提交 snapshot 不覆寫，版本相同亦不能偷換 commit。
   若要把 bridge／server 納入版本 snapshot，須先升級 schema 及相容測試；不可直接向
   schema 1 加入 component，亦不可把目前 workspace 組合當成已發布的 v0.1.2 snapshot。
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
