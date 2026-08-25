# My Note

## Changes or Suggestions for R1 CST (Control Signal Transport)

### Source and Sink FSM
1. Evaluate using tinyFSM for context safe and more stability.
2. Evaluate source and sink FSM delete UNKNOWN state and add INITIAL state
3. I think that the DISCONNECTED state can be switch to INITIAL state if the connection is re-established. Avoid frequently add/remove the unstable entries.

### Timeout and Disconnect Design for Sink
1. Each sink's status checked by CSM's heartbeat.
2. Each sink's callback first go into a tiny function to record self data rate, then call custom callback function.
3. CSM publish self status while heartbeat, status includes managed Sources/Sinks etc.. Design the CSM status message type.

## Request for New Design flow
1. For draft, use git control for drafting. Add commitment for every modification, and given a draft version, e.g. v0.1.0 for the very first version.
2. Please commit this draft for the first version, then start implementing the new design flow.
3. This note will be updated as the design evolves. So in addition to read this note, please check git diff to see the new changes.