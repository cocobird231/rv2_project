# My Note

## Changes or Suggestions for R1 CST (Control Signal Transport)

For all components, follow the RAII design rule.
For all flags and concurrent variables, be sure the thread safe, optimize the efficiency using atomic, mutex and shared_lock if possible.

### Source and Sink FSM
1. Evaluate using tinyFSM for context safe and more stability.
2. Evaluate source and sink FSM delete UNKNOWN state and add INITIAL state
3. I think that the DISCONNECTED state can be switch to INITIAL state if the connection is re-established. Avoid frequently add/remove the unstable entries.

### Source and Sink Design Detail

#### Source Design Detail
1. Provide a send API, pass a message to function, publish/request message to Sink and record the function calling time and count.
2. Provide a non-public calling rate calculating function, calculate the rate using former recorded data, update self status and return status.
3. CSM and Source should be friend class.

#### Sink Design Detail
1. Provide a custom callback function registration API. For subscribe/request message incoming, first record the time and count, then call the custom callback function.
2. Provide a blocked wait for message function, return while new message income. Maybe use condition variable approach.
3. Provide a non-public calling rate calculating function, calculate the rate using former recorded data, update self status and return status.
4. CSM and Sink should be friend class.


### Control Signal Manager (CSM)

#### Role of CSM

##### Sources Management
1. Provides control signal source registration API.
2. Source's ControlSignalInfo validation.
3. Send request to target CSM with ControlSignalInfo, target CSM should validate ControlSignalInfo and create correspond control signal sink.
4. Provide control signal source handler.

##### Sinks Management
1. Received Source registration request from source CSM.
2. Provide per mesage type custom callback function registration API.
3. Validate request ControlSignalInfo, create corresponding Sink.
4. Provide control signal sink handler.

##### Heartbeat Mechanism
1. Run status calculation for managed Sources and Sinks, store the status per entity, and publish the status.
2. If abnormal status occurs, send the request to corresponding CSM with abnormal Sources/Sinks status.


## Request for New Design flow
1. For draft, use git control for drafting. Add commitment for every modification, and given a draft version, e.g. v0.1.0 for the very first version.
2. Please commit this draft for the first version, then start implementing the new design flow.
3. This note will be updated as the design evolves. So in addition to read this note, please check git diff to see the new changes.