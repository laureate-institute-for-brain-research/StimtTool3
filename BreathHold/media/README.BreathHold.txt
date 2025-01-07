README for the Breath Hold Task

*****************************************************************SUMMARY**************************************************************************

This module records data for the Breath Hold task.
The subject is presented with instructions, then there is a single practice trial to become familiar with the rating system.
After that, there are four trials where the subject is to hold his breath as long as possible.
Two trials are after full normal exhalation and two are after vital capacity inhalation

*****************************************************************TRIAL STRUCTURE******************************************************************

[                     instruction slides                    ] -> 
^                   ^              ^                        ^
INSTRUCT_ONSET   CALIBRATION_1   CALIBRATION_2         TASK_ONSET


-> [trial instruction slide] -> [breath hold (HOLDING slide)] ->
   ^                            ^                           ^
 TRIAL_INSTRUCT_ONSET      TRIAL_ONSET                 TRIAL_COMPLETE

 
 -> [break slide] ->
    ^           ^
 TRIAL_ONSET  TRIAL_COMPLETE


-> [VAS question] ->
                ^
           VAS_RATING
*****************************************************************INPUT DETAILS********************************************************************


TRIAL ORDER IS: fixed


*****************************************************************OUTPUT DETAILS*******************************************************************

trial 0 is the practice trial, trial 1 is the trial using the ice bath

INSTRUCT_ONSET (1)
response_time: not used
response: not used
result: not used

TASK_ONSET (2)
response_time: time between INSTRUCT_ONSET and TASK_ONSET
response: not used
result: not used

BASELINE_BREATHS (3)
response_time: not used
response: not used
result: not used

TRIAL_INSTRUCT_ONSET (4)
response_time: not used
response: not used
result: not used

TRIAL_ONSET (5)
response_time: difference between TRIAL_ONSET and TRIAL_INSTRUCT_ONSET (time the instruction slide was displayed--not used for break trials)
response: not used
result: not used

TRIAL_COMPLETE (6)
response_time: difference between TRIAL_COMPLETE and TRIAL_ONSET (breath hold or break duration)
response: not used
result: not used

VAS_RATING (7)
response_time: time to make this rating
response: VAS rating (0-100)
result: question asked

CALIBRATION_1 (8) (99.99% O2)
response_time: not used
response: not used
result: not used

CALIBRATION_2 (9) (13%O2, 9.9%CO2, Bal N2)
response_time: not used
response: not used
result: not used




