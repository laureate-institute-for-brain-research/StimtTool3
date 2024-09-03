README for the Horizon Task

# TRIAL STRUCTURE WIN
``` 
    response_time | pre-outcome-jitter        post-outcome-jitter                 
([         Slot Options Shown         ] ---> [   Outcome Shown   ])xROOM-SIZE --> [Post-block fixation]
^                 ^                          ^                                    ^
TRIAL_ONSET    SELECTION                     OUTCOME                              FIXATION
               JITTER                        JITTER
```

# INPUT DETAILS

```
EACH LINE CODES: one trial<br/>
COLUMN 1: TrialTypes - <min-room=0;max-room=1>_<room-size#>_<block-num#>_<left-forced=L;right-forced=R;free-choice=X>
COLUMN 2: Stimuli - Not used
COLUMN 3: Durations - block-fixation post-outcome-jitter pre-outcome-jitter
COLUMN 4: ExtraArgs - left-reward_right-reward

TRIAL ORDER: fixed
```

# OUTPUT DETAILS

```
INSTRUCT_ONSET (1)
response_time: not used
response: not used
result: not used

TASK_ONSET (2)
response_time: time between INSTRUCT_ONSET and TASK_ONSET
response: not used
result: not used

TRIAL_ONSET (3)
response_time: not used
response: not used
result: not used

SELECTION (4)
response_time: Time between trial onset and selection
response: response
result: reward

OUTCOME (5)
response_time: not used
response: reward
result: total score

JITTER (6)
response_time: not used
response: not used
result: not used

FIXATION (7)
response_time: not used
response: not used
result: not used
```

# SERIAL SIGNALING DETAILS
Note: 
A single value is transmitted to mark the onset of an event.
The task output will need to be referenced for event durations.

SERIAL PORT TEST: outputs full range

TASK START: 0xFF -> 0x3C (TASK CODE) -> 0x00
INSTRUCT_ONSET: 0x01 (NOTE: this value will match the event code from the task output)
INSTRUCT_ONSET: 0x02
INSTRUCT_ONSET: 0x03
INSTRUCT_ONSET: 0x04
INSTRUCT_ONSET: 0x05
INSTRUCT_ONSET: 0x06
INSTRUCT_ONSET: 0x07
TASK END: 0xFE