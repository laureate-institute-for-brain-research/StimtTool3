README for the Cooperation Task

!!! Notes for Operation: This task uses IAPS images that are not intended for public sharing. The following directory will need to be created and
populated with the IAPS image set:
    C:\StimTool3\Cooperation\media\outcome_media\images\

*****************************************************************SUMMARY**************************************************************************

The Cooperation Task (adapted from the three-armed bandit task) presents sets of three faces from validated face image databases and participants 
will repeatedly choose among these faces. Depending on their choice, instead of wins/losses, they will either be shown positive, neutral, or 
negative image/sound combinations. Positive stimuli include calming nature scenes from a previously validated database or positive images from 
the widely used IAPS image dataset, combined with a calming chime sound. The neutral images/sounds consist of neutral IAPS images and a boring 
cowbell sound. The negative images also come from the IAPS database and are combined with an unpleasant screaming sound.

*****************************************************************TRIAL STRUCTURE******************************************************************

    0.5s-1.5s           
[Fixation Shown] -> [Game Room and Faces Shown] -> (
^                   ^
FIXATION_ONSET      BLOCK_ONSET

       response time                    parameter defined time       parameter defined time      parameter defined time    
[    Game Room and Faces Shown    ] -> [possible jittered pause] -> [Speech Bubble Appears] -> [possible jittered pause] ->
^                       ^              ^                            ^                          ^                           
TRIAL_ONSET     SELECTION              JITTER_ONSET                 BUBBLE_ONSET               JITTER_ONSET                

     parameter defined time            parameter defined time 
[Outcome Image and Outcome Sound] -> [possible jittered pause]
^                                    ^                        
OUTCOME_IMAGE_ONSET                  JITTER_ONSET             
OUTCOME_SOUND_ONSET              

)x16

*****************************************************************INPUT DETAILS********************************************************************

EACH LINE CODES: one block
COLUMN 1: <TrialCount>_<order>_<forced-order>_<forced-outcomes>
    order: permutations of [s=safe,g=good,b=bad] defining the [left,middle,right] location of the faces on the screen.
    forced-order: lists of [s,g,b] (EXs. sgb,bgg,gsb,ggs) defining the order that the first 3 faces must be picked in.
    forced-outcomes: lists of [N=neutral,L=loss,W=win] defining the outcomes associated with the forced choices
COLUMN 2: Face images (choice images) for the block (3 space separated paths)
COLUMN 3: Fixation between blocks
COLUMN 4: #_#_#-#_#_#-#_#_# = three dash seperated sets of underscore separated probabilities. The first set is for the good choice, the second 
    is for the safe choice, and the third is for the bad choice. Each set defines the probability of getting a negative outcome, neutral outcome,
    or positive outcome for the choice.
Block order: Fixed

*****************************************************************OUTPUT DETAILS*******************************************************************

INSTRUCT_ONSET (1)
response_time: not used
response: not used
result: not used

TASK_ONSET (2)
response_time: time between INSTRUCT_ONSET and TASK_ONSET
response: not used
result: not used

BLOCK_ONSET (3)
response_time: not used
response: not used
result: face images for block/room

TRIAL_ONSET (4)
response_time: not used
response: not used
result: not used

SELECTION (5)
response_time: time between TRIAL_ONSET and SELECTION
response: response _ <forced choice direction or blank> (EXs. up_M, left_L, right_M, up_, left_, right_)
result: pos, neut, neg

FIXATION_ONSET (6)
response_time: not used
response: not used
result: fixation duration

OUTCOME_IMAGE_ONSET (7)
response_time: not used
response: not used
result: outcome image file

OUTCOME_SOUND_ONSET (8)
response_time: not used
response: not used
result: outcome sound file

AUDIO_ONSET (9) - NOT USED
response_time: not used
response: not used
result: not used

JITTER_ONSET (10)
response_time: not used
response: not used
result: not used

BUBBLE_ONSET (11)
response_time: not used
response: not used
result: not used