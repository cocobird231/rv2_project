# rv2_project

RV2 專案總目錄與 ROS2 `ament_cmake` package，保存版本 snapshot，並提供
`test_joystick.launch.py` 組合既有 joy、bridge、server 與 master，觀察控制輸出。
首版 **v0.1.0** 記錄各 R1 package 的已合併 release 版本、精確 commit 及原 tag 的相同 tree。

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

`ros2_ws/src/` 包含八個 component gitlinks；根目錄 `r1_test_framework/` 是此 package
自己的測試入口，與 workspace 內的 framework 固定相同 SHA。Framework 不是 ROS package，
不寫入 ROS runtime dependencies。各 component 自己的 nested framework 維持該 release
原本的 pin；不為了 project snapshot 改寫已發布內容。

目前 workspace 另納入以下兩個已合併的 R1 consumers，固定合併後的 SHA；它們尚未
列入歷史 v0.1.2 snapshot。Workspace submodules 與 Unitree pre-install 已隨
PR #5 合併（`50f034b`）；本輪只補齊新環境的 rosdep 初始化，不新增 snapshot 或 project
release。`package.xml` 仍為 0.1.2，schema 1 的五個 components 與既有 JSON 均保持原內容。

| Consumer | 版本 | 固定 r1 commit | 原 release tag commit（tree 相同） |
|---|---|---|---|
| rv2_csm_topic_bridge | 0.1.0 | `78ba1a94825eb9790f23a3be5dbfb31df5162ec7` | `c3f2b4b6dc669d98552b801b5bc68858aec4da61` |
| rv2_server_control | 0.1.1 | `38cfa0f233eb1343e77b54ae97790d01171118fc` | `c3a2794e5c49c1ab35288d012db3777f273d0d32` |

`joy_interpreter` 也納入 submodule，固定 server 已驗證的 `test` 分支
`944306b61746dcdaa932a404994b8f829a2a9611`（package 0.1.0，沒有對應 release tag）。
此版本提供 server 使用的 `update(joy, now)`；目前 master 的單參數 API 不相容。
Unitree sources 位於 server 的 `thirdparty/unitree/`，不再需要外部 API checkout 或 symlink。
`test_depends.repos` 直接列出 interfaces、transport、bridge、server、joy_interpreter 與
server 內附的 `unitree_api`；framework 不遞迴讀取 child 的依賴清單。

## 預先安裝 Unitree

先安裝 colcon 與 rosdep，並 source ROS 2；rosdep 的首次初始化由腳本處理。
由 project 根目錄執行：

```bash
source /opt/ros/jazzy/setup.bash
./pre_install.sh --dry-run
./pre_install.sh && source "pre_install/${ROS_DISTRO}/install/setup.bash"
```

腳本固定從目前 server submodule 的內附 sources 建置 `unitree_api`、`unitree_go`、
`unitree_hg` 三包，明確指定套件路徑以跨過 nested package 的 discovery 邊界。
它優先沿用目前使用者已有的 rosdep cache。缺少 cache 時才檢查 sources：已有
任一 `*.list` 就直接更新；沒有 sources list 才執行 `rosdep init`（非 root 透過
sudo）。之後以目前使用者執行 `rosdep update --rosdistro "$ROS_DISTRO"` 建立 cache；
已有 cache 時不重新初始化或更新，即使 sources list 不存在也可沿用。
接著以 rosdep 安裝目前 ROS 環境所需的 build/runtime dependencies，再用 colcon
建立獨立的 merged underlay；上游 tests 不在此安裝流程執行。
初始化、cache 更新、依賴安裝或編譯任一步失敗，腳本立即停止；範例以 `&&` 確保
只在安裝成功後 source，避免使用先前殘留或不完整的產物。
Unitree 產物預設位於 `pre_install/<ROS_DISTRO>/{build,install,log}`，BSD LICENSE
隨每包安裝，完成後列出 `source` 指令。重新執行會沿用該處建置產物。

`--dry-run` 只顯示命令，不建立產物或執行安裝。腳本也可從其他 cwd 呼叫；自訂
`--output-dir DIR` 的相對路徑以呼叫端 cwd 為準，例如：

```bash
/path/to/rv2_project/pre_install.sh --output-dir /work/unitree-underlay && \
  source /work/unitree-underlay/install/setup.bash
```

腳本不修改 shell 設定；下一個 terminal 仍需 source 此 underlay。
rosdep 初始化 sources 或安裝系統依賴時可能要求 sudo；cache 更新使用目前帳號，
請勿對整支腳本或 `rosdep update` 加 sudo。若初始化因網路或權限失敗，先處理錯誤再重跑。
需要手動處理時，可在尚未建立 sources 的環境執行 `sudo rosdep init`，成功後以目前帳號
執行 `rosdep update --rosdistro "$ROS_DISTRO"`；已有 sources 時直接執行後者。
本專案的 agent 驗證全在官方 ROS Docker 中執行，host 不安裝依賴。
`pre_install.sh` 是 source checkout 的建置入口，不安裝至 `share/rv2_project`；一般
framework 四步測試會直接掛載內附 API，不需事先在 host 執行此腳本。

`package.xml` 是 project 版本的唯一來源，選擇 `snapshots/v<version>.json`。
完整版本對照見 [設計稿 §2.1.1](docs/r1_design_docs/r1_design_draft.md)。
文件、snapshot、README 與 `launch/` 安裝到 `share/rv2_project/`，可在已 source 的 ROS 環境查詢：

```bash
ros2 pkg prefix --share rv2_project
```

本 package 宣告 launch 使用的 child runtime dependencies。要明確列出 project 與
nested ROS packages，可在測試 Docker／開發容器內由本目錄執行：

