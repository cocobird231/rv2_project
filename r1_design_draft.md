# R1 Control Signal Transport 程式設計規劃書(草稿 v0.5.1)

> 狀態:初版草稿,供討論。未決事項集中在第 11 章。
> 位置:先實作於本 repo(`rv2_control_signal_transport`)的 `r1` namespace 下,後續 migrate 至獨立 package。
> 版控:草稿以 git 管理,每次修訂一個 commit,版本號記於本節與 §0 版本歷史。

## 0. 版本歷史

| 版本 | 摘要 |
|---|---|
| v0.1.0 | 初版:設計概念、主架構、7 類別章節、整合測試規劃;經一輪 adversarial review 修正 |
| v0.2.0 | 依 my_note.md:UNKNOWN 改名 INITIAL(查無 entry 語意改以 `std::optional` 表達);新增 §4.6 tinyFSM 評估(結論:不採用,維持自製 CAS 狀態機) |
| v0.3.0 | 依 my_note.md(RAII、Sink timeout/disconnect 設計):RAII 總則(§1.5);DISCONNECTED 改為可重連休眠態,新增 → INITIAL 轉移(§2.3/§4);heartbeat 升級為雙向 **ManagerStatus** 狀態發布、Manager 單一 timer(§2.5);Sink 內建 data-rate 統計、收訊先記錄再 dispatch(§6);callback API 改為 `registerCallback`(字串鍵 + template 雙層,§8);整合場景與未決事項更新 |
| v0.4.0 | 依 my_note.md(並發原則、Source/Sink/CSM design detail):並發原則 §1.6(atomic 優先、shared_mutex 讀寫分離);**Source 對稱 rate 統計**(send 記錄呼叫時間/次數);rate **記錄(hot path)與計算(CSM tick 驅動之非公開 `_calcRate()`,friend)分離**,per-entity 狀態快取;Sink 新增 **`waitForMessage()`** 阻塞等待 API(condition variable + 序號);`ControlSignalManage.srv` 增 **NOTIFY_ABNORMAL** op,異常狀態邊緣觸發主動通報對向 CSM |
| v0.5.1 | 依 my_note.md 文件撰寫準則:全文文風修訂——移除口語與比喻用語(改以標準技術術語敘述)、消除過度精簡的語句、統一測試場景命名;內容與設計無變更 |
| v0.5.0 | 依 my_note.md(FSM #4/#5、timeout 機制、CSM Master):**timeout 改雙獨立閾值**(同一 elapsed 比 `timeout_ns` 與 `disconnect_timeout_ns`,皆可 0 = 停用;四種 FSM 變體圖 §2.3.1);**per-state 轉移 callback**(entity 層 + CSM 註冊 API);rolling window **大小可配置**(N-bucket 環形);`getStatus()` 整合查詢;**CSM Master 集中式通知架構**(新 §9)取代 v0.3.0 互訂 status link 與 v0.4.0 點對點 NOTIFY_ABNORMAL——CSM 向 master 註冊 + heartbeat,master 訂閱各 CSM status、以 controller_name 配對 Source-Sink、one-shot 通知 `/<csm_name>/get_notifications` |

---

## 1. 設計概念

### 1.1 目標

由 `rv2_control_signal_transport` 改寫,保留 Source / Sink / Manager 三角架構,但:

1. **精簡參數與功能** — 移除未被狀態機使用的欄位、合併重疊機制、縮減狀態數。
2. **Manager 全權管理** — 使用者「不能」直接建構 Source/Sink;唯一入口是
   `ControlSignalManager::registerSource(info)`。Manager 驗證後自動向 target
   manager 發出 request,在對方產生對應 Sink。使用者拿到的是 **Handle**(弱引用),
   不是物件本體,從介面層防止錯誤使用與生命週期缺陷。
3. **並發正確性內建於設計** — rv2 並發稽核(2026-08 audit)確認 20 項問題,
   r1 逐項以架構手段消除,而非事後補丁。
4. **RAII 貫穿所有元件**(my_note 總則)— 資源(rclcpp entities、狀態、map entries)
   一律「建構取得、解構釋放」,詳 §1.5。

### 1.2 與 rv2 的差異總表

| 面向 | rv2 | r1 |
|---|---|---|
| 使用者建構 Source/Sink | 可直接 `new`(測試中大量使用) | **禁止**;建構子 private,只有 Manager(經 Factory)可建 |
| 使用者持有物件 | `getSource()` 回傳 `shared_ptr`(物件殘留與 use-after-free 風險) | 回傳 `SourceHandle`/`SinkHandle`(內部 `weak_ptr`) |
| 狀態機 | 5 態(UNKNOWN/ACTIVE/LOW_FREQ/TIMEOUT/DISCONNECTED),轉移散落各處、relaxed atomics、可被覆寫 | **4 態**(INITIAL/ACTIVE/TIMEOUT/DISCONNECTED;移除 LOW_FREQ、UNKNOWN 改名 INITIAL);集中於 `LivenessState` 類,CAS 轉移表;DISCONNECTED 為**休眠態**,重連 → INITIAL(v0.3.0,§2.3) |
| 斷線後 entry | DISCONNECTED 即 erase(不穩定連線反覆 add/remove) | entry **保留**於 DISCONNECTED,重連自動復原;僅顯式 unregister / 解構移除(§2.5) |
| Keep-alive | 每個 channel 一條 `_keep_alive` topic + 每個 Sink 一個 timer | **雙向 ManagerStatus 發布**:每個 Manager 一條 `<name>/status` topic(含管理清單與各 entry 狀態),互為 link liveness 依據(§2.5) |
| 頻率監控 | `send_freq_hz` 宣告值 + LOW_FREQ 推導(從未驅動決策) | **Source/Sink 對稱實測 rate**(v0.4.0):hot path 只記錄(時間+次數),計算集中於 CSM tick 呼叫的非公開 `_calcRate()`;隨 status 發布(§5/§6) |
| 讀取模式 | `read()` 輪詢 | `read()` 輪詢 + **`waitForMessage()` 阻塞等待**(condition variable,§6) |
| 異常傳遞 | 無(各側獨立判定,對向不知情) | **CSM Master 集中式**(v0.5.0,§9):master 訂閱各 CSM status、配對 Source-Sink、狀態變化 one-shot 通知雙方 CSM;CSM 之間不互訂、不直發 |
| Timeout 語意 | TIMEOUT 持續逾 `disconnect_timeout_ns` 才斷線(疊加計時) | **雙獨立閾值**(v0.5.0):同一 elapsed 比對兩閾值,`0` = 各自停用;四種 FSM 變體(§2.3.1) |
| 狀態變化觀測 | 輪詢 `getState()` | 輪詢 + **per-state 轉移 callback**(entity 層註冊,CSM 亦提供 per-state 註冊 API,§5/§6/§8) |
| Sink callback API | `setSinkMsgCallback<msgT>(cb)`(type_index 鍵) | `registerCallback` 雙層:template 型別安全版 + 字串鍵型別抹除版;鍵統一為 type 字串(§8) |
| RAII | shutdown 語意混雜、解構不保證釋放順序 | 全元件 RAII(§1.5):解構即完整釋放;Manager 解構自動 best-effort 反註冊 |
| 註冊協定 | 單向一次性;TOCTOU、無 rollback、無 unregister | **兩階段(佔位 → 確認)** + 失敗 rollback + 顯式 `unregisterSource()` |
| ControlSignalInfo | 12 欄位、9 條驗證規則 | **8 欄位、5 條規則**(§3) |
| callback lambda | 捕獲裸 `this` | 一律捕獲 `weak_ptr`(`enable_shared_from_this`) |
| Callback group | 全部落在 node 預設 MutuallyExclusive group(未文件化) | 明確策略:Manager 服務使用專屬 Reentrant group;文件化限制(§2.6) |
| 逾時檢查 | 被動 lazy + 多處觸發 | 被動 lazy 保留,但唯一寫入路徑經 `LivenessState`(§4) |
| map 鍵 | `controller_name`(2026-08 改) | 同,`controller_name` 為主鍵;`channel_name` 同樣唯一 |

### 1.3 rv2 稽核教訓 → r1 對策

| rv2 問題(嚴重度) | r1 對策 |
|---|---|
| `registerSource` TOCTOU、`operator[]` 靜默覆蓋(🔴) | 兩階段註冊:先插入 PENDING 佔位(原子佔用兩個鍵),遠端確認後轉正;任何插入路徑禁止 `operator[]`,一律 `emplace` + 檢查 |
| 裸 `this` 捕獲 → UAF(🔴) | `enable_shared_from_this` + lambda 捕獲 `weak_ptr`,callback 先 `lock()` 失敗即 return |
| stale TIMEOUT/LOW_FREQ 蓋掉新 ACTIVE、無法自癒(🟡) | `LivenessState::checkTimeout()` 以 `compare_exchange` 帶 epoch 檢查;活動時間戳與狀態同字打包(§4) |
| relaxed ordering 可見性(🟡) | `LivenessState` 內統一 acq/rel;外界只透過其 API 存取 |
| DISCONNECTED 非真終態(🟡) | 轉移表強制:DISCONNECTED 無出邊;`reportActivity()` 對 DISCONNECTED 回 false |
| 分散式註冊非原子、孤兒 Sink 永久佔位(🟡) | rollback:本地失敗時發 best-effort UNREGISTER;Sink 側 PENDING 有 TTL,未收到首筆資料/確認逾時自動回收 |
| Sink 自 map 移除後仍持續發送心跳(🟡) | 使用者無法持有 `shared_ptr`;Manager 移除時立即 `shutdown()`(釋放 rclcpp entities),heartbeat 與 subscription 隨之停止 |
| 同 node callback 內呼叫 `send()`/`registerSource()` 必然 false-timeout(🟡) | Manager 服務/client 用專屬 Reentrant group;`registerSource` 文件化為「禁止在任何 callback 內呼叫」+ debug assert |
| debug log 無鎖讀 map(🟡 UB) | log 在鎖內取 snapshot |
| `_onReg` 之尚未觸發的 TOCTOU(⚪) | 同兩階段插入,結構性消除 |

### 1.4 所有權與生命週期模型

```
ControlSignalManager ──(唯一擁有 shared_ptr)──► Source / Sink 實體
        │                                              ▲
        │ registerSource() 回傳                        │ weak_ptr
        ▼                                              │
   SourceHandle ───────────────────────────────────────┘
```

- Manager 是唯一 owner。**移除**(unregister、解構;v0.3.0 起 auto-disconnect 不再移除,見 §2.5)時:
  1. `endpoint->shutdown()`:重置 rclcpp entities(pub/sub/client/service)→ 不再有新 callback 排入。
  2. 從 map erase → `shared_ptr` 釋放。
  3. in-flight callback 因 `weak_ptr::lock()` 失敗直接返回 → 無 UAF。
- Handle 失效後所有操作回傳 error code(不丟例外)。

### 1.5 RAII 原則(v0.3.0,my_note 總則)

全部元件遵守「建構取得、解構釋放」:

| 元件 | 建構取得 | 解構釋放 |
|---|---|---|
| Source / Sink | rclcpp transport entities、LivenessState | entities 重置(等效 `shutdown()`;`shutdown()` 僅為提前釋放的冪等捷徑,解構為最終保障) |
| Manager | 服務、status pub、timer、callback group | 依序:timer → 服務 → 對所有 ACTIVE Source 發 **best-effort UNREGISTER**(通知 targets)→ 釋放全部 entries |
| LinkMonitor | heartbeat 訂閱 | 訂閱釋放(controllers 集合空時即時解構,§8.3) |
| Handle | 無資源(weak_ptr + 字串) | 無 |

- 禁止裸 `new`/手動 delete;一律 `std::shared_ptr`/`std::unique_ptr`/值語意。
- 不依賴使用者呼叫任何 cleanup API:忘記 unregister、直接讓 Manager 出 scope,
  也不留下 dangling rclcpp entities 或遠端孤兒 entry(best-effort 通知為主,
  遠端 TTL 與休眠機制為最終保障)。

### 1.6 並發原則(v0.4.0,my_note 總則)

所有 flag 與並發變數依「最輕量足夠」原則選工具,由輕至重:

| 工具 | 適用 | 本設計應用點 |
|---|---|---|
| `std::atomic`(單變數) | 獨立 flag、計數器、快取值 | `shutdown_` flag、rate bucket 計數、cached `rateHz_`(atomic\<float\>)、訊息序號 `msgSeq_` |
| CAS 複合字(§4.2) | 多欄位一致轉移 | `LivenessState` 的 state+epoch |
| `std::shared_mutex` | **讀多寫少**共享結構 | CSM `sources_`/`sinks_` map(讀:狀態查詢、status tick、getXxx;寫:register/unregister)、黑白名單、`typedCbs_` callback 表 |
| `std::mutex` + condition variable | 寫頻繁 / 需等待語意 | Sink `msgMtx_`(每訊息寫)+ `msgCv_`(`waitForMessage`,§6) |

- 規則:atomic 能表達就不用鎖;讀路徑遠多於寫路徑才用 `shared_mutex`
  (`std::shared_lock` 讀 / `std::unique_lock` 寫),否則普通 mutex 更省;
  持鎖區塊最小化,callback 一律鎖外呼叫(承襲 rv2 驗證過的模式)。
- 每個成員變數在類別章節中標注其保護手段;無標注 = 建構後唯讀。

---

## 2. 程式主架構

### 2.1 Namespace 與檔案布局

Namespace:`rv2_interfaces::r1`(migrate 後改 `r1_control_signal_transport`;程式內以巢狀 `r1` 隔離)。

```
include/rv2_control_signal_transport/r1/
    control_signal_info.h      # Info 別名 + validateControlSignalInfo()
    liveness_state.h           # LivenessState(純邏輯,無 ROS 依賴)
    control_signal_source.h    # BaseControlSignalSource + ControlSignalSource<msgT, srvT>
    control_signal_sink.h      # BaseControlSignalSink + ControlSignalSink<msgT, srvT>
    control_signal_factory.h   # ControlSignalFactory + R1_REGISTER_CONTROL_SIGNAL
    control_signal_handles.h   # SourceHandle / SinkHandle
    control_signal_manager.h   # ControlSignalManager
src/r1/
    control_signal_factory.cpp # Factory singleton 定義(shared library 單一定義)
    control_signal_types.cpp   # 具體型別註冊(Joy / Twist / String)
test/r1/
    r1_test_utils.h
    test_liveness_state.cpp    # 純邏輯,無 rclcpp
    test_info_validation.cpp   # 純邏輯,無 rclcpp
    test_factory.cpp
    test_transport.cpp         # Source/Sink(經 Manager 之 friend 測試通道)
    test_manager.cpp           # 跨 CSM 協定
```

介面定義(暫置 `rv2_interfaces`,migrate 時搬移):

```
rv2_interfaces/msg/r1/ControlSignalInfo.msg
rv2_interfaces/msg/r1/ManagerStatus.msg          # 狀態發布;訂閱者 = CSM Master(§2.5.1)
rv2_interfaces/msg/r1/EntryStatus.msg            # 含 manager_name(v0.5.0,master 配對/通知用)
rv2_interfaces/srv/r1/ControlSignalManage.srv    # op = REGISTER | UNREGISTER(v0.5.0 移除 NOTIFY_ABNORMAL)
rv2_interfaces/srv/r1/ControlSignalInfoReq.srv
rv2_interfaces/srv/r1/CsmRegister.srv            # CSM → master 註冊(v0.5.0)
rv2_interfaces/srv/r1/CsmNotify.srv              # master → CSM 狀態變化通知(v0.5.0)
# master heartbeat 用 std_srvs/srv/Trigger,不另定義
```

新增執行檔(v0.5.0):`csm_master_node`(獨立 node,host `r1::CsmMaster`,§9)。

```
src/r1/csm_master.cpp / include/rv2_control_signal_transport/r1/csm_master.h
```

### 2.2 元件關係圖

```mermaid
graph TB
    subgraph NodeA["Node A(Source 側)"]
        MA["r1::ControlSignalManager A"]
        SRC["r1::ControlSignalSource"]
        HA["SourceHandle(使用者)"]
        MA -->|owns| SRC
        HA -.weak.-> SRC
    end
    subgraph NodeB["Node B(Sink 側)"]
        MB["r1::ControlSignalManager B"]
        SNK["r1::ControlSignalSink"]
        HB["SinkHandle(使用者)"]
        MB -->|owns| SNK
        HB -.weak.-> SNK
    end
    MA -->|"① manage(REGISTER)"| MB
    SRC -->|"data: channel_name"| SNK
    subgraph Master["CSM Master 節點(v0.5.0,§9)"]
        CM["r1::CsmMaster"]
    end
    MA -->|"register + heartbeat(Trigger)"| CM
    MB -->|"register + heartbeat(Trigger)"| CM
    MA -->|"status: mgrA/status"| CM
    MB -->|"status: mgrB/status"| CM
    CM -->|"get_notifications(狀態變化 one-shot)"| MA
    CM -->|"get_notifications"| MB
    F["r1::ControlSignalFactory(singleton)"]
    MA -.creates via.-> F
    MB -.creates via.-> F
```

- v0.5.0 起 **CSM 之間不互訂 status**;status 唯一訂閱者為 CSM Master。
  CSM 間僅存的直接通訊 = 註冊協定(`control_signal_manage`,§2.4)與資料通道本身。

### 2.3 狀態機(4 態)

```mermaid
stateDiagram-v2
    [*] --> INITIAL : 建立
    INITIAL --> ACTIVE : reportActivity()
    INITIAL --> TIMEOUT : checkTimeout() elapsed > timeout_ns
    ACTIVE --> TIMEOUT : checkTimeout() elapsed > timeout_ns
    TIMEOUT --> ACTIVE : reportActivity()
    TIMEOUT --> DISCONNECTED : checkTimeout() elapsed > disconnect_timeout_ns
    INITIAL --> DISCONNECTED : disconnect()(forced)
    ACTIVE --> DISCONNECTED : disconnect()(forced)
    TIMEOUT --> DISCONNECTED : disconnect()(forced)
    DISCONNECTED --> INITIAL : reportActivity()(重連,v0.3.0)
    DISCONNECTED --> [*] : unregister / 解構
```

- 移除 LOW_FREQ:rv2 中它由 `timeout_ns/2` 寫死推導、不影響任何決策,只增加狀態機複雜度。
  頻率監控若有需求,由上層以 `lastActivityNs()` 自行判讀(§4 提供查詢)。
- UNKNOWN 改名 **INITIAL**(v0.2.0):物件建構後、首次活動前的狀態,我們**確知**其意義,
  「UNKNOWN」名不符實。rv2 另有雙重語意問題——`getSourceState()` 查無 entry 也回 UNKNOWN,
  與初始態混淆;r1 拆開:enum 用 INITIAL,查詢 API 以 `std::optional`(nullopt = 查無)表達(§8.2)。
  轉移語意不變:INITIAL 完整繼承原 UNKNOWN 的三條出邊。
- **雙獨立閾值 timeout**(v0.5.0,my_note Timeout Mechanism):同一 `elapsed = now − lastActivity`
  比對兩個閾值——`elapsed > timeout_ns` → TIMEOUT(data-rate timeout);
  `elapsed > disconnect_timeout_ns` → DISCONNECTED(disconnect timeout,優先判定)。
  取代 rv2 / v0.4.0 之前的「TIMEOUT **持續**超過 disconnect_timeout 才斷線」疊加計時——
  CSM 不再需要 per-entity 追蹤 TIMEOUT 起始時間,判定全部內聚於 `LivenessState::checkTimeout()`。
  兩閾值皆支援 **`0` = 停用**(§2.3.1 變體);皆啟用時仍要求 `disconnect > timeout`(§3.2)。
- 「forced disconnect」(my_note Timeout #4):`disconnect()` API 為獨立轉移來源
  (CSM 管理決策、使用者強制),與閾值機制並存;所有變體皆保留此邊。
- DISCONNECTED 改為**休眠態**(v0.3.0,my_note FSM #3):不再是無出邊終態。
  重連(收到活動)→ 回 **INITIAL**(本次活動記入 lastActivity;後續活動才轉 ACTIVE,
  讓不穩定連線需「連續」活動才回到 ACTIVE)。entry 不因斷線被移除——
  不穩定連線在 TIMEOUT/DISCONNECTED/INITIAL 之間反覆轉換,map entry 常駐,
  避免 rv2 的頻繁 add/remove(含跨 CSM 重新註冊)開銷與識別鍵競爭。
  移除只發生於顯式 `unregisterSource()` 或 Manager 解構。
  上層仲裁(如 ControlServer)視 DISCONNECTED sink 為不可選——效果等同 rv2 的移除,但可自癒。

#### 2.3.1 Timeout 停用之 FSM 變體(v0.5.0,my_note Timeout #3)

兩閾值各自可為 `0`(停用),共四種組態;`disconnect()`(forced)與重連邊全變體保留。

**變體 A — 兩者啟用**(`timeout_ns > 0, disconnect_timeout_ns > 0`):上圖(完整)。

**變體 B — disconnect 停用**(`timeout_ns > 0, disconnect_timeout_ns = 0`):
無自動 DISCONNECTED;最深自動狀態為 TIMEOUT。

```mermaid
stateDiagram-v2
    [*] --> INITIAL
    INITIAL --> ACTIVE : reportActivity()
    INITIAL --> TIMEOUT : elapsed > timeout_ns
    ACTIVE --> TIMEOUT : elapsed > timeout_ns
    TIMEOUT --> ACTIVE : reportActivity()
    INITIAL --> DISCONNECTED : disconnect()(forced)
    ACTIVE --> DISCONNECTED : disconnect()(forced)
    TIMEOUT --> DISCONNECTED : disconnect()(forced)
    DISCONNECTED --> INITIAL : reportActivity()(重連)
```

**變體 C — data-rate timeout 停用**(`timeout_ns = 0, disconnect_timeout_ns > 0`):
TIMEOUT 態不可達;elapsed 超過 disconnect 閾值直接休眠(適合「只要最終斷線判定、
不需中間警示」的通道)。

```mermaid
stateDiagram-v2
    [*] --> INITIAL
    INITIAL --> ACTIVE : reportActivity()
    INITIAL --> DISCONNECTED : elapsed > disconnect_timeout_ns 或 disconnect()
    ACTIVE --> DISCONNECTED : elapsed > disconnect_timeout_ns 或 disconnect()
    DISCONNECTED --> INITIAL : reportActivity()(重連)
```

**變體 D — 兩者停用**(`timeout_ns = 0, disconnect_timeout_ns = 0`):
無任何自動逾時;只有 forced `disconnect()` 能離開 INITIAL/ACTIVE
(適合離散事件型通道,如 e-stop 指令)。

```mermaid
stateDiagram-v2
    [*] --> INITIAL
    INITIAL --> ACTIVE : reportActivity()
    INITIAL --> DISCONNECTED : disconnect()(forced)
    ACTIVE --> DISCONNECTED : disconnect()(forced)
    DISCONNECTED --> INITIAL : reportActivity()(重連)
```

實作註記:四變體共用同一 `checkTimeout(now, timeoutNs, disconnectNs)`——閾值為 0 即跳過
該項比對,**不是**四份狀態機;變體只是參數化行為的可視化。單元測試逐變體驗證(§4.5)。

### 2.4 註冊協定(兩階段 + rollback)

```mermaid
sequenceDiagram
    participant U as 使用者
    participant MA as Manager A
    participant MB as Manager B(target)

    U->>MA: registerSource(info)
    Note over MA: ① validate + 過濾
    Note over MA: ② lock:雙鍵查重 → 插入 PENDING 佔位
    MA->>MB: ControlSignalManage(REGISTER, info)
    Note over MB: ③ validate + 過濾 + lock 查重
    Note over MB: ④ Factory 建 Sink(PENDING, TTL 起算)
    MB-->>MA: SUCCESS
    Note over MA: ⑤ Factory 建 Source,PENDING → 轉正
    MA-->>U: SourceHandle

    Note over MA,MB: ── 失敗路徑 ──
    alt 遠端拒絕 / 逾時
        Note over MA: 移除 PENDING 佔位
        MA--)MB: ControlSignalManage(UNREGISTER)(best-effort,逾時情境)
        Note over MB: Sink PENDING TTL 逾期未見資料 → 自動回收
        MA-->>U: error
    end
```

- **佔位(PENDING)** 在持鎖下完成雙鍵(controller_name + channel_name)查重與插入,
  消除 rv2 的 TOCTOU;之後的遠端等待不持鎖。
- 逾時屬「結果不明」:同時做本地回收 + best-effort UNREGISTER + 依賴遠端 TTL,三重保險。
- `unregisterSource(handle)`:本地 shutdown + erase,並向 target 發 UNREGISTER。

### 2.5 Liveness 協定(v0.5.0 改版:CSM Master 集中式)

v0.3.0 的「CSM 互訂 status」與 v0.4.0 的「點對點 NOTIFY_ABNORMAL」在多 CSM 拓撲下
的連線數與通知路徑隨 CSM 數量以 O(N²) 成長(my_note:3 個 CSM 互為 source/target 時,
每個 CSM 須同時管理多個入站異常與多個出站通知)。v0.5.0 改為**集中式**:

- 每個 CSM 啟動時向 **CSM Master** 註冊(`/csm_master/register`),
  之後每個 status tick 呼叫 `/csm_master/heartbeat`(`std_srvs/Trigger`)——
  CSM 藉 response 確認 master 在線;master 藉請求到達確認 CSM 存活。
- CSM 照常發布 `<name>/status`(§2.5.1);**唯一訂閱者為 master**,CSM 之間互不訂閱。
- Master 以 `controller_name`(全系統唯一)配對 Source-Sink,任一側狀態變化 →
  **one-shot** 呼叫**雙方** CSM 的 `/<csm_name>/get_notifications` 推送(§9)。

| 對象 | 機制 | 判定 |
|---|---|---|
| Sink | **資料驅動**(主):任何收訊 → `reportActivity()`;master 通知(輔) | `checkTimeout()` 雙閾值(§2.3);通知 → 加速判定 / 觀測對側 |
| Source(topic 模式) | **master 通知**:配對 Sink 異常 / 對向 CSM 失聯 → 注入 | 通知內容映射:對側 TIMEOUT/DISCONNECTED → 本地 `checkTimeout()` 加速;CSM 失聯 → 該 CSM 全部配對 entity 注入 TIMEOUT |
| Source(service 模式) | service response(成功 → activity)+ master 通知 | response 逾時記 TIMEOUT;其餘同上 |
| 兩者 | 自身 elapsed 雙閾值(§2.3) | TIMEOUT / DISCONNECTED(休眠,不移除) |
| 重連 | 恢復收訊 / master 通知對側復原 | DISCONNECTED → INITIAL → (活動) → ACTIVE |

- **Master 失聯時(degraded mode)**:CSM heartbeat 得不到 response → log warning,
  本地判定(資料驅動 + 雙閾值)照常運作;僅失去「對側視角」通知。
  master 回線後 heartbeat 恢復,通知續傳(master 重新收 status 重建配對表)。
- Topic-模式 Source 在 degraded mode 下無任何活性來源(v0.3.0 link 已移除)→
  維持 INITIAL/最後狀態;此為集中式的取捨,列 §12 未決(是否補本地 fallback)。

#### 2.5.1 ManagerStatus 訊息(my_note #4,新設計)

`rv2_interfaces/msg/r1/ManagerStatus.msg`(取代 v0.2.0 的空 ManagerHeartbeat):

```
# 每 status_interval 發布於 <manager_name>/status
string manager_name
builtin_interfaces/Time stamp
r1/EntryStatus[] sources
r1/EntryStatus[] sinks
```

`rv2_interfaces/msg/r1/EntryStatus.msg`:

```
string manager_name         # 所屬 CSM(v0.5.0;master 配對與通知定位用)
string controller_name
string channel_name
string type                 # factory 型別鍵
string mode                 # topic / service
bool   is_source            # v0.5.0:master 配對方向判別
int8   state                # 0=INITIAL 1=ACTIVE 2=TIMEOUT 3=DISCONNECTED(常數)
float32 data_rate_hz        # 實測速率:Sink = 收訊率(§6);Source = send 呼叫率(§5,v0.4.0)
int8   priority
```

- 接收端(master)用途:CSM 活性佐證、配對表更新、狀態變化偵測(§9)。
- 頻寬:entry 數大時可調升 `statusIntervalMs`(Manager 參數);訊息內容為
  輕量 metadata,200ms × 數十 entries 規模無虞。
- `control_signal_info_req` service 保留(pull 式完整 Info 查詢;status 為 push 式輕量摘要)。
- **狀態計算與快取**(v0.4.0,my_note Heartbeat #1):status tick 對每個 entity 呼叫其
  非公開 `_calcRate()`(friend,§5/§6)——計算實測 rate、執行雙閾值逾時檢查、回傳
  `{state, rateHz}`;結果**per-entity 快取**於 CSM(組裝 ManagerStatus 直接取用)。
- 異常偵測與通知職責(v0.5.0)**上移至 master**:CSM 只發 status,
  變化比對、配對、one-shot 通知全在 master(§9);CSM 被動接收 `get_notifications`。

### 2.6 執行緒模型

- 本庫**不建立任何執行緒**(承襲 rv2);一切依附 node executor。
- **Manager 單一 timer**(v0.3.0):status tick 一個 timer 完成全部週期工作——
  發布 ManagerStatus、link 檢查、entities 掃描(timeout / disconnect 判定)。
  取代 v0.2.0 的 statusTimer + heartbeatTimer 雙 timer;endpoint 依然零 timer。
- **Callback group 策略**:
  - Manager 的 service servers(manage / info_req / get_notifications)、master clients
    (register / heartbeat)、status timer:放入 Manager 自建的
    **Reentrant group**(建構子建立),與使用者 node 的預設 group 隔離。
  - Source/Sink 的資料 pub/sub/service:預設 group(維持與使用者 callback 相同的互斥行為,符合 rclcpp 預設慣例)。
- 文件化硬規則 + debug assert:
  - `registerSource()` / `unregisterSource()` **禁止**在任何 ROS callback 內呼叫。
  - service 模式 `send()` 為阻塞呼叫,禁止在 callback 內呼叫。
- Manager 掃描 timer 於鎖內完成 snapshot 後才 log,無鎖外 map 存取。

---

## 3. `r1::ControlSignalInfo` 與驗證

### 3.1 訊息欄位(8 欄)

`rv2_interfaces/msg/r1/ControlSignalInfo.msg`

| 欄位 | 型別 | 說明 |
|---|---|---|
| `controller_name` | string | **必填、主鍵**。全系統唯一;Manager 之 map 鍵、黑白名單鍵 |
| `channel_name` | string | **必填、唯一**。資料 topic / service 名稱 |
| `target_manager_name` | string | 註冊時必填;Sink 所在 Manager 名 |
| `mode` | string | `"topic"` / `"service"`(常數定義於 msg) |
| `type` | string | Factory 型別鍵(`"joy"` / `"twist"` / `"string"` / …) |
| `priority` | int8 | 1–94,值大者優先;僅攜帶轉發,由上層仲裁消費 |
| `timeout_ns` | int64 | data-rate timeout 閾值;**0 = 停用**(v0.5.0,§2.3.1)。service 模式亦為 response 等待上限(0 時 service 模式拒絕註冊,見 §3.2 規則 5) |
| `disconnect_timeout_ns` | int64 | 0 = 永不自動移除;否則須 > `timeout_ns` |

刪除(相對 rv2):`send_freq_hz`(從未驅動狀態機)、`use_keep_alive` / `keep_alive_interval_ns`
(改為 Manager 參數)、`controller_priority_type`(類別上限屬約定,降為文件層)。

### 3.2 驗證規則(5 條)

`validateControlSignalInfo(info)` → `{bool valid; std::string error;}`

1. `controller_name` 非空。
2. `channel_name` 非空。
3. `mode` ∈ {topic, service};`type` 非空。
4. `priority` ∈ [1, 94]。
5. `timeout_ns ≥ 0`、`disconnect_timeout_ns ≥ 0`(0 = 各自停用,§2.3.1);
   兩者皆 > 0 時 `disconnect_timeout_ns > timeout_ns`;
   `mode == service` 時 `timeout_ns > 0`(response 等待上限不可停用)。

### 3.3 單元測試方法與流程

- **框架**:gtest;**純邏輯、不需 rclcpp init**(msg struct 直接填欄位)。
- 流程:builder helper `makeR1Info()` 給合法預設 → 逐條規則做「單欄位破壞」測試,
  驗證 `valid == false` 且 `error` 指名該欄位;全合法組合驗證 `valid == true`。
- 案例表:

| 案例 | 修改 | 預期 |
|---|---|---|
| V1 | 全預設 | valid |
| V2 | `controller_name = ""` | invalid, error 含 "controller_name" |
| V3 | `channel_name = ""` | invalid |
| V4 | `mode = "unknown"` | invalid |
| V5 | `priority` ∈ {0, -1, 95, 127} | invalid(4 子案例) |
| V6 | `priority` ∈ {1, 94} | valid(邊界) |
| V7 | `timeout_ns = 0`(topic 模式) | valid(停用,v0.5.0);`mode = service` 時 invalid |
| V8 | `disconnect_timeout_ns = timeout_ns`(皆 > 0) | invalid(須嚴格大於) |
| V10 | `timeout_ns = 0, disconnect_timeout_ns > 0`(topic) | valid(變體 C) |
| V9 | `disconnect_timeout_ns = 0` | valid(停用) |

---

## 4. `r1::LivenessState`

### 4.1 職責

單一類別封裝 4 態狀態機 + 活動時間戳,是**全系統唯一**允許改變狀態的地方。
純 C++、無 ROS 依賴 → 可完整單元測試。

### 4.2 設計

- 內部兩個 atomic(**定案布局**,不採單字 48-bit 壓縮方案——犧牲些微效能換可讀性與完整 ns 精度):
  - `std::atomic<uint64_t> packed_`:`[ state:8 | epoch:56 ]`
  - `std::atomic<int64_t>  lastActivityNs_`
- 所有轉移走 **CAS loop**,規則:
  1. load `packed_`(acquire)→ 查轉移表 → 允許才 `compare_exchange_strong`(acq_rel),
     expect = snapshot 完整值(state+epoch)。
  2. **每次成功轉移 epoch+1**(reportActivity、checkTimeout 的 →TIMEOUT、disconnect 皆同),
     雙向防 ABA。
  3. `reportActivity()`:先 store `lastActivityNs_`(release)再 CAS 狀態;
     `checkTimeout()`:先 load `packed_`(acquire)再 load 時間戳、算 elapsed,
     成立才以 snapshot 為 expect 執行 CAS。若期間 `reportActivity()` 已先完成轉移
     (epoch 已遞增),CAS 失敗,重新讀取後判定不成立,狀態保持 ACTIVE。
     此機制消除 stale-TIMEOUT 覆寫。
- 時間來源:`steadyNs()` 由呼叫端注入(參數傳入),elapsed 判定因此可注入假時鐘、完全 deterministic;
  交錯順序類測試(誰先誰後)以壓力迴圈 + TSan 覆蓋。

### 4.3 類別介面

```cpp
namespace r1 {

enum class ControlSignalState : uint8_t { INITIAL, ACTIVE, TIMEOUT, DISCONNECTED };

class LivenessState
{
public:
    explicit LivenessState(int64_t nowNs);

    /// 收訊 / 心跳 / 成功 response。
    /// 非 DISCONNECTED → ACTIVE;DISCONNECTED → INITIAL(重連,v0.3.0)。
    /// 回傳轉移後狀態(呼叫端可據此辨識重連事件)。
    ControlSignalState reportActivity(int64_t nowNs);

    /// 被動逾時檢查;必要時執行 {INITIAL,ACTIVE}→TIMEOUT。回傳檢查後狀態。
    /// 雙閾值(v0.5.0):0 = 該項停用。disconnect 判定優先於 timeout。
    ControlSignalState checkTimeout(int64_t nowNs, int64_t timeoutNs, int64_t disconnectNs);

    /// 休眠態;冪等。回傳是否由本次呼叫完成轉移。
    /// 非終態(v0.3.0):之後 reportActivity() 可重連回 INITIAL。
    bool disconnect();

    ControlSignalState state() const;        // load(acquire),不觸發檢查
    int64_t lastActivityNs() const;          // 供上層做頻率監控(取代 LOW_FREQ)

private:
    std::atomic<uint64_t> packed_;           // state + epoch
    std::atomic<int64_t>  lastActivityNs_;
};

} // namespace r1
```

### 4.4 行為細節

- `checkTimeout(now, timeoutNs, disconnectNs)`(v0.5.0 雙閾值):snapshot(state, epoch)
  → 計算 `elapsed = now - lastActivity` → 依序判定(0 = 跳過該項):
  1. `disconnectNs > 0 && elapsed > disconnectNs` 且 state ∈ {INITIAL, ACTIVE, TIMEOUT}
     → CAS 寫入 DISCONNECTED(優先判定;變體 C 由此路徑直接進入休眠)。
  2. 否則 `timeoutNs > 0 && elapsed > timeoutNs` 且 state ∈ {INITIAL, ACTIVE}
     → CAS 寫入 TIMEOUT。
  期間若 `reportActivity()` 已先完成轉移(epoch 遞增),CAS 失敗,重新讀取後判定不成立,
  狀態保持 ACTIVE。雙閾值取代 v0.4.0 之前由 CSM 執行的「TIMEOUT 持續計時」判定,
  逾時判定完整內聚於本類,CSM 不需追蹤 TIMEOUT 起始時間。
- `reportActivity()`:非 DISCONNECTED 態 → ACTIVE(epoch+1);
  **DISCONNECTED → INITIAL**(epoch+1,重連,v0.3.0;本次活動記入 lastActivity)。
  重連進入 INITIAL 而非 ACTIVE:單一訊息不足以判定連線恢復,需後續活動才轉 ACTIVE;
  若無後續活動,INITIAL 依逾時規則回到 TIMEOUT 與 DISCONNECTED。
  不穩定連線的狀態變化全程發生於狀態機內,entry 常駐,不進行 add/remove。
- `disconnect()`:CAS 至 DISCONNECTED(**休眠態**,非終態);
  `checkTimeout()` 於 DISCONNECTED 不動作;唯一出路為 `reportActivity()`(→ INITIAL)。
  物件移除(unregister / 解構)是 Manager 層行為,與狀態機解耦。

### 4.5 單元測試方法與流程

- **框架**:gtest,純邏輯 + 假時鐘(手動遞增的 int64)。並發測試用 `std::thread`。
- 流程:
  1. **轉移表窮舉**:4 態 × 3 操作全組合,驗證合法轉移與拒絕(含 DISCONNECTED 終態性)。
  2. **逾時語意**:INITIAL 自建構起算逾時;ACTIVE 依 lastActivity;邊界 `elapsed == timeout` 不觸發。
  3. **stale-TIMEOUT 回歸測試**(對應 rv2 稽核發現):執行緒 A 進入 checkTimeout 且已完成
    snapshot(以 hook / 兩步 API 或高頻壓力重現),執行緒 B reportActivity → 斷言最終態 ACTIVE。
    壓力版:1 writer 高頻 reportActivity + N checker 高頻 checkTimeout(短 timeout),
    每輪結束時只要「最後一次操作是 activity」即斷言 ACTIVE;跑 10⁵ 輪。
  4. **disconnect 並發**:disconnect 與 reportActivity 併發 10⁵ 輪,斷言終態恆 DISCONNECTED。
  5. TSan job(見 §11.4)覆蓋本類所有並發測試。

| 案例 | 內容 | 預期 |
|---|---|---|
| L1 | 初始 | INITIAL |
| L2 | reportActivity | → ACTIVE, true |
| L3 | checkTimeout(elapsed > t) | ACTIVE → TIMEOUT |
| L4 | TIMEOUT 後 reportActivity | → ACTIVE |
| L5 | disconnect 後 checkTimeout | DISCONNECTED(不動作) |
| L6 | INITIAL + elapsed > t | → TIMEOUT |
| L7 | 併發 stale-TIMEOUT 壓力 | 無 ACTIVE 被舊判定覆寫 |
| L8 | 併發 disconnect 壓力 | 掃描期間狀態恆收斂 DISCONNECTED;僅 reportActivity 可離開 |
| L9 | **重連**:disconnect 後 reportActivity | → INITIAL(回傳 INITIAL);再 reportActivity → ACTIVE |
| L10 | 重連後無後續活動 | INITIAL → TIMEOUT → DISCONNECTED,循環不需重建物件 |
| L11 | 併發 reportActivity vs disconnect 壓力 | 終局為兩者之一的合法結果;無非法狀態、epoch 單調遞增 |
| L12 | **變體 A**:elapsed 越過兩閾值 | 先 TIMEOUT(> timeout)後 DISCONNECTED(> disconnect);單次呼叫越過兩者 → 直接 DISCONNECTED |
| L13 | **變體 B**(disconnect=0):elapsed 極大 | 停留 TIMEOUT,永不自動 DISCONNECTED |
| L14 | **變體 C**(timeout=0):elapsed > disconnect | INITIAL/ACTIVE 直接轉入 DISCONNECTED,TIMEOUT 不可達 |
| L15 | **變體 D**(皆 0):elapsed 極大 | 狀態不變;僅 disconnect() 可轉 DISCONNECTED |

### 4.6 替代方案評估:tinyFSM(v0.2.0,依 my_note.md)

評估對象:[digint/tinyfsm](https://github.com/digint/tinyfsm) — header-only、C++11 template、
零動態配置、無 RTTI/例外依賴,MIT 授權;最新版 0.3.3,其後長期無 release。

| 面向 | 評估 |
|---|---|
| Thread-safety | **無內建同步**。`LivenessState` 的核心需求正是多執行緒併發轉移(使用者執行緒 `checkTimeout` vs executor 執行緒 `reportActivity`);採 tinyfsm 仍須自行外包 mutex 或 atomic 層——並發正確性問題原封不動回到我們手上,library 未解決本設計最難的部分 |
| 實例模型 | tinyfsm 狀態為**每個 FSM 類型的 static instance**(單例導向);r1 每個 Source/Sink 需獨立 FSM 實例,需 workaround,與設計錯配 |
| 表達力 | epoch/CAS 防 stale-TIMEOUT 語意(帶版本的比較交換轉移)無法以 tinyfsm 的事件 dispatch 模型表達 |
| 規模 | 本狀態機僅 4 態 × 3 操作;引入外部依賴的結構開銷大於收益 |
| 維護 | 0.3.3 後長期停更,依賴風險 |

**結論:不採用**。維持 §4.2 自製 CAS 狀態機。但採納 tinyfsm 的精神——轉移表集中宣告
(constexpr 轉移表)+ 單元測試窮舉全組合(§4.5 流程 1),確保「context safety」訴求
以可驗證方式落實。若未來狀態數成長(>8 態)再重啟評估。

---

## 5. `r1::ControlSignalSource`

### 5.1 職責

控制訊號發送端。topic 模式持 `Publisher<msgT>`,service 模式持 `Client<srvT>`。
**建構子 private**;`friend class ControlSignalManager` + Factory creator 可建。
繼承 `std::enable_shared_from_this`。

### 5.2 類別架構

```cpp
namespace r1 {

/// _calcRate() 回傳的輕量快照(v0.4.0);CSM per-entity 快取此值
struct EntityStatus {
    ControlSignalState state;
    float              rateHz;
};

namespace detail {
/// Rolling-window 呼叫/收訊記錄器(v0.5.0,my_note:window size 可配置)。
/// N-bucket 環形(N 固定 8),bucket 時距 = windowNs / N;record() 對當前
/// bucket 原子遞增(過期 bucket lazy 清零);calcHz() 加總完整窗 / 窗長。
/// 純 atomic、無鎖;Source(send 記錄)與 Sink(收訊記錄)共用。
class RateRecorder {
public:
    explicit RateRecorder(int64_t windowNs);   // windowNs 來自 ManagerOptions.rateWindowNs
    void  record(int64_t nowNs);               // hot path,O(1)
    float calcHz(int64_t nowNs) const;         // cold path,_calcRate() 專用
private:
    std::array<std::atomic<uint32_t>, 8> buckets_;
    std::atomic<int64_t> bucketEpochNs_;
    const int64_t windowNs_;
};
} // namespace detail

/// per-state 轉移 callback 簽名(v0.5.0,my_note FSM #5)
using StateCb = std::function<void(const std::string& controllerName,
                                   ControlSignalState oldState,
                                   ControlSignalState newState)>;

class BaseControlSignalSource
{
public:
    virtual ~BaseControlSignalSource() = default;
    virtual ControlSignalState getState() const = 0;              // 觸發被動檢查
    virtual const msg::r1::ControlSignalInfo& getInfo() const = 0;
    virtual std::type_index msgType() const = 0;
    virtual SendResult sendErased(const void* msg) = 0;
    virtual void shutdown() = 0;          // 釋放 rclcpp entities;冪等
protected:
    BaseControlSignalSource() = default;
};

/// SendResult 取代 rv2 的 (bool return + bool& cmdSuccess) 雙輸出
enum class SendResult : uint8_t {
    OK,             // 已送出(topic)/ 對方接受(service)
    REJECTED,       // service 對方回非 SUCCESS
    NO_TRANSPORT,   // transport 不可用 / 已 shutdown
    TIMEOUT,        // service response 逾時
    DISCONNECTED    // 已被 Manager 判定斷線
};

template<typename msgT, typename srvT = void>
class ControlSignalSource : public BaseControlSignalSource,
                            public std::enable_shared_from_this<...>
{
    friend class ControlSignalManager;
    friend class ControlSignalFactory;   // creator lambda
private:
    ControlSignalSource(rclcpp::Node* node, const InfoT& info);   // private!

    rclcpp::Node*                 node_;
    InfoT                         info_;
    std::variant<PubPtr, CliPtr>  transport_;   // ClientPtrOf<void> = monostate(承襲 rv2 trait)
    LivenessState                 liveness_;
    std::atomic<bool>             shutdown_{false};

    // send 呼叫記錄(v0.4.0/v0.5.0):rolling window,大小由 ManagerOptions.rateWindowNs 配置
    detail::RateRecorder          rate_;
    std::atomic<float>            cachedRateHz_{0.f};   // _calcRate() 結果快取

    // per-state 轉移 callback(v0.5.0):每狀態一 slot;CSM 經 friend 安裝
    std::array<StateCb, 4>        stateCbs_;
    mutable std::shared_mutex     stateCbMtx_;

    /// 非公開(my_note Source #2):由 CSM status tick 呼叫(friend)。
    /// rate_.calcHz() → cachedRateHz_ → checkTimeout(雙閾值)→ 回傳 {state, rateHz};
    /// 轉移發生時 fire 對應 stateCbs_(無鎖呼叫,copy 後執行)。
    EntityStatus _calcRate(int64_t nowNs);

public:
    SendResult send(const msgT& msg);
    float sendRateHz() const;                       // 讀 cachedRateHz_,不觸發計算
    EntityStatus getStatus() const;                 // v0.5.0(my_note FSM #4):{state, cachedRate} 整合查詢
    ControlSignalState getState() const override;   // link 狀態由 Manager 餵入:見下
    ...
};

} // namespace r1
```

### 5.3 行為細節

- **send(共通前置,v0.4.0,my_note Source #1)**:`shutdown_` 檢查 →
  `rate_.record(now)`(rolling window 原子遞增,窗長可配置)→ 進入模式分支。
- **send(topic)**:publish → `OK`。狀態不變(無 send-side 回饋;liveness 由 Manager link 供給)。
- **send(service)**:`service_is_ready()` → `async_send_request` → 等待 ≤ `timeout_ns`
  (**無 50ms 隱藏 fallback**;`timeout_ns` 必填,直接使用)。
  ready → `liveness_.reportActivity()`,依 response 回 `OK`/`REJECTED`;
  逾時 → `liveness_.checkTimeout()` 語意下記為 TIMEOUT 並回 `TIMEOUT`,
  並呼叫 `client->remove_pending_request()`(rv2 稽核:pending request 洩漏)。
- **link liveness 注入**:Source 本身不訂閱 status。Manager 的 link 監視器
  在 link activity / link timeout 時對該 target 的所有 Source 呼叫
  `liveness_.reportActivity()` / `checkTimeout()`。Source 保持零 timer、零訂閱。
- **DISCONNECTED(休眠)下的 send**:回 `SendResult::DISCONNECTED`,拒絕發送;
  transport **保留**(v0.3.0:斷線不再 shutdown,等待 link 恢復觸發重連 → INITIAL)。
- **`_calcRate()`**(v0.4.0,非公開,`friend class ControlSignalManager` 專用):
  CSM status tick 每週期呼叫一次。`rate_.calcHz(now)` →
  store `cachedRateHz_` → `liveness_.checkTimeout(now, timeout, disconnect)`(雙閾值)
  → 回傳 `{state, rateHz}`。公開 `sendRateHz()` 僅讀快取——
  **記錄(每次 send,O(1) atomic)與計算(每 tick 一次)分離**,hot path 零除法零鎖。
- **state callback fire 規則**(v0.5.0):所有經本類方法觸發的 LivenessState 轉移
  (`_calcRate` 內 checkTimeout、Manager 注入 activity/disconnect、service send 的
  reportActivity/TIMEOUT)在偵測到 old ≠ new 時,shared_lock 下 copy 對應
  `stateCbs_[new]` → **無鎖呼叫**。同一轉移恰 fire 一次(轉移由 CAS 唯一勝出者觸發)。
- **shutdown()**:僅於 unregister / 解構呼叫。置 flag → 重置 `transport_` → 之後 send 回 `NO_TRANSPORT`。
- lambda(service 模式無)一律不存在 → Source 無捕獲 `this` 的 callback。

### 5.4 單元測試方法與流程

- **框架**:gtest + `CsmTestBase`(r1 版:MultiThreadedExecutor 背景 spin)。
- **建構通道**:測試經 `ControlSignalFactory`(friend)直建,或經測試專用
  `ManagerTestAccess`(`friend struct`,只在 test build 提供)。**不開放 public 建構**。
- 流程:每案例建 node → 經 factory 建 Source(+ 對測 Sink 或 mock service)→ 操作 → 斷言。

| 案例 | 內容 | 預期 |
|---|---|---|
| S1 | topic 模式初始 | `getState() == INITIAL`;`send() == OK` |
| S2 | service 模式 send 成功 | `OK`;state → ACTIVE(reportActivity) |
| S3 | service 模式 server 回 REJECT | `REJECTED`;state 仍 ACTIVE(有 response 即活動) |
| S4 | service 模式無 server | `TIMEOUT`;state → TIMEOUT;耗時 ≈ `timeout_ns`(驗證無 50ms fallback) |
| S5 | shutdown 後 send | `NO_TRANSPORT`;冪等 shutdown |
| S6 | sendErased 型別轉發 | 與 send 等價;`msgType()` 正確 |
| S7 | Manager 注入 link timeout | state → TIMEOUT;再注入 activity → ACTIVE |
| S8 | disconnect 後 send | `DISCONNECTED`(transport 保留但拒送) |
| S9 | **重連**:disconnect 後注入 link activity | state → INITIAL;再注入 → ACTIVE;send 恢復 `OK` |
| S10 | **send rate**:20 Hz send 2 秒後呼叫 `_calcRate()`(測試經 friend 通道) | 回傳 rateHz ∈ [18, 22];`sendRateHz()` 讀到同值;停止 1 窗後歸 0 |
| S11 | rate 並發:高頻 send + 週期 `_calcRate()` + 高頻 `sendRateHz()` | 無 race(TSan);快取值單調收斂 |
| S12 | **state callback**:註冊 TIMEOUT/ACTIVE slot,驅動轉移 | 每次轉移恰觸發一次、old/new 正確;未註冊 slot 無動作;nullptr 清除 |
| S13 | **window 配置**:rateWindowNs 0.5s vs 2s | calcHz 收斂時間與窗長一致;`getStatus()` 回 {state, rate} 一致 |

---

## 6. `r1::ControlSignalSink`

### 6.1 職責

控制訊號接收端。topic 模式持 `Subscription<msgT>`,service 模式持 `Service<srvT>`。
建構子 private;`enable_shared_from_this`;**零 timer**(keep-alive timer 已移除)。

### 6.2 類別架構

```cpp
namespace r1 {

class BaseControlSignalSink
{
public:
    using ErasedMsgCb = std::function<void(const void*, const msg::r1::ControlSignalInfo&)>;
    virtual ~BaseControlSignalSink() = default;
    virtual ControlSignalState getState() const = 0;
    virtual const msg::r1::ControlSignalInfo& getInfo() const = 0;
    virtual std::type_index msgType() const = 0;
    virtual bool readErased(void* outMsg) const = 0;   // true 僅當 ACTIVE
    virtual void setErasedMsgCallback(ErasedMsgCb cb) = 0;
    virtual void shutdown() = 0;
protected:
    BaseControlSignalSink() = default;
};

template<typename msgT, typename srvT = void>
class ControlSignalSink : public BaseControlSignalSink,
                          public std::enable_shared_from_this<...>
{
    friend class ControlSignalManager;
    friend class ControlSignalFactory;
private:
    ControlSignalSink(rclcpp::Node* node, const InfoT& info);

    std::variant<SubPtr, SrvPtr> transport_;
    LivenessState                liveness_;
    mutable std::mutex           msgMtx_;      // 僅護 latestMsg_
    std::optional<msgT>          latestMsg_;
    mutable std::mutex           cbMtx_;       // 僅護 msgCb_
    MsgCb                        msgCb_;
    std::atomic<bool>            shutdown_{false};
    // 收訊記錄(v0.5.0):rolling window,窗長由 ManagerOptions.rateWindowNs 配置
    detail::RateRecorder         rate_;
    std::atomic<float>           cachedRateHz_{0.f};  // _calcRate() 結果快取(v0.4.0)
    // per-state 轉移 callback(v0.5.0):同 Source 樣式
    std::array<StateCb, 4>       stateCbs_;
    mutable std::shared_mutex    stateCbMtx_;
    // waitForMessage(v0.4.0):序號 + condition variable(msgMtx_ 為其鎖)
    std::atomic<uint64_t>        msgSeq_{0};
    mutable std::condition_variable msgCv_;

    /// 非公開(my_note Sink #3):CSM status tick 呼叫(friend)。
    /// 計算收訊率 → cachedRateHz_ → checkTimeout → 回傳 {state, rateHz}。
    EntityStatus _calcRate(int64_t nowNs);
public:
    bool read(msgT& out) const;
    /// 阻塞等待「呼叫之後」的下一筆訊息(my_note Sink #2)。
    /// timeoutNs 0 = 無限等;收到 → true + out;逾時 / shutdown → false。
    bool waitForMessage(msgT& out, int64_t timeoutNs = 0) const;
    float dataRateHz() const;                  // 讀 cachedRateHz_,不觸發計算
    EntityStatus getStatus() const;            // v0.5.0:{state, cachedRate} 整合查詢
    void setMsgCallback(MsgCb cb);
    ...
};

} // namespace r1
```

### 6.3 行為細節

- **收訊路徑 `_store()`**(v0.3.0 固定順序,my_note Sink #2):lambda 捕獲 `weak_ptr`,
  lock 失敗即 return。成功後:
  1. **`rate_.record(now)`(前置小函數)**:記錄時間與次數(rolling window 原子遞增,
     窗長可配置),永遠第一步。
  2. `msgMtx_` 下寫 `latestMsg_`,`msgSeq_`+1 → **`msgCv_.notify_all()`**(喚醒 waitForMessage)。
  3. `liveness_.reportActivity()` —— 一般態 → ACTIVE;**DISCONNECTED → INITIAL(重連)**,
     訊息照存(資料真實有效);轉移結果記入 log(重連事件可觀測)。
  4. cbMtx_ 下 copy callback → **無鎖呼叫** callback(承襲 rv2 正確做法)。
  rv2 稽核所列「DISCONNECTED 狀態被收訊路徑覆寫」問題在 r1 成為受控行為:
  狀態恢復必須經由狀態機的合法轉移(進入 INITIAL,而非直接轉 ACTIVE),
  轉移語意集中於 `LivenessState`。
- **rate 記錄與計算分離**(v0.4.0,my_note Sink #1/#3):hot path 只做 O(1) 原子遞增;
  計算集中在非公開 **`_calcRate()`**,由 CSM status tick 每週期呼叫一次(friend):
  `rate_.calcHz(now)` → store `cachedRateHz_` → `checkTimeout(雙閾值)` →
  回傳 `{state, rateHz}` 供 CSM 快取與發布(§2.5.1)。公開 `dataRateHz()` 僅讀快取。
- **state callback fire 規則**(v0.5.0):同 §5.3——所有經 `_store`/`_calcRate`/
  Manager 注入的轉移,old ≠ new 時 copy `stateCbs_[new]` 無鎖呼叫,恰一次。
- **`waitForMessage(out, timeoutNs)`**(v0.4.0,my_note Sink #2):
  進入時 snapshot `seq0 = msgSeq_` → `std::unique_lock<std::mutex> lk(msgMtx_)` →
  `msgCv_.wait[_for](lk, pred)`,pred = `msgSeq_ > seq0 || shutdown_`。
  以**序號**為條件:免疫 spurious wakeup、無 lost-wakeup(notify 在持鎖遞增 seq 之後)。
  滿足且非 shutdown → copy `latestMsg_` 回 true;逾時或 shutdown → false。
  `shutdown()` 置 flag 後 `notify_all()`,等待者即刻退出(RAII:解構前 shutdown 保證無滯留等待者)。
  ⚠ 阻塞呼叫:禁止在任何 ROS callback 內使用(同 `registerSource` 規則,§2.6)。
- **read()**:`checkTimeout()` → msgMtx_ 下 copy → 僅 ACTIVE 回 true。
  首訊息視窗安全性由「ACTIVE 只在 `latestMsg_` 寫入後設定」保證(rv2 已證明,保留同序)。
- **service 模式**:server callback `_store(req->data)` 後回 `SRV_RES_SUCCESS`;
  DISCONNECTED 下收到 request = 重連事件,同 `_store` 流程(回 SUCCESS)。
- PENDING TTL(§2.4):由 Manager 側追蹤,Sink 本身不管。

### 6.4 單元測試方法與流程

- 同 §5.4 環境;對測用 factory 直建的 Source 或裸 `rclcpp` publisher/client(mock 上游)。

| 案例 | 內容 | 預期 |
|---|---|---|
| K1 | 初始 | INITIAL;`read() == false`,out 為預設值 |
| K2 | 收first訊息 | ACTIVE;read true + 內容正確 |
| K3 | 停止發送 elapsed > timeout | TIMEOUT;read false(內容仍為最後值) |
| K4 | TIMEOUT 後恢復發送 | → ACTIVE |
| K5 | callback:註冊後每訊息觸發、nullptr 清除、replace 語意 | 觸發次數/內容正確 |
| K6 | callback 內 re-enter(呼叫 read/getState) | 無死鎖(callback 無鎖呼叫的回歸測試) |
| K7 | service 模式 round-trip | request data == read 內容;response SUCCESS |
| K8 | **重連**:disconnect 後收訊 | 狀態 → INITIAL、訊息已存(read 仍 false)、callback 觸發;續發 → ACTIVE、read true |
| K9 | shutdown 後上游持續發送 | 無 callback、無狀態變化(subscription 已釋放) |
| K10 | weak-capture UAF 回歸:高頻收訊中 Manager 移除 Sink | 無 crash(ASan/TSan job) |
| K11 | **data rate**:20 Hz 發送 2 秒後呼 `_calcRate()`(friend 通道) | 回傳 ∈ [18, 22];`dataRateHz()` 同值;停止 1 窗後歸 0 |
| K12 | rate 並發:高頻收訊 + 週期 `_calcRate()` + 高頻 `dataRateHz()` | 無 race(TSan) |
| K13 | **waitForMessage**:等待中發送一筆 | 即刻返回 true、內容正確;逾時版在無訊息時 ≈ timeoutNs 返回 false |
| K14 | waitForMessage 喚醒語意:等待前已存在的舊訊息 | 不觸發(只等「呼叫後」新訊息);並發多等待者全部喚醒 |
| K15 | waitForMessage + shutdown | 等待者即刻返回 false;無 deadlock、無 UAF(ASan) |

---

## 7. `r1::ControlSignalFactory`

### 7.1 職責

執行期型別字串 → 編譯期 `(MsgT, SrvT)` 的註冊表。承襲 rv2 設計(已驗證良好),差異:

- creator 回傳 `std::shared_ptr`(rv2 為 `unique_ptr`;r1 的 enable_shared_from_this 需要)。
- `Register()` 重複註冊改為**記 log 並拒絕**(rv2 靜默覆蓋)。
- `CreateSource/CreateSink` 不丟例外,回傳 `nullptr` + error out-param(精簡呼叫端 try/catch)。

### 7.2 類別介面

```cpp
class ControlSignalFactory
{
public:
    static ControlSignalFactory& Instance();      // 定義於 .cpp(shared library 單一定義,承襲 rv2)

    template<typename MsgT, typename SrvT = void>
    bool Register(const std::string& name);       // false = 名稱已存在

    std::shared_ptr<BaseControlSignalSource>
    CreateSource(const std::string& type, rclcpp::Node*, const InfoT&) noexcept;
    std::shared_ptr<BaseControlSignalSink>
    CreateSink(const std::string& type, rclcpp::Node*, const InfoT&) noexcept;

    std::string typeKey(std::type_index) const;   // 反查;未註冊回 ""
    bool has(const std::string& type) const;
};

#define R1_REGISTER_CONTROL_SIGNAL(UniqueId, name_str, MsgType, SrvType) ...
```

`src/r1/control_signal_types.cpp` 註冊 joy / twist / string(string topic-only,`void`)。

### 7.3 單元測試方法與流程

- gtest + 單 node(需 rclcpp init,不需跨 node)。

| 案例 | 內容 | 預期 |
|---|---|---|
| F1 | Create 已註冊型別(topic/service 模式) | 非 null;`msgType()` 正確 |
| F2 | Create 未註冊型別 | nullptr + error 字串,無例外 |
| F3 | typeKey 反查 joy/twist/string/未註冊 | "joy"/"twist"/"string"/"" |
| F4 | 重複 Register 同名 | 回 false;原 entry 不變 |
| F5 | singleton 跨 TU 一致性 | library 內註冊對測試可見(shared library 單一定義回歸) |

---

## 8. `r1::ControlSignalManager`

### 8.1 職責

- 唯一入口:`registerSource()` / `unregisterSource()`。
- 服務 host:`<name>/control_signal_manage`(REGISTER/UNREGISTER)、
  `<name>/control_signal_info_req`、**`<name>/get_notifications`**(v0.5.0,master 專用)。
- **ManagerStatus 發布**(v0.3.0):單一 status timer 週期發布 §2.5.1 訊息;
  v0.5.0 起訂閱者為 master,CSM 互不訂閱。
- **Master 互動**(v0.5.0):啟動時 `/csm_master/register` 註冊;每 tick 呼叫
  `/csm_master/heartbeat`(Trigger,async;response 逾時 → degraded mode log)。
- 同一 status tick 內完成:狀態計算、發布、master heartbeat、entity 掃描
  (雙閾值 → TIMEOUT / **disconnect→休眠**)、PENDING TTL 回收。
- Sink callback 註冊:`registerCallback`;**per-state 轉移 callback 註冊**(v0.5.0,見下)。
- 黑白名單(`controller_name` 為鍵,雙向套用;承襲 rv2)。

### 8.2 類別架構

```cpp
class ControlSignalManager
{
public:
    ControlSignalManager(rclcpp::Node* node, const std::string& name,
                         const ManagerOptions& opt = {});
    // 非拷貝非移動

    // ── 使用者 API ──
    // 文件縮寫:using InfoT = rv2_interfaces::msg::r1::ControlSignalInfo;
    enum class RegisterError : uint8_t {
        OK, INVALID_INFO, FILTERED, DUPLICATE,
        TARGET_UNREACHABLE, TIMEOUT_UNKNOWN,   // TIMEOUT_UNKNOWN = 結果不明,已觸發 rollback
        REJECTED, TYPE_UNSUPPORTED
    };
    struct RegisterResult { RegisterError code; SourceHandle handle; };

    RegisterResult registerSource(const InfoT& info, int64_t timeoutMs = 5000);
    bool unregisterSource(const SourceHandle& h, int64_t timeoutMs = 5000);

    SourceHandle getSource(const std::string& controllerName) const;   // 查無 → 空 handle(valid()==false)
    SinkHandle   getSink(const std::string& controllerName) const;
    // 查無 entry → std::nullopt(取代 rv2「查無回 UNKNOWN」的雙重語意)
    std::optional<ControlSignalState> getSourceState(const std::string& controllerName) const;
    std::optional<ControlSignalState> getSinkState(const std::string& controllerName) const;
    std::vector<InfoT> getSourceInfoList() const;
    std::vector<InfoT> getSinkInfoList() const;

    // ── 通知接收(v0.5.0:來源改為 CSM Master 的 get_notifications 呼叫)──
    // 文件縮寫:using EntryStatusT = rv2_interfaces::msg::r1::EntryStatus;
    // entries = master 推送的「配對另一側 / 本側」狀態變化清單(EntryStatus.manager_name 標示歸屬)。
    using NotificationCb = std::function<void(const std::vector<EntryStatusT>& entries)>;
    void setNotificationCallback(NotificationCb cb);   // nullptr 清除

    // ── per-state 轉移 callback(v0.5.0,my_note CSM Sources/Sinks #5)──
    // 對「全部」managed sources / sinks 生效;state = 轉入之新狀態。
    // cb(controllerName, oldState, newState);每狀態一 slot,後者覆蓋,nullptr 清除。
    void registerSourceStateCallback(ControlSignalState state, StateCb cb);
    void registerSinkStateCallback(ControlSignalState state, StateCb cb);

    // ── Sink callback 註冊(v0.3.0,my_note Sink #3)──
    // 鍵 = factory 型別字串("joy"/"twist"/...);每型別一個 callback,後者覆蓋。
    // 型別安全版(推薦):msgT 經 Factory typeKey 反查出字串鍵。
    template<typename msgT>
    bool registerCallback(std::function<void(const msgT&, const InfoT&)> cb);
    // 字串鍵 + 型別抹除版(generic 工具用;type 未註冊於 Factory → 回 false):
    bool registerCallback(const std::string& type, BaseControlSignalSink::ErasedMsgCb cb);
    void unregisterCallback(const std::string& type);

    void enableControllerWhitelist(const std::vector<std::string>&);
    void disableControllerWhitelist();
    void enableControllerBlacklist(const std::vector<std::string>&);
    void disableControllerBlacklist();

    const std::string& getName() const;

private:
    struct SourceEntry {                    // map value;PENDING 佔位即一個 entry
        enum class Phase { PENDING, ACTIVE } phase;
        std::shared_ptr<BaseControlSignalSource> source;   // PENDING 時為 nullptr
        std::string  channelName;           // 佔位期間供雙鍵查重
        int64_t      pendingSinceNs;
        EntityStatus lastStatus;            // v0.4.0:上一 tick _calcRate() 快取
    };
    struct SinkEntry { /* 同型,含 PENDING TTL 起點 + lastStatus */ };
    // (v0.5.0:LinkMonitor 移除——CSM 不互訂 status;變化偵測/通知移至 master。
    //  lastNotifiedState 亦移除,邊緣偵測屬 master 職責。)

    // v0.4.0(§1.6):map 讀多寫少 → shared_mutex(讀 shared_lock / 寫 unique_lock)
    mutable std::shared_mutex sourceMtx_;  std::map<std::string, SourceEntry> sources_;
    mutable std::shared_mutex sinkMtx_;    std::map<std::string, SinkEntry>   sinks_;
    // cbMtx_ / typedCbs_、filterMtx_ / 黑白名單:承襲 rv2
    rclcpp::CallbackGroup::SharedPtr mgmtGroup_;   // Reentrant;服務/client/timers 屬之
};

struct ManagerOptions {
    int64_t     statusIntervalMs = 200;   // 單一 tick:狀態計算 + status 發布 + master heartbeat
    int64_t     pendingTtlMs     = 10000;
    int64_t     rateWindowNs     = 1'000'000'000;  // v0.5.0:RateRecorder 窗長(可配置)
    std::string masterName       = "csm_master";   // v0.5.0:master 服務前綴
};
```

### 8.3 行為細節

- **registerSource(兩階段)**:validate → 過濾 → `sourceMtx_` 下雙鍵查重 +
  `emplace` PENDING(失敗 = 重複 → error)→ 放鎖 → 遠端 manage(REGISTER) →
  成功:factory 建 Source、entry 轉正、確保 link 監視器存在、回 Handle;
  失敗/逾時:erase PENDING(+ 逾時情境 best-effort UNREGISTER)。
  轉正時**再持鎖檢查 entry 仍為自己的 PENDING**(防禦性;佔位已排除他人)。
- **_onManage(REGISTER)**:validate → 過濾 → `sinkMtx_` 查重 + emplace PENDING →
  放鎖建 Sink → 持鎖轉正(re-check:entry 仍存在且 `phase == PENDING` 才轉正;
  已被 TTL 回收 → 銷毀剛建的 Sink、回 error)→ 套用 typed callback → 回 SUCCESS。
  Sink PENDING 起 TTL:掃描 timer 發現 PENDING 超過 `pendingTtlMs` 且 liveness 仍 INITIAL → 回收。
  轉正與 TTL 回收**皆在 `sinkMtx_` 下檢查 `phase`**,互斥無競態;
  且 `pendingTtlMs`(預設 10s)≫ service 處理時間(ms 級),正常路徑不會被誤收。
- **_onManage(UNREGISTER)**:比對 controller_name(+ 來源 manager 名)→ shutdown + erase。
- **status tick**(mgmtGroup 單一 timer,週期 `statusIntervalMs`,v0.5.0):
  1. **狀態計算**(shared_lock 巡覽):對每個 ACTIVE-phase entity 呼叫 `_calcRate(now)`
     (friend;內含**雙閾值** checkTimeout,TIMEOUT 與 DISCONNECTED〔休眠〕判定
     一併完成——CSM 不再追蹤 TIMEOUT 起始時間)→ 寫回 `entry.lastStatus` 快取
     (寫欄位為 tick 專屬,單寫者,shared_lock 下安全)。轉移發生 → entity
     fire per-state callback(§5.3/§6.3)。
  2. 發布 ManagerStatus(直接取 `lastStatus` 快取組訊息,鎖外 publish)。
  3. **master heartbeat**:async 呼叫 `/csm_master/heartbeat`(Trigger);
     上次呼叫的 response 逾時未達 → degraded mode(log,一次性)。
  4. PENDING TTL 回收;log 以快取 snapshot。
- **_onGetNotifications**(v0.5.0,master → CSM):收 `CsmNotify::Request.entries` →
  比對本地 entries:對側 TIMEOUT/DISCONNECTED → 對本地配對 entity 立即
  `checkTimeout()`(加速收斂);對側恢復 ACTIVE 且本地 DISCONNECTED →
  `reportActivity()` 注入(重連 → INITIAL)→ 觸發 `setNotificationCallback`
  使用者回呼(無鎖)→ 回 SUCCESS。
- **degraded mode**(master 失聯):本地判定照常;不重試 register(heartbeat 本身
  即持續探測,master 回線後第一個成功 heartbeat 觸發 re-register 確認)。
- **移除路徑**(僅 unregister / 解構):`entity->shutdown()` → erase(先 shutdown 再 erase)。
- **LinkMonitor 生命週期**:Source 註冊轉正時 `links_[target].controllers.insert(ctrl)`
  (無 entry 則建立訂閱);Source 移除(unregister / auto-disconnect / 解構)時
  `controllers.erase(ctrl)`,**集合空 → erase LinkMonitor(關閉 heartbeat 訂閱)**。
  多個 Source 同 target 共用一個 link,個別 unregister 不影響其餘。
- **鎖序**:`sourceMtx_`/`sinkMtx_` → `cbMtx_`(單向,承襲 rv2 已驗證無死鎖);
  `linkMtx_` 獨立,不與前兩者巢狀。

### 8.4 單元測試方法與流程

- gtest + 雙 node 雙 Manager(r1TestBase);MultiThreadedExecutor 背景 spin。
- 假時鐘不可行(rclcpp timer),以短週期參數(`ManagerOptions`)壓縮測試時間。

| 案例 | 內容 | 預期 |
|---|---|---|
| M1 | 正常註冊 | 本地 Source + 遠端 Sink;Handle 有效 |
| M2 | 重複 controller / 重複 channel(本地) | error,無遠端呼叫(觀察遠端無 Sink) |
| M3 | 跨 manager 重複(A1 已註冊,A2 同 controller → 同 target) | 遠端拒絕;A2 無殘留 PENDING |
| M4 | **並發註冊壓力**:16 執行緒同 controller 不同 target | 恰一成功;無覆蓋(rv2 TOCTOU 回歸) |
| M5 | target 不存在 → 逾時 | error;PENDING 已清;之後同名可重註冊 |
| M6 | 遠端接受但 response 丟失(mock 攔截) | 本地 error + UNREGISTER 送出;遠端 Sink 經 TTL 回收(孤兒回歸) |
| M7 | unregisterSource | 兩側移除;Handle 失效;同名可重註冊 |
| M8 | **get_notifications 注入**(mock master 呼叫):對側 TIMEOUT 清單 | 本地配對 Source 加速 checkTimeout;對側恢復清單 + 本地 DISCONNECTED → 重連 INITIAL;`setNotificationCallback` 觸發 |
| M9 | auto-disconnect(v0.3.0 休眠語意) | TIMEOUT 持續 > disconnect_timeout → 兩側各自轉 DISCONNECTED;entry 保留、Handle 仍 valid、state 查詢回 DISCONNECTED |
| M15 | **重連復原**:M9 後恢復資料/link | 兩側 DISCONNECTED → INITIAL → ACTIVE;無 add/remove、無重新註冊 |
| M16 | ManagerStatus 內容 | 訊息含全部 entries、state 值正確、source/sink `data_rate_hz` ≈ 實際速率(取自 `lastStatus` 快取);週期 ≈ `statusIntervalMs` |
| M17 | **master heartbeat**:mock master 有回應/無回應 | 有:tick 正常;無:degraded log 一次、本地判定不受影響;回線後 heartbeat 恢復 + re-register 確認 |
| M18 | **per-state callback**:registerSourceStateCallback(TIMEOUT)/registerSinkStateCallback(ACTIVE) | 全部同類 entities 轉移各觸發一次;old/new 正確;覆蓋與 nullptr 清除語意 |
| M19 | **雙閾值休眠**(取代 TIMEOUT-持續邏輯):elapsed 一次越過兩閾值 | entity 直接 DISCONNECTED;CSM 無 per-entry 計時殘留;status 反映 |
| M10 | Handle 在移除後操作 | error code,無 crash、無殘留活動(shutdown 已停止 heartbeat 與 subscription) |
| M11 | 黑白名單:雙向、enable/disable、空白名單=全擋 | 承襲 rv2 案例組 |
| M12 | registerCallback:template 版與字串版、先註冊後建 Sink / 先建後註冊、覆蓋與 unregister | 兩序皆觸發;未註冊 type 回 false |
| M13 | InfoReq 服務 | 列表正確、含 PENDING 排除策略(僅列 ACTIVE) |
| M14 | callback 內呼叫 registerSource(debug build) | assert / 明確錯誤,而非 5s 假逾時 |

---

## 9. `r1::CsmMaster`(v0.5.0 新增)

### 9.1 職責

多 CSM 拓撲下,互訂 status + 點對點通知的連線數為 O(N²) 且每個 CSM 同時要管
多入站/多出站通知(my_note:3 CSM 互為 source/target 的例子)。CsmMaster 集中化:

- 唯一的 status 訂閱者:對每個註冊 CSM 訂閱其 `<name>/status`。
- 配對:以 `controller_name`(全系統唯一)配對 Source-Sink,
  `EntryStatus.manager_name` + `is_source` 定位歸屬。
- **one-shot 通知**:記錄全部 entities 前次狀態,狀態**變化**時(edge)
  對配對雙方 CSM 呼叫 `/<csm_name>/get_notifications` 推送;level 不重發。
- CSM 活性:heartbeat service 收到請求 = CSM 活著;逾時未見 → CSM 失聯處理。
- 黑白名單:以 CSM 名管理可註冊者(對齊 CSM 對 controller 的黑白名單模式)。

獨立執行檔 `csm_master_node`(參數:名稱、逾時、名單);亦可程式庫方式嵌入。

### 9.2 服務與介面

| 介面 | 型別 | 說明 |
|---|---|---|
| `/csm_master/register`(server) | `srv/r1/CsmRegister` | CSM 註冊:req = csm_name;res = response + reason。重複註冊 = 冪等更新(重啟支援) |
| `/csm_master/heartbeat`(server) | `std_srvs/srv/Trigger` | CSM 每 tick 呼叫;master 記 lastSeen;res.success 恆 true(在線證明) |
| `<csm>/status`(subscriber) | `msg/r1/ManagerStatus` | 每註冊 CSM 一條;更新 entities 快取 + 變化偵測 |
| `<csm>/get_notifications`(client) | `srv/r1/CsmNotify` | 變化推送:req.entries = 變化 EntryStatus 清單(含歸屬 manager_name);async best-effort |

```cpp
class CsmMaster
{
public:
    CsmMaster(rclcpp::Node* node, const MasterOptions& opt = {});
    void enableCsmWhitelist(const std::vector<std::string>&);   // + disable / blacklist 對稱
    ...
private:
    struct CsmRecord {
        rclcpp::Subscription<ManagerStatus>::SharedPtr statusSub;
        rclcpp::Client<CsmNotify>::SharedPtr           notifyCli;
        LivenessState  liveness;                  // heartbeat 驅動
        std::map<std::string, EntryStatusT> entries;   // key: controller_name;含前次狀態
    };
    mutable std::shared_mutex csmMtx_;
    std::map<std::string, CsmRecord> csms_;       // key: csm_name
    rclcpp::TimerBase::SharedPtr tick_;           // 週期:heartbeat 逾時掃描 + 通知隊列送出
};

struct MasterOptions {
    int64_t tickIntervalMs   = 200;
    int64_t csmTimeoutMs     = 600;    // heartbeat 未見逾時 → CSM 失聯
};
```

### 9.3 行為細節

- **status 訊息處理**(訂閱 callback):shared_lock 取 CsmRecord → 逐 entry 與快取比對,
  `state` 變化 → 收入變化集(帶新 EntryStatus)→ 更新快取。
  變化集依配對規則展開:該 entry 的 controller_name 之**兩側**(source 側 + sink 側)
  歸屬 CSM 均為通知對象(排除變化來源側自己已知的?不排除——對稱推送,雙方都收,
  接收端自行忽略「本來就是自己」的項目;語意簡單優先,my_note #5 範例即雙方都收)。
- **通知送出**:async `CsmNotify` per 目標 CSM(合併同 tick 內多筆變化);
  不等回應、不重試(one-shot);目標失聯 → log。
- **CSM 失聯**(tick 掃描 heartbeat lastSeen 逾時):
  該 CSM 全部 entries 視為 DISCONNECTED(master 視角)→ 生成變化集通知其配對 CSM
  → 保留 CsmRecord(休眠;heartbeat 恢復即復原,與 entity 的休眠設計原則一致)。
- **註冊**:黑白名單檢查 → 建 statusSub + notifyCli → 冪等(重複註冊重建訂閱,支援 CSM 重啟)。
- Master 自身重啟:CSM 持續週期性呼叫 heartbeat(service 未 ready 時 CSM 進入
  degraded mode);master 回線後收到 heartbeat 與 re-register,重建 record;
  第一輪 status 訊息重建 entries 快取,並以該輪為比對基準,不觸發變化通知,
  避免重啟後產生大量重複通知。

### 9.4 單元測試方法與流程

- gtest;mock CSM = 裸 node(status publisher + get_notifications server + heartbeat/register clients),不依賴真 ControlSignalManager(隔離測 master 邏輯)。

| 案例 | 內容 | 預期 |
|---|---|---|
| CM1 | 註冊 + heartbeat | record 建立;heartbeat 後 lastSeen 更新;Trigger res.success |
| CM2 | 黑白名單 | 拒絕者 register 得 error、無訂閱建立 |
| CM3 | **配對通知**:mock A 發 status(Source X ACTIVE→TIMEOUT) | A 與配對 B 各收到一次 CsmNotify,entries 含 X 新狀態 |
| CM4 | one-shot:同狀態重複 status | 不重發;恢復 ACTIVE → 再發一次 |
| CM5 | CSM 失聯:A heartbeat 停 | A 的 entries 生成 DISCONNECTED 變化,B 收通知;A record 保留 |
| CM6 | A 恢復 heartbeat + status | 通知恢復;冷啟動基準不誤發 |
| CM7 | master 重啟模擬(重建 CsmMaster) | re-register 後首輪 status 不觸發大量變化通知 |
| CM8 | 未配對 entry(只有 Source 無 Sink) | 僅通知歸屬 CSM 自身側;無 crash |
| CM9 | 通知目標 service 不可達 | async 失敗 log;tick 不阻塞 |

---

## 10. `r1::SourceHandle` / `r1::SinkHandle`

### 10.1 職責

使用者唯一持有物。輕量值型別(可拷貝),內部 `weak_ptr` + 主鍵字串。

### 10.2 介面

```cpp
class SourceHandle
{
public:
    SourceHandle() = default;                       // 空 handle
    bool valid() const;                             // weak_ptr 可 lock 且未 shutdown
    const std::string& controllerName() const;

    SendResult send(const void* msg) = delete;      // 型別安全版:
    template<typename msgT> SendResult send(const msgT& msg);   // msgType 不符 → SendResult::NO_TRANSPORT + assert(debug)
    ControlSignalState state() const;               // 失效回 DISCONNECTED
    std::optional<msg::r1::ControlSignalInfo> info() const;
private:
    friend class ControlSignalManager;
    std::weak_ptr<BaseControlSignalSource> src_;
    std::string controllerName_;
};

class SinkHandle
{
public:
    bool valid() const;
    template<typename msgT> bool read(msgT& out) const;
    /// 轉發 Sink::waitForMessage(v0.4.0);handle 失效 → 立即 false。
    /// ⚠ 阻塞:禁止在 ROS callback 內呼叫。
    template<typename msgT> bool waitForMessage(msgT& out, int64_t timeoutNs = 0) const;
    ControlSignalState state() const;
    std::optional<msg::r1::ControlSignalInfo> info() const;
    // callback 註冊統一經由 Manager::registerCallback(型別層級);Handle 不提供,避免生命週期耦合
};
```

### 10.3 行為細節

- 所有操作先 `lock()`;失敗回「失效語意」(state → DISCONNECTED、send → DISCONNECTED、read → false)。
- `send<msgT>` 於 debug build 以 `msgType()` 驗證型別,不符 assert;release 回錯誤碼。
- Handle 不延長物件生命週期(weak_ptr),Manager erase 後即失效,
  物件殘留問題因此不會發生。

### 10.4 單元測試方法與流程

| 案例 | 內容 | 預期 |
|---|---|---|
| H1 | 空 handle | `valid() == false`;所有操作失效語意 |
| H2 | 正常 handle send/read/state | 轉發正確 |
| H3 | 型別不符 send<WrongMsg> | 錯誤碼(release)/ assert(debug) |
| H4 | Manager erase 後 | `valid() == false`;操作失效語意;無 crash |
| H5 | handle 拷貝語意 | 拷貝共享失效狀態 |
| H6 | 併發:handle 操作 vs Manager 移除(壓力) | 無 UAF(ASan/TSan) |

---

## 11. 系統整合測試規劃

### 11.1 需開發的測試 packages

| Package | 內容 | 用途 |
|---|---|---|
| `r1_test_mocks` | **MockManagerNode**:僅實作 `control_signal_manage` service 的可腳本化 node。腳本項:接受 / 拒絕(指定 reason)/ 延遲 N ms 回覆 / **不回覆** / 回覆後立刻斷線。 | 註冊協定故障注入(M5/M6 之整合版) |
| | **MockSourceNode / MockSinkNode**:裸 rclcpp pub/sub/client/server,可設定頻率、突發停止、亂序型別 | 資料面故障注入 |
| | **MockMasterNode**(v0.5.0):可腳本化 master——register 拒絕、heartbeat 不回應、注入任意 CsmNotify 呼叫、攔截記錄 | CSM 側 master 互動與 degraded mode 測試 |
| | **StatusFaultNode**(v0.5.0):可暫停 / 恢復 / 降頻某 CSM 的 status 發布(代理) | master 變化偵測與 CSM 失聯測試 |
| `r1_integration_tests` | `launch_testing` 場景集(下表,含 `csm_master_node` in loop)+ 斷言工具(等待狀態收斂 helper、`ros2 topic`/`service` 探測) | 端到端驗證 |

### 11.2 整合場景

| 場景 | 步驟 | 驗證 |
|---|---|---|
| I1 全流程 | A 註冊 joy → B 自動建 Sink → 高頻 send → read/callback | 資料一致;兩側 ACTIVE;InfoReq 列表正確 |
| I2 多型別多通道 | joy + twist + string,topic + service 混合 | 隔離性;各自狀態獨立 |
| I3 斷線恢復 | 停止發送 → Sink TIMEOUT → 恢復 → ACTIVE | 狀態時序;無誤移除(disconnect_timeout=0) |
| I4 auto-disconnect + 重連 | 同 I3 但 disconnect_timeout 有值;斷流至雙側 DISCONNECTED → 恢復發送 | 兩側轉 DISCONNECTED(entry 保留、status 可觀測);恢復後自動 INITIAL → ACTIVE,無重新註冊 |
| I5 CSM 失聯(master 判定) | kill B node(heartbeat 停) | master 逾時 → 通知 A:B 的 entities DISCONNECTED;A 對應 Source 注入;B 回線 → 通知恢復 |
| I6 target 重啟 | kill B node → 重啟 B(空 Manager)| master 失聯→回線流程;B 已無 entry → A 需 unregister + 重新註冊;驗證 A 側顯式 re-register 流程 |
| I11 status 對帳 | 訂閱兩側 `<name>/status`,對照 InfoReq 與實際狀態 | entries/state/rate 一致;斷線期間 DISCONNECTED 可見 |
| I12 **master 通報鏈**(v0.5.0) | A 停止發送 → B 側 Sink TIMEOUT → master 偵測變化 | master 對 A、B 各推 get_notifications 恰一次;A 的 `setNotificationCallback` 收到、清單正確;恢復後再斷 → 再一次 |
| I14 **master 失聯 degraded**(v0.5.0) | kill master;A、B 之間資料傳輸持續 | 兩側本地判定不受影響;degraded log;master 回線後 heartbeat 與通知恢復,無大量誤發通知 |
| I13 waitForMessage 端到端 | 使用者執行緒 `handle.waitForMessage(out, 1s)`,期間 A 發送 | 即時返回;斷流時 ≈ 1s 逾時 false;unregister 中斷等待 false |
| I7 並發註冊壓力 | 兩個 node 並發向同 target 註冊 100 組(部分同名) | 唯一性不變量成立;成功數 = 唯一名數;無殘留 PENDING |
| I8 response 丟失 | MockManagerNode:接受但不回覆 | A 逾時 error;B(真 Manager 版場景)Sink TTL 回收 |
| I9 惡意/錯誤 payload | MockSourceNode 以錯誤型別發往 channel | Sink 不 crash;型別安全(DDS 層擋掉或 read 型別檢查) |
| I10 壓力 + sanitizer | I1 拉長 × ASan/TSan build | 無 leak / race 報告 |

### 11.3 執行環境

- 每個場景獨立 `ROS_DOMAIN_ID`(launch_testing 配發),避免互相干擾。
- CI:`colcon test` 跑單元;整合場景獨立 job(`colcon test --packages-select r1_integration_tests`)。

### 11.4 Sanitizer 矩陣

| Build | 目標 |
|---|---|
| ASan + LSan | H6 / K10 / M10 / I10(UAF 與 leak 回歸) |
| TSan | LivenessState 全部並發測試、M4 並發註冊壓力 |
| UBSan | 全單元測試 |

---

## 12. 未決事項(下輪討論)

1. **master SPOF 與 HA**(v0.5.0 新):集中式後 master 為單點。degraded mode 保住
   本地判定,但 topic-模式 Source 在 master 失聯期間**完全沒有活性來源**
   (v0.3.0 link 已移除)——是否補本地 fallback(如可選 per-target 直訂)或 master 備援?
2. **priority 語意**:1–94 頻帶與 e-stop=94 約定是否原樣承襲?`controller_priority_type`
   降為文件約定是否可行(rv2_server_control 目前讀該欄位)?
3. **msg/srv 放置**:暫置 `rv2_interfaces/msg/r1/` vs 直接新開 `r1_interfaces` package?
   (migrate 成本與相依耦合的取捨)
4. **status 對帳(reconciliation)**:I6 缺口——target 重啟後 A 側 entry 休眠,
   但 B 已無對應 Sink,不會自動復原。v0.5.0 起 master 持全域 entries 快取,
   是偵測配對缺失的適當位置:master 偵測「Source 存在、配對 Sink 消失」→
   通知 A(或代為觸發 re-REGISTER)。機制歸 master 或 CSM、自動或人工,未決。
8. **rate window 粒度**:`rateWindowNs` 目前為 Manager 全域(ManagerOptions);
   高頻(50Hz joy)與低頻(1Hz)通道並存時是否需 per-entity 配置(Info 欄位)?
5. **DISCONNECTED 休眠 entry 的 GC**:休眠 entry 常駐是 v0.3.0 特性,但永久休眠
   (對向已 unregister / 更名)是否需要可選 purge timeout?(0 = 永不,預設)
6. **`registerSource` 之 async 版本**:提供 future/callback 版避免阻塞需求?
7. **rv2 → r1 migration 路徑**:兩套並存期間,`rv2_server_control` 等下游何時切換、
   是否提供 adapter。
