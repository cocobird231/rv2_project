# My Note

## Changes or Suggestions for R1 CST (Control Signal Transport)

For all components, follow the RAII design rule.
For all flags and concurrent variables, be sure the thread safe, optimize the efficiency using atomic, mutex and shared_lock if possible.

### Source and Sink FSM
1. Evaluate using tinyFSM for context safe and more stability.
2. Evaluate source and sink FSM delete UNKNOWN state and add INITIAL state
3. I think that the DISCONNECTED state can be switch to INITIAL state if the connection is re-established. Avoid frequently add/remove the unstable entries.
4. Provide get status API.
5. Provide register state callback function API for each state. If switch to a new state, the registered callback function will be invoked if set.

### Source and Sink Design Detail

#### Source Design Detail
1. Provide a send API, pass a message to function, publish/request message to Sink and record the function calling time and count. For data recording, use the rolling window approach, window size should be configurable.
2. Provide a non-public calling rate calculating function, calculate the rate using former recorded data, update self status and return status.
3. CSM and Source should be friend class.

#### Sink Design Detail
1. Provide a custom callback function registration API. For subscribe/request message incoming, first record the time and count, then call the custom callback function. For data recording, use the rolling window approach, window size should be configurable.
2. Provide a blocked wait for message function, return while new message income. Maybe use condition variable approach.
3. Provide a non-public calling rate calculating function, calculate the rate using former recorded data, update self status and return status.
4. CSM and Sink should be friend class.

#### Timeout Mechanism for Source ans Sink
1. Two type of timeout:
   - data rate timeout: When message sent/received rate greater than `timeout_ns`, entity goes to TIMEOUT state.
   - disconnected timeout: When message sent/received rate greater than `disconnect_timeout_ns`, entity goes to DISCONNECTED state.
2. Both timeout supports value `0` represents disable timeout check.
3. Since both timeout could be disbled, draw additional FSM for data rate timeout disabled, disconnected timeout disabled and both disabled.
4. Consider the entity could be set to disconnected state by function, FSM should handle this case.


### Control Signal Manager (CSM)

#### Role of CSM

##### Sources Management
1. Provides control signal source registration API.
2. Source's ControlSignalInfo validation.
3. Send request to target CSM with ControlSignalInfo, target CSM should validate ControlSignalInfo and create correspond control signal sink.
4. Provide control signal source handler.
5. Provide control signal source state callback registration API for each state.

##### Sinks Management
1. Received Source registration request from source CSM.
2. Provide per mesage type custom callback function registration API.
3. Validate request ControlSignalInfo, create corresponding Sink.
4. Provide control signal sink handler.
5. Provide control signal sink state callback registration API for each state.

##### Heartbeat Mechanism
1. Run status calculation for managed Sources and Sinks, store the status per entity, and publish the status.
2. If abnormal status occurs, send the request to corresponding CSM with abnormal Sources/Sinks status.
3. Source and target CSM shouldn't subscribe to each other's status topic to avoid complex Sources/Sinks status notification.
4. Instead of subscribing to each other's status topics, CSMs should register to CSM master and send the heartbeats.
5. CSM should provide get notification service `/<csm_name>/get_notifications` for CSM master to send requests for entity state changes.


### New Service: CSM Master
The CSM relation could be complex if multiple CSMs are involved. E.g. for 3 CSMs, each of them could be others source and target CSM at the same time, so one CSM need to host a service and manage two incoming abnormal entity statuses, and send requests two CSM B and CSM C for abnormal entity status at the same time.

To optimize the complexity of CSM notification, a CSM Master service can be introduced to centralize the management and coordination of multiple CSMs.

Following are the draft design for the CSM Master service:
1. Centralized management and coordination of multiple CSMs.
2. CSM master provides a service `/csm_master/heartbeat` for CSMs to request the heartbeat using simple `std_srvs/srv/Trigger.msg` type. This mechanism allows CSMs to send a request during heartbeat to insure CSM master still online (has response), and CSM master ensure the CSMs are alive.
3. CSM master provides a service `/csm_master/register` for CSMs to register themselves with the master.
4. CSM master should have a blacklist and whitelist for managing registered CSMs.
5. For registered CSMs, master should subscribe to their status topics, identify the Source-Sink pairs and their belonging CSM, find the state changed pairs and send notification requests for both belonging CSMs. The notification sending strategy should be one shot, so master should record all entities from all CSMs, send notification to related CSMs only if belonging/paired entity state changed. For example, CSM A have a Source, and target CSM B have a paired Sink, whether Source or Sink state changed, both CSM A and CSM B will receive notifications from CSM master.


## Project Design Scope
The priority field in ControlSignalInfo.msg is required, and it will not affect the control signal transport. The ControlSignalInfo.msg should be general for future used, not just for control server or rv2 project. So for the design concept, it should not be restrict to the control server design, or rv2 system. E.g. the priority should not comment as range 1-94 (the control server ). Our design is 0-100, and 0 for invalid and 100 for highest priority.
For all files, do not writing too much comments, the comment need to be brief and clear. For detial information, please write documents.
Please review current draft, check if there're some control server or rv2 system related content, if so, please remove it and make it general.


## Request for New Design flow
1. For draft, use git control for drafting. Add commitment for every modification, and given a draft version, e.g. v0.1.0 for the very first version.
2. Please commit this draft for the first version, then start implementing the new design flow.
3. This note will be updated as the design evolves. So in addition to read this note, please check git diff to see the new changes.
4. If adding some fixes or documenting changes, use the minor version number.

## Document Writing Guidelines
1. 使用正規的專業術語來敘述，避免使用形容詞、譬喻和口語化。
2. 可以盡量詳細的敘述，不要過於精簡，這會讓閱讀很吃力。
3. 語句要通順，並使用plugins來修飾文筆，讓文章看起來像是人寫的。
4. 撰寫多個應用情境並繪製時序圖、流程圖、呼叫函數流程與說明
   - 一對一CSM，Source端的CSM註冊Source A, B，Target CSM生成Sink A, B, 兩者不同message Type
   - 一對多CSM，Source端的CSM註冊Source A, B，Target A CSM生成Sink A, Target B CSM生成Sink B
   - 多對一CSM，Source A CSM註冊Source A，Source B CSM註冊Source B，Target CSM生成Sink A, B
   - 上述的CSM組合中包含以下應用情境:
      - Source註冊到Sink生成的完整流程
      - Source send interval > timeout和disconnect時的系統反應
      - Source CSM crash時的系統反應
      - Sink CSM crash時的系統反應
      - CSM master crash時的系統反應
   - 分別使用topic模式與service模式進行上述的CSM組合與應用情境描述，並以模式為主要章節區別