```bash
colcon list --paths . ros2_ws/src/*
```

v0.1.2 的 R1-only 來源不再依賴 legacy `rv2_interfaces`。此列表不會安裝外部 ROS／apt
依賴，也不等於完整執行環境已鎖版。

## 實機 joystick 操作

完成上述 pre-install 並 source Unitree underlay、準備其他 ROS dependencies 後，
可在 ROS 開發容器由 project 根目錄建置。
明確選用這裡固定的 R1 sources，避免混入外層 workspace 的 legacy checkout：

```bash
colcon build --paths . ros2_ws/src/* --packages-up-to rv2_project
source install/setup.bash
```

在已安裝上述 packages、source 對應 `install/setup.bash` 且可存取 joystick 的 ROS 環境執行：

```bash
ros2 launch rv2_project test_joystick.launch.py
```

預設啟動 `joy_node`（20 Hz autorepeat）、Joy bridge、control server、一個獨立 master，
以及 `ros2 topic echo /api/sport/request unitree_api/msg/Request`。
Echo 只訂閱 request，不模擬機器人、不發布 response。Server launch 的內建 master 已關閉。

查參數或選擇裝置：

```bash
ros2 launch rv2_project test_joystick.launch.py --show-args
ros2 run joy joy_enumerate_devices
ros2 launch rv2_project test_joystick.launch.py device_id:=1
ros2 launch rv2_project test_joystick.launch.py device_name:="裝置的完整 SDL 名稱"
```

`device_name` 非空時優先於 `device_id`。`start_joy`、`start_bridge`、`start_server`、
`start_master`、`observe_requests` 預設皆為 `true`，可個別設為 `false`。
已有 master 時用 `start_master:=false`；只需 server 自己的輸出 log 時用
`observe_requests:=false`。`joy_topic` 預設 `/joy`；`server_name`、`master_name`、
`bridge_name` 預設分別為 `control_server`、`csm_master`、`topic_bridge`。
自訂 YAML 使用 `bridge_config_file:=/absolute/path/bridge.yaml` 與
`server_config_file:=/absolute/path/server.yaml`；上述 launch 名稱與 Joy topic/type 會覆寫 YAML。

以下三組分開執行，每組用兩個 terminal。先確認非零搖桿輸入產生 API **1008**（Move，
`x/y/z` 對應 axes 0/1/3），再對 terminal B 按 Ctrl+C，等待後以原命令重啟。

Joy 程序停止／恢復：

```bash
# Terminal A
ros2 launch rv2_project test_joystick.launch.py start_joy:=false
# Terminal B
ros2 run joy joy_node --ros-args -p autorepeat_rate:=20.0
```

Bridge 停止／恢復：

```bash
# Terminal A
ros2 launch rv2_project test_joystick.launch.py start_bridge:=false
# Terminal B
ros2 launch rv2_csm_topic_bridge topic_bridge.launch.py topic_name:=/joy msg_type:=joy
```

Server 遲啟動／重啟（保留 terminal A 的 master）：

```bash
# Terminal A
ros2 launch rv2_project test_joystick.launch.py start_server:=false
# Terminal B
ros2 launch rv2_server_control control_server.launch.py start_master:=false
```

使用預設設定時，停止 Joy 輸入超過 `timeout_ms=2000` 應觸發一次 API **1003**
（StopMove）；持續失聯不反覆發送。`disconnect_timeout_ms=10000` 從最後資料計算，
超過後移除註冊；恢復新輸入應重新註冊，保持與中斷前相同的非零值仍應再次輸出 Move。
Bridge 停止也應讓仍在執行的 server 停止輸出；server 本身停止期間沒有程序可以發 StopMove，
重啟後觀察 master 對帳及新輸入恢復。需要時另開 terminal：

```bash
ros2 topic echo /topic_bridge/status r1_interfaces/msg/ManagerStatus
ros2 topic echo /control_server/status r1_interfaces/msg/ManagerStatus
```

拔除／插回 joystick 另做一次；部分 driver 拔除後仍送 neutral samples，此時應以
driver log 判斷實體斷線，不能只期待 transport TIMEOUT；未自動重開裝置時重啟 joy node。
Bridge mailbox 只保留最新 pending sample，註冊／service 等待期間的短按可能被後續訊息覆蓋，
包含 R2（axes 5，小於 0.5 為急停）與 buttons；此路徑不保證保留每個按鍵邊緣。
實機、裝置 mapping 與 hotplug 驗收仍由使用者執行。

## 測試

所有 build、依賴安裝、測試均使用 framework 的官方 ROS Docker，host 不安裝依賴。
由本 package 根目錄執行：

```bash
./r1_test_framework/test_build.sh
./r1_test_framework/test_deps.sh
./r1_test_framework/test_run.sh
./r1_test_framework/test_clean.sh
```

無參數 `test_run.sh` 建置 project 的 runtime dependency closure，驗證 manifest unit、
真實 Git/ROS 安裝 integration、pre-install 三包建置／重跑／安裝後 import 與下游編譯，
以及從 installed project launch 啟動的組合測試。
組合測試在 Docker 內以合成 Joy 驗證輸出、輸入停止與同值恢復；它不替代實機驗收。
流程只執行 project 的測試，不代替各 child owner 的完整測試，並保留
`test_env/jazzy/runs/full-*/summary.tsv`、逐案例 pytest log、JUnit XML 與 build log。
Project 沒有自有 native runtime，framework 未為此 owner 定義 sanitizer profile，
ASan/UBSan/TSan 均為 N/A；這不表示 launch 內的 child runtime 已通過 sanitizer。
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
