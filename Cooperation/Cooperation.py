
import StimToolLib, os, random, operator
from psychopy import visual, core, event, data, gui, sound
import csv
import copy
import numpy
from labjack import ljm

# Cooperation Task Module
## AR 7-2023

class GlobalVars:
    #This class will contain all module specific global variables
    #This way, all of the variables that need to be accessed in several functions don't need to be passed in as parameters
    #It also avoids needing to declare every global variable global at the beginning of every function that wants to use it
    def __init__(self):
        self.win = None #the window where everything is drawn
        self.clock = None #global clock used for timing
        self.output = None #The output file
        self.msg = None
        self.ideal_trial_start = None #ideal time the current trial started
        self.trial = None #trial number
        self.trial_type = None #trial type
        self.old_type = None
        self.outcome_durations = 0
        self.selection_durations = 0 # sum of selection durations within a block
        self.speech_bubble_durations = 0 # sum of speech bubble durations within a block
        self.speech_bubble_duration = 0.5 # duration of speech bubble display for one trial
        self.choice_delay_durations = 0
        self.choice_delay_duration = 0
        self.cb_screen_duration = 0
        self.pos_outcome = []
        self.neg_outcome = []
        self.neu_outcome = []
        self.pos_outcome_counts = [0,0,0] # This keeps track of per block and per face positive outcomes
        self.neg_outcome_counts = [0,0,0] # This keeps track of per block and per face negative outcomes
        self.neu_outcome_counts = [0,0,0] # This keeps track of per block and per face neutral outcomes
        self.pos_outcome_count = 0 # This keeps track of per task outcomes (used for cycling through positive outcome images)
        self.neg_outcome_count = 0 # This keeps track of per task outcomes (used for cycling through negative outcome images)
        self.neu_outcome_count = 0 # This keeps track of per task outcomes (used for cycling through neutral outcome images)
        self.choice_number = 1
        self.game_number = 1
        self.game_total = 0
        self.PLEASANT_COLOR = '#00ff00'
        self.UNPLEASANT_COLOR = '#ff0000' 
        self.PLEASANT_COLOR_2 = '#66ff99' 
        self.UNPLEASANT_COLOR_2 = '#f70546'
        self.lead_inout_flag = True


event_types = {
    'INSTRUCT_ONSET':1,
    'TASK_ONSET':2,
    'BLOCK_ONSET':3, # game room onset / cb type and onset
    'TRIAL_ONSET':4, # decision start in game room
    'SELECTION':5, # selection onset
    'FIXATION_ONSET':6, # fixation onset
    'OUTCOME_IMAGE_ONSET':7, # outcome image
    'OUTCOME_SOUND_ONSET':8, # outcome sound
    'AUDIO_ONSET':9, # instructions audio
    'JITTER_ONSET':10,
    'BUBBLE_ONSET':11,
    'TASK_END':StimToolLib.TASK_END 
    }

# repeating list of outcome images
# constantly increasing indices will eventually start returning values from the beginning of the list
class OutcomeList:
    def __init__(self, image_list):
        self.outcomes = image_list

    def __str__(self):
        return str(self.outcomes)
    
    def __getitem__(self, indices):
        if indices >= len(self.outcomes)-1:
            indices = indices % len(self.outcomes)-1
        return self.outcomes[indices]

def read_coop_trial_structure(schedule_file, win, msg):
    #This function will read a .csv file and parse each line, reading images into memory as necessary
    #Each line should have three commas separating four different groups of values--but any of these might be empty
    #The values should be: TrialTypes, Stimuli, Durations, ExtraArgs
    #Within each group of values, different entries should be separated by spaces, allowing an arbitrary number of stimuli or durations for each trial.
    #This may be useful if you have multiple ITIs within a trial.
    #TrialTypes is whatever coding the particular experiment uses.  These value are returned as strings.
    #Each string in stimuli should point to an image that will be read into memory.
    #Durations indicates whatever duration parameters the experiment requires.  These values will be converted to floats.
    #ExtraArgs is provided as a place to put anything else that might be needed--anything there will be returned as strings.
    #Draw a loading message
    directory = os.path.dirname(schedule_file)
    msg.setText('Loading...')
    msg.alignHoriz = 'center'
    msg.draw() #Draw the message
    win.flip() #Refresh the window 
    types = []
    stimuli = []
    durations = []
    extras = []
    exp_order = csv.reader(open(schedule_file))
    #next(exp_order) #throw away the header
    for idx,i in enumerate(exp_order):
        if idx == 0: continue
        #print(i)
        types.append(i[0])
        s = i[1].split()
        s1 = []
        
        for j in s:
            # print(j)
            s1.append(visual.ImageStim(win, image=os.path.join(directory, j), units='pix')) #load images into memory
        print(s1)
        for thing in s1:
            print(thing.image)
        stimuli.append(s1)
        
        d = i[2].split()
        d1 = []
        for j in d:
            d1.append(float(j)) #convert elements into floats
        durations.append(d1)
        extras.append(i[3].split())
    print(durations)
    #stimuli = map(list, zip(*stimuli)) #convert lists like [[1,2],[2,3],[3,4]] into [[1,2,3],[2,3,4]]
    # stimuli = list(map(list, list(zip(*stimuli)))) # same as above but in python3
    for stuff in stimuli:
        print("NEW ENTRY IN STIMULI")
        print(stuff)
    #durations = map(list, zip(*durations))
    durations = list(map(list, list(zip(*durations))))
    #extras = map(list, zip(*extras))
    extras = list(map(list, list(zip(*extras))))
    print(types)
    print(stimuli)
    print(durations)
    print(extras)
    return types,stimuli,durations,extras

def get_jittered_fixation(run_param_list):
    return random.uniform(run_param_list[0], run_param_list[1])

def show_fixation(trial, duration):
    g.fid_fixation.draw()
    g.win.flip()
    now = g.clock.getTime()
    StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['FIXATION_ONSET'], now, 'NA', 'NA', duration, g.session_params['signal_parallel'], g.session_params['parallel_port_address'], g.session_params['signal_serial'], g.session_params['serial_port_address'], g.session_params['baud_rate'])
    StimToolLib.just_wait(g.clock, (g.ideal_trial_start + g.cb_screen_duration + duration))


# Draws or Removes common game room stimuli
# flag=True=Draw
# flag=false=Remove
def game_room_stimuli(image, trials_in_block, trial_type, flag):
    if flag:
        # g.bg.setAutoDraw(True)
        ## Faces
        image[0].setPos([-0.6,0])
        image[1].setPos([0,0])
        image[2].setPos([0.6,0])
        image[0].setAutoDraw(True)
        image[1].setAutoDraw(True)
        image[2].setAutoDraw(True)
        g.face_1_title.setAutoDraw(True)
        g.face_2_title.setAutoDraw(True)
        g.face_3_title.setAutoDraw(True)
        ## Trial and Block counts
        g.choice_number_numtxt.setText(str(g.choice_number) + "/" + str(trials_in_block))
        g.choice_number_txt.setAutoDraw(True)
        g.choice_number_numtxt.setAutoDraw(True)
        g.game_number_numtxt.setText(str(g.game_number) + "/" + str(g.game_total))
        g.game_number_txt.setAutoDraw(True)
        g.game_number_numtxt.setAutoDraw(True)
        ## Game Type Labels and Scores
        if trial_type == 'pleasant':
            g.game_type_txt.setColor(g.PLEASANT_COLOR)
            g.game_type_txt.setText("Positive Outcome Game")
            g.score_txt.setColor(g.PLEASANT_COLOR_2)
            g.score_txt.setText("Number of Positive Outcomes:")
            g.score_numtxt.setColor(g.PLEASANT_COLOR_2)
            g.pleasant_bottom_txt.setAutoDraw(True)
        elif trial_type == 'unpleasant':
            g.game_type_txt.setColor(g.UNPLEASANT_COLOR)
            g.game_type_txt.setText("Negative Outcome Game")
            g.score_txt.setColor(g.UNPLEASANT_COLOR_2)
            g.score_txt.setText("Number of Negative Outcomes:")
            g.score_numtxt.setColor(g.UNPLEASANT_COLOR_2)
            g.unpleasant_bottom_txt.setAutoDraw(True)
        g.game_type_txt.setAutoDraw(True)
        g.score_txt.setAutoDraw(True)
        g.score_numtxt.setText("0" + "/" + str(trials_in_block))
        g.score_numtxt.setAutoDraw(True)
        g.forced_txt.setAutoDraw(True)
        # for spot_arr in g.spots:
        #     for spot in spot_arr:
        #         spot.setAutoDraw(True)
        # for spot_arr in g.spots_lo:
        #     for spot in spot_arr:
        #         spot.setAutoDraw(True)
    else:
        # g.bg.setAutoDraw(False)
        image[0].setAutoDraw(False)
        image[1].setAutoDraw(False)
        image[2].setAutoDraw(False)
        g.face_1_title.setAutoDraw(False)
        g.face_2_title.setAutoDraw(False)
        g.face_3_title.setAutoDraw(False)
        g.choice_number_txt.setAutoDraw(False)
        g.choice_number_numtxt.setAutoDraw(False)
        g.game_number_txt.setAutoDraw(False)
        g.game_number_numtxt.setAutoDraw(False)
        g.game_type_txt.setAutoDraw(False)
        g.pleasant_bottom_txt.setAutoDraw(False)
        g.unpleasant_bottom_txt.setAutoDraw(False)
        g.score_txt.setAutoDraw(False)
        g.score_numtxt.setAutoDraw(False)
        g.forced_txt.setAutoDraw(False)
        # for spot_arr in g.spots:
        #     for spot in spot_arr:
        #         spot.setAutoDraw(False)
        # for spot_arr in g.spots_lo:
        #     for spot in spot_arr:
        #         spot.setAutoDraw(False)
        # clear score stimuli
        for s_list in g.smiles:
            for s in s_list:
                s.setAutoDraw(False)
        for s_list in g.neutrals:
            for s in s_list:
                s.setAutoDraw(False)
        for s_list in g.frowns:
            for s in s_list:
                s.setAutoDraw(False)

def get_outcome_type(prob, forced_trials_count, forced_outs):
    randnum = random.random()
    if randnum <= float(prob[0]):
        out = 'neg'
        out_sound = g.neg_sound
        speech_bubble_path = 'media/speech_bad.png'
    elif randnum <= float(prob[1]):
        out = 'neut'
        out_sound = g.neu_sound
        speech_bubble_path = 'media/speech_neut.png'
    else:
        out = 'pos'
        out_sound = g.pos_sound
        speech_bubble_path = 'media/speech_good.png'
    
    if forced_trials_count < 3:
        forced_outcome = forced_outs[forced_trials_count]
    else:
        forced_outcome = ''
    
    if forced_outcome == 'W':
        out = 'pos'
        out_sound = g.pos_sound
        speech_bubble_path = 'media/speech_good.png'
    elif forced_outcome == 'N':
        out = 'neut'
        out_sound = g.neu_sound
        speech_bubble_path = 'media/speech_neut.png'
    elif forced_outcome == 'L':
        out = 'neg'
        out_sound = g.neg_sound
        speech_bubble_path = 'media/speech_bad.png'

    return out, speech_bubble_path, out_sound


def do_one_block(type, image, duration, probs):
    # Retrieve trial count, trial type, and probabilities
    trials_in_block = int(type.split('_')[0])
    trial_to_mark = type + " " + probs
    trial_type = type.split('_')[1]
    forced_order = type.split('_')[2]
    forced_outs = type.split('_')[3]
    prob_groups = probs.split("-") # example element: 0.59_0.25_0.16
    # Good group probabilities
    good_prob_neg = float(prob_groups[0].split('_')[2]) # ex. 0.16 = 16% negative outcome 
    good_prob_pos_neut = float(prob_groups[0].split('_')[2]) + float(prob_groups[0].split('_')[1]) # ex. 0.16 + 0.25 = 41% (above is positive outcome 59%, below is neutral outcome 25%)
    # safe group probabilities
    safe_prob_neg = float(prob_groups[1].split('_')[2]) # ex. 0.16 = 16% negative outcome 
    safe_prob_pos_neut = float(prob_groups[1].split('_')[2]) + float(prob_groups[1].split('_')[1]) # ex. 0.16 + 0.25 = 41% (above is positive outcome 59%, below is neutral outcome 25%)
    # bad group probabilities
    bad_prob_neg = float(prob_groups[2].split('_')[2]) # ex. 0.16 = 16% negative outcome 
    bad_prob_pos_neut = float(prob_groups[2].split('_')[2]) + float(prob_groups[2].split('_')[1]) # ex. 0.16 + 0.25 = 41% (above is positive outcome 59%, below is neutral outcome 25%)

    type_code_map = {'g': [good_prob_neg, good_prob_pos_neut], 's': [safe_prob_neg, safe_prob_pos_neut], 'b': [bad_prob_neg, bad_prob_pos_neut]}
    forced_direction_map = {trial_type[0]: 'L', trial_type[1]: 'M', trial_type[2]: 'R'}
    forced_list = [forced_direction_map[forced_order[0]], forced_direction_map[forced_order[1]], forced_direction_map[forced_order[2]]]

    probs1 = type_code_map[trial_type[0]] # left
    probs2 = type_code_map[trial_type[1]] # middle
    probs3 = type_code_map[trial_type[2]] # right
    cb_audio = None

    if g.lead_inout_flag:
        g.lead_inout_flag = False
        g.fid_fixation.draw()
        g.win.flip()
        now = g.clock.getTime()
        StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['FIXATION_ONSET'], now, 'NA', 'NA', g.run_params['lead_inout_duration'], g.session_params['signal_parallel'], g.session_params['parallel_port_address'], g.session_params['signal_serial'], g.session_params['serial_port_address'], g.session_params['baud_rate'])
        StimToolLib.just_wait(g.clock, (g.ideal_trial_start + float(g.run_params['lead_inout_duration'])))
        g.ideal_trial_start += float(g.run_params['lead_inout_duration'])

    # Handle counterbalance game type screens
    if g.game_number == 1:
        StimToolLib.mark_event(g.output, g.trial, 'MAIN_START', event_types['BLOCK_ONSET'], g.clock.getTime(), 'NA', 'NA', trial_to_mark, g.session_params['signal_parallel'], g.session_params['parallel_port_address'], g.session_params['signal_serial'], g.session_params['serial_port_address'], g.session_params['baud_rate'])

    # Reset Choice count
    g.choice_number = 1
    # Reset durations
    g.selection_durations = 0 # sum of selection durations within a block
    g.speech_bubble_durations = 0 # sum of speech bubble durations within a block
    g.outcome_durations = 0
    g.choice_delay_durations = 0

    # FIXATION
    show_fixation(type, duration)

    # Set up and Draw Stimuli
    game_room_stimuli(image, trials_in_block, trial_type, True)

    g.win.flip()
    StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['BLOCK_ONSET'], g.clock.getTime(), 'NA', 'NA', image[0].image + ' | ' + image[1].image + ' | ' + image[2].image, g.session_params['signal_parallel'], g.session_params['parallel_port_address'], g.session_params['signal_serial'], g.session_params['serial_port_address'], g.session_params['baud_rate'])

    # Perform Trials
    forced_trials_count = 0
    for i in range(0, trials_in_block):
        g.choice_number_numtxt.setText(str(g.choice_number) + "/" + str(trials_in_block))
        g.win.flip()
        g.choice_delay_durations += get_jittered_fixation(g.run_params['pre_selection_duration'])
        StimToolLib.just_wait(g.clock, g.ideal_trial_start + g.cb_screen_duration + duration + g.selection_durations + g.speech_bubble_durations + g.outcome_durations + g.choice_delay_durations)
        do_one_trial(trial_type, image, duration, probs1, probs2, probs3, trials_in_block, forced_trials_count, forced_list, forced_outs, trial_to_mark)
        forced_trials_count += 1
        g.trial += 1
        g.choice_number += 1

    # clear stimuli
    game_room_stimuli(image, trials_in_block, trial_type, False)
    # Reset outcome type counts
    g.pos_outcome_counts = [0,0,0]
    g.neg_outcome_counts = [0,0,0]
    g.neu_outcome_counts = [0,0,0]

    g.win.flip()

    # increment block count
    g.game_number += 1
    g.old_type = trial_type

    g.ideal_trial_start = g.ideal_trial_start + g.cb_screen_duration + duration + g.selection_durations + g.speech_bubble_durations + g.outcome_durations + g.choice_delay_durations

def do_one_trial(trial_type, image, duration, probs1, probs2, probs3, trials_in_block, forced_trials_count, forced_list, forced_outs, trial_to_mark):
    StimToolLib.mark_event(g.output, g.trial, trial_to_mark, event_types['TRIAL_ONSET'], g.clock.getTime(), 'NA', 'NA', 'NA', g.session_params['signal_parallel'], g.session_params['parallel_port_address'], g.session_params['signal_serial'], g.session_params['serial_port_address'], g.session_params['baud_rate'])

    # Reset Trial State
    responded = False
    blank_screen = False
    speech_bubble_path = ''
    speech_bubble = g.outcome_speech
    outcome = None
    outcome_sound = None

    pre_selection_duration = get_jittered_fixation(g.run_params['post_outcome_duration'])
    post_selection_duration = get_jittered_fixation(g.run_params['post_selection_duration'])
    post_bubble_duration = get_jittered_fixation(g.run_params['post_bubble_duration'])

    event.clearEvents()

    selection_start = g.clock.getTime()
    g.win.flip()

    if forced_trials_count < 3:
        forced_choice_direction = forced_list[forced_trials_count]
    else:
        forced_choice_direction = ''

    # Response loop
    while (not responded):
        # check for exit from task
        if event.getKeys(["escape"]):
            raise StimToolLib.QuitException()
        
        # check for response
        if forced_choice_direction == 'L':
            resp = event.getKeys([g.session_params['left']])
            g.forced_txt.setText('CHOOSE LEFT')
        elif forced_choice_direction == 'M':
            resp = event.getKeys([g.session_params['up']])
            g.forced_txt.setText('CHOOSE MIDDLE')
        elif forced_choice_direction == 'R':
            resp = event.getKeys([g.session_params['right']])
            g.forced_txt.setText('CHOOSE RIGHT')
        else:
            resp = event.getKeys([g.session_params['left'], g.session_params['right'], g.session_params['up']])
            g.forced_txt.setText('')
        if resp and not responded and not blank_screen: #subject pressed a key and hasn't already responded
            resp_time_to_mark = g.clock.getTime()
            resp_rt_to_mark = g.clock.getTime() - selection_start
            if resp[0] == g.session_params['left'] and forced_choice_direction != 'R' and forced_choice_direction !='M':
                responded = True
                # retrieve outcome type (pos, neg, neut) and path to the proper speech bubble
                outcome_type, speech_bubble_path, outcome_sound = get_outcome_type(probs1, forced_trials_count, forced_outs)
                if outcome_type == 'pos':
                    # Increment counts
                    g.pos_outcome_counts[0] += 1
                    g.pos_outcome_count += 1
                    # Draw next face for meter
                    g.smiles[0][g.pos_outcome_counts[0] - 1].setAutoDraw(True)
                    # Set the outcome using the instance of OutcomeList
                    outcome = g.pos_outcomes[g.pos_outcome_count - 1]
                elif outcome_type == 'neut':
                    # Increment counts
                    g.neu_outcome_counts[0] += 1
                    g.neu_outcome_count += 1
                    # Draw next face for meter
                    g.neutrals[0][g.neu_outcome_counts[0] - 1].setAutoDraw(True)
                    # Set the outcome using the instance of OutcomeList
                    outcome = g.neu_outcomes[g.neu_outcome_count - 1]
                else:
                    g.neg_outcome_counts[0] += 1
                    g.neg_outcome_count += 1
                    g.frowns[0][g.neg_outcome_counts[0] - 1].setAutoDraw(True)
                    outcome = g.neg_outcomes[g.neg_outcome_count - 1]
                g.outcome_speech_left.setImage(os.path.join(os.path.dirname(__file__), speech_bubble_path))
                speech_bubble = g.outcome_speech_left
            if resp[0] == g.session_params['up'] and forced_choice_direction != 'L' and forced_choice_direction !='R':
                responded = True
                outcome_type, speech_bubble_path, outcome_sound = get_outcome_type(probs2, forced_trials_count, forced_outs)
                if outcome_type == 'pos':
                    g.pos_outcome_counts[1] += 1
                    g.pos_outcome_count += 1
                    g.smiles[1][g.pos_outcome_counts[1] - 1].setAutoDraw(True)
                    outcome = g.pos_outcomes[g.pos_outcome_count - 1]
                elif outcome_type == 'neut':
                    g.neu_outcome_counts[1] += 1
                    g.neu_outcome_count += 1
                    g.neutrals[1][g.neu_outcome_counts[1] - 1].setAutoDraw(True)
                    outcome = g.neu_outcomes[g.neu_outcome_count - 1]
                else:
                    g.neg_outcome_counts[1] += 1
                    g.neg_outcome_count += 1
                    g.frowns[1][g.neg_outcome_counts[1] - 1].setAutoDraw(True)
                    outcome = g.neg_outcomes[g.neg_outcome_count - 1]
                g.outcome_speech.setImage(os.path.join(os.path.dirname(__file__), speech_bubble_path))
                speech_bubble = g.outcome_speech
            if resp[0] == g.session_params['right'] and forced_choice_direction != 'L' and forced_choice_direction !='M':
                responded = True
                outcome_type, speech_bubble_path, outcome_sound = get_outcome_type(probs3, forced_trials_count, forced_outs)
                if outcome_type == 'pos':
                    g.pos_outcome_counts[2] += 1
                    g.pos_outcome_count += 1
                    g.smiles[2][g.pos_outcome_counts[2] - 1].setAutoDraw(True)
                    outcome = g.pos_outcomes[g.pos_outcome_count - 1]
                elif outcome_type == 'neut':
                    g.neu_outcome_counts[2] += 1
                    g.neu_outcome_count += 1
                    g.neutrals[2][g.neu_outcome_counts[2] - 1].setAutoDraw(True)
                    outcome = g.neu_outcomes[g.neu_outcome_count - 1]
                else:
                    g.neg_outcome_counts[2] += 1
                    g.neg_outcome_count += 1
                    g.frowns[2][g.neg_outcome_counts[2] - 1].setAutoDraw(True)
                    outcome = g.neg_outcomes[g.neg_outcome_count - 1]
                g.outcome_speech_right.setImage(os.path.join(os.path.dirname(__file__), speech_bubble_path))
                speech_bubble = g.outcome_speech_right
            StimToolLib.mark_event(g.output, g.trial, trial_to_mark, event_types['SELECTION'], resp_time_to_mark, resp_rt_to_mark, resp[0] + "_" + forced_choice_direction, outcome_type, g.session_params['signal_parallel'], g.session_params['parallel_port_address'], g.session_params['signal_serial'], g.session_params['serial_port_address'], g.session_params['baud_rate'])

        if not responded:
            StimToolLib.short_wait()
            g.win.flip()
    
    # if trial_type == 'pleasant':
    #     # set score to sum of positive outcomes across faces
    #     g.score_numtxt.setText(str(g.pos_outcome_counts[0] + g.pos_outcome_counts[1] + g.pos_outcome_counts[2]) + "/" + str(trials_in_block))
    # else:
    #     # set score to sum of negative outcomes across faces
    #     g.score_numtxt.setText(str(g.neg_outcome_counts[0] + g.neg_outcome_counts[1] + g.neg_outcome_counts[2]) + "/" + str(trials_in_block))

    # Draw the speech bubble
    speech_bubble.setAutoDraw(True)
    g.selection_durations += g.clock.getTime() - selection_start
    g.speech_bubble_durations += post_selection_duration
    StimToolLib.mark_event(g.output, g.trial, trial_to_mark, event_types['JITTER_ONSET'], g.clock.getTime(), 'NA', 'NA', 'NA', g.session_params['signal_parallel'], g.session_params['parallel_port_address'], g.session_params['signal_serial'], g.session_params['serial_port_address'], g.session_params['baud_rate'])
    StimToolLib.just_wait(g.clock, g.ideal_trial_start + g.cb_screen_duration + duration + g.selection_durations + g.speech_bubble_durations + g.outcome_durations + g.choice_delay_durations)
    g.win.flip()
    g.speech_bubble_durations += g.speech_bubble_duration
    StimToolLib.mark_event(g.output, g.trial, trial_to_mark, event_types['BUBBLE_ONSET'], g.clock.getTime(), 'NA', 'NA', 'NA', g.session_params['signal_parallel'], g.session_params['parallel_port_address'], g.session_params['signal_serial'], g.session_params['serial_port_address'], g.session_params['baud_rate'])
    while g.clock.getTime() < g.ideal_trial_start + g.cb_screen_duration + duration + g.selection_durations + g.speech_bubble_durations + g.outcome_durations + g.choice_delay_durations:
        StimToolLib.short_wait()
        g.win.flip()
    speech_bubble.setAutoDraw(False)
    
    # Draw the outcome image and curtain (to hide the game room)
    g.outcome_durations += post_bubble_duration
    StimToolLib.mark_event(g.output, g.trial, trial_to_mark, event_types['JITTER_ONSET'], g.clock.getTime(), 'NA', 'NA', 'NA', g.session_params['signal_parallel'], g.session_params['parallel_port_address'], g.session_params['signal_serial'], g.session_params['serial_port_address'], g.session_params['baud_rate'])
    StimToolLib.just_wait(g.clock, g.ideal_trial_start + g.cb_screen_duration + duration + g.selection_durations + g.speech_bubble_durations + g.outcome_durations + g.choice_delay_durations)
    g.curtain.setAutoDraw(True)
    outcome.setAutoDraw(True)
    outcome_sound.play()
    g.outcome_durations += g.run_params['outcome_duration']
    StimToolLib.mark_event(g.output, g.trial, trial_to_mark, event_types['OUTCOME_IMAGE_ONSET'], g.clock.getTime(), 'NA', 'NA', outcome.image, g.session_params['signal_parallel'], g.session_params['parallel_port_address'], g.session_params['signal_serial'], g.session_params['serial_port_address'], g.session_params['baud_rate'])
    StimToolLib.mark_event(g.output, g.trial, trial_to_mark, event_types['OUTCOME_SOUND_ONSET'], g.clock.getTime(), 'NA', 'NA', outcome_sound.name, g.session_params['signal_parallel'], g.session_params['parallel_port_address'], g.session_params['signal_serial'], g.session_params['serial_port_address'], g.session_params['baud_rate'])
    while g.clock.getTime() < g.ideal_trial_start + g.cb_screen_duration + duration + g.selection_durations + g.speech_bubble_durations + g.outcome_durations + g.choice_delay_durations:
        StimToolLib.short_wait()
        g.win.flip()
    outcome_sound.stop()
    outcome.setAutoDraw(False)
    g.win.flip()
    g.outcome_durations += pre_selection_duration
    StimToolLib.mark_event(g.output, g.trial, trial_to_mark, event_types['JITTER_ONSET'], g.clock.getTime(), 'NA', 'NA', 'NA', g.session_params['signal_parallel'], g.session_params['parallel_port_address'], g.session_params['signal_serial'], g.session_params['serial_port_address'], g.session_params['baud_rate'])
    StimToolLib.just_wait(g.clock, g.ideal_trial_start + g.cb_screen_duration + duration + g.selection_durations + g.speech_bubble_durations + g.outcome_durations + g.choice_delay_durations)
    g.curtain.setAutoDraw(False)
    
    
def run(session_params, run_params):
    global g
    g = GlobalVars()
    g.session_params = session_params
    g.run_params = StimToolLib.get_var_dict_from_file(os.path.dirname(__file__) + '/Cooperation.Default.params', {})
    g.run_params.update(run_params)
    try:
        run_try()
        g.status = 0
    except StimToolLib.QuitException as q:
        g.status = -1
    StimToolLib.task_end(g)
    return g.status
    
def run_try():

    print("\n================================================================")
    print("============================ NEW RUN ============================")
    print("================================================================\n")
    
    schedules = [f for f in os.listdir(os.path.dirname(__file__)) if f.endswith('.schedule')]
    if not g.session_params['auto_advance']:
        myDlg = gui.Dlg(title="COOP")
        myDlg.addField('Run Number', choices=schedules, initial=g.run_params['run'])
        myDlg.show()  # show dialog and wait for OK or Cancel
        if myDlg.OK:  # then the user pressed OK
            thisInfo = myDlg.data
        else:
            print('QUIT!')
            return -1 #the user hit cancel so exit 
        g.run_params['run'] = thisInfo[0]
    
    
    param_file = g.run_params['run'][0:-9] + '.params' #every .schedule file can (probably should) have a .params file associated with it to specify running parameters (including part of the output filename)

    StimToolLib.get_var_dict_from_file(os.path.join(os.path.dirname(__file__), param_file), g.run_params)
    g.prefix = StimToolLib.generate_prefix(g)
    schedule_file = os.path.join(os.path.dirname(__file__), g.run_params['run'])
    StimToolLib.general_setup(g)

    trial_types,images,durations,junk = read_coop_trial_structure(schedule_file, g.win, g.msg)
    durations = durations[0] #durations of the ITIs
    probabilities = junk[0]
    g.game_total = len(trial_types) # Total number of blocks/games

    # Create special lists of possible outcome images for each category (positive, negative, neutral) 
    trial_types2,pos_outcomes,durations2,junk2 = StimToolLib.read_trial_structure(os.path.join(os.path.dirname(__file__), g.run_params['pos_media']), g.win, g.msg)
    trial_types2,neg_outcomes,durations2,junk2 = StimToolLib.read_trial_structure(os.path.join(os.path.dirname(__file__), g.run_params['neg_media']), g.win, g.msg)
    trial_types2,neu_outcomes,durations2,junk2 = StimToolLib.read_trial_structure(os.path.join(os.path.dirname(__file__), g.run_params['neut_media']), g.win, g.msg)
    pos_outcomes[0]
    neg_outcomes[0]
    neu_outcomes[0]
    image_scale = 0.8
    for img in pos_outcomes[0]:
        img.units = 'norm'
        ratio = img.size[0] / img.size[1]
        if ratio >= 1:
            img.size = [image_scale, image_scale*ratio]
        else:
            img.size = [image_scale*ratio, image_scale]
    for img in neg_outcomes[0]:
        img.units = 'norm'
        ratio = img.size[0] / img.size[1]
        if ratio >= 1:
            img.size = [image_scale, image_scale*ratio]
        else:
            img.size = [image_scale*ratio, image_scale]
    for img in neu_outcomes[0]:
        img.units = 'norm'
        ratio = img.size[0] / img.size[1]
        if ratio >= 1:
            img.size = [image_scale, image_scale*ratio]
        else:
            img.size = [image_scale*ratio, image_scale]
    g.pos_outcomes_list = pos_outcomes[0]
    g.neg_outcomes_list = neg_outcomes[0]
    g.neu_outcomes_list = neu_outcomes[0]
    g.pos_outcomes = OutcomeList(g.pos_outcomes_list)
    g.neg_outcomes = OutcomeList(g.neg_outcomes_list)
    g.neu_outcomes = OutcomeList(g.neu_outcomes_list)

    #set up stimuli
    ## BG
    g.screen_ratio = int(g.session_params['screen_x']) / int(g.session_params['screen_y'])
    g.bg = visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media/background.jpg'), pos=[0,0], units='pix')
    ## Fixation
    g.fid_fixation = visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media/fid_fixation.png'), pos=[0,0], units='norm')
    ## Sounds
    g.pos_sound = sound.Sound(value=os.path.join(os.path.dirname(__file__), 'media/pos.aiff'), name="positive sound", volume=1)
    g.neu_sound = sound.Sound(value=os.path.join(os.path.dirname(__file__), 'media/neut.aiff'), name="neutral sound", volume=1)
    g.neg_sound = sound.Sound(value=os.path.join(os.path.dirname(__file__), 'media/neg.aiff'), name="negative sound", volume=1)
    ## CB Type Screens
    g.run1_pleasant = visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media/instructions/Slide26.jpeg'), units='norm') # run 1 block 2 pleasant
    g.run1_pleasant_sound = sound.Sound(value=os.path.join(os.path.dirname(__file__), 'media/instructions/CooperationTaskInstructionsSlide_BeforeBlock2_positive.aiff'), volume=1)
    g.run1_unpleasant = visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media/instructions/Slide25.jpeg'), units='norm') # run 1 block 2 unpleasant
    g.run1_unpleasant_sound = sound.Sound(value=os.path.join(os.path.dirname(__file__), 'media/instructions/CooperationTaskInstructionsSlide_BeforeBlock2_negative.aiff'), volume=1)
    g.run2_pleasant = visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media/instructions/Slide28.jpeg'), units='norm') # run 2 last pleasant
    g.run2_pleasant_sound = sound.Sound(value=os.path.join(os.path.dirname(__file__), 'media/instructions/CooperationTaskInstructionsSlide_BeforeLast_positive.aiff'), volume=1)
    g.run2_unpleasant = visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media/instructions/Slide27.jpeg'), units='norm') # run 2 last unpleasant
    g.run2_unpleasant_sound = sound.Sound(value=os.path.join(os.path.dirname(__file__), 'media/instructions/CooperationTaskInstructionsSlide_BeforeLast_negative.aiff'), volume=1)
    ## Game Room Stimuli
    ### Faces
    g.face_1_title = visual.TextStim(g.win, text='1', units='norm', pos=[-0.6, 0.3], height=0.1, color='white')
    g.face_2_title = visual.TextStim(g.win, text='2', units='norm', pos=[0.0, 0.3], height=0.1, color='white')
    g.face_3_title = visual.TextStim(g.win, text='3', units='norm', pos=[0.6, 0.3], height=0.1, color='white')
    ### Game and Trial counts
    g.choice_number_txt = visual.TextStim(g.win, text='Choice Number: ', units='norm', pos=[-0.82, 0.8], height=0.06, color='white')
    g.choice_number_numtxt = visual.TextStim(g.win, text='1', units='norm', pos=[-0.63, 0.8], height=0.06, color='white')
    g.game_number_txt = visual.TextStim(g.win, text='Game Number: ', units='norm', pos=[-0.827, 0.87], height=0.06, color='white')
    g.game_number_numtxt = visual.TextStim(g.win, text='1', units='norm', pos=[-0.63, 0.87], height=0.06, color='white')
    g.forced_txt = visual.TextStim(g.win, text='CHOOSE LEFT', units='norm', pos=[0.0, 0.45], height=0.15, color='white')
    ### Game Type Display
    g.game_type_txt = visual.TextStim(g.win, text='Positive Outcome Games', units='norm', pos=[0.66, 0.86], height=0.08, color=g.PLEASANT_COLOR)
    ### Bottom Text
    g.pleasant_bottom_txt = visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media/pleasant_text_bottom.png'), pos=[0,-0.7], size=[1.1,0.2], units='norm')
    g.unpleasant_bottom_txt = visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media/unpleasant_text_bottom.png'), pos=[0,-0.7], size=[1.1,0.2], units='norm')
    ### Top Text Scoring
    g.score_txt = visual.TextStim(g.win, text='Number of Positive Outcomes:', units='norm', pos=[0.60, 0.76], height=0.06, color=g.PLEASANT_COLOR_2)
    g.score_numtxt = visual.TextStim(g.win, text='1', units='norm', pos=[0.88, 0.76], height=0.06, color=g.PLEASANT_COLOR_2)
    ### Curtain (to hide game room for outcome display)
    g.curtain = visual.Rect(g.win, units='norm', fillColor='black', lineColor='black', size=[2,2])
    ### Speech Bubbles 
    g.outcome_speech_left = visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media/speech_good.png'), pos=[-0.40,0.11], size=[0.3,0.39], units='norm')
    g.outcome_speech = visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media/speech_good.png'), pos=[0.20,0.11], size=[0.3,0.39], units='norm')
    g.outcome_speech_right = visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media/speech_good.png'), pos=[0.80,0.11], size=[0.3,0.39], units='norm')
    ### Face Score Meters
    g.smiles = [[],[],[]]
    g.neutrals = [[],[],[]]
    g.frowns = [[],[],[]]
    g.spots = [[],[],[]]
    g.spots_lo = [[],[],[]]
    start_x1 = -0.865
    start_x2 = -0.265
    start_x3 = 0.335
    for i in range(0,int(trial_types[0].split('_')[0])):
        # add smiles
        g.smiles[0].append(visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media/smile.png'), pos=[start_x1,-0.3], units='norm'))
        g.smiles[1].append(visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media/smile.png'), pos=[start_x2,-0.3], units='norm'))
        g.smiles[2].append(visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media/smile.png'), pos=[start_x3,-0.3], units='norm'))
        # add neutrals
        g.neutrals[0].append(visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media/neutral.png'), pos=[start_x1,-0.37], units='norm'))
        g.neutrals[1].append(visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media/neutral.png'), pos=[start_x2,-0.37], units='norm'))
        g.neutrals[2].append(visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media/neutral.png'), pos=[start_x3,-0.37], units='norm'))
        #add frowns
        g.frowns[0].append(visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media/frown.png'), pos=[start_x1,-0.44], units='norm'))
        g.frowns[1].append(visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media/frown.png'), pos=[start_x2,-0.44], units='norm'))
        g.frowns[2].append(visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media/frown.png'), pos=[start_x3,-0.44], units='norm'))
        #add spots
        # g.spots[0].append(visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media/spots.jpg'), pos=[start_x1,-0.3], units='norm'))
        # g.spots[1].append(visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media/spots.jpg'), pos=[start_x2,-0.3], units='norm'))
        # g.spots[2].append(visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media/spots.jpg'), pos=[start_x3,-0.3], units='norm'))
        # g.spots_lo[0].append(visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media/spots.jpg'), pos=[start_x1,-0.37], units='norm'))
        # g.spots_lo[1].append(visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media/spots.jpg'), pos=[start_x2,-0.37], units='norm'))
        # g.spots_lo[2].append(visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media/spots.jpg'), pos=[start_x3,-0.37], units='norm'))
        # adjust positions
        start_x1 += 0.03
        start_x2 += 0.03
        start_x3 += 0.03

    start_time = data.getDateStr()
    fileName = os.path.join(g.prefix + '.csv')
    
    g.output = open(fileName, 'w')
    
    sorted_events = sorted(event_types.items(), key=lambda item: item[1])
    g.output.write('Administrator:,' + g.session_params['admin_id'] + ',Original File Name:,' + fileName + ',Time:,' + start_time + ',Parameter File:,' +  param_file + ',Event Codes:,' + str(sorted_events) + '\n')
    g.output.write('trial_number,trial_type,event_code,absolute_time,response_time,response,result\n')
    StimToolLib.task_start(StimToolLib.FLIGHT_INIT_DIST_CODE, g)
    instruct_start_time = g.clock.getTime()
    StimToolLib.mark_event(g.output, 'NA', 'NA', event_types['INSTRUCT_ONSET'], instruct_start_time, 'NA', 'NA', 'NA', g.session_params['signal_parallel'], g.session_params['parallel_port_address'], g.session_params['signal_serial'], g.session_params['serial_port_address'], g.session_params['baud_rate'])

    StimToolLib.run_instructions(os.path.join(os.path.dirname(__file__), 'media', 'instructions', g.run_params['instruction_schedule']), g)

    g.trial = 0
    StimToolLib.wait_start(g.win)
    instruct_end_time = g.clock.getTime()
    StimToolLib.mark_event(g.output, 'NA', 'NA', event_types['TASK_ONSET'], instruct_end_time, instruct_end_time - instruct_start_time, 'NA', 'NA', g.session_params['signal_parallel'], g.session_params['parallel_port_address'], g.session_params['signal_serial'], g.session_params['serial_port_address'], g.session_params['baud_rate'])
    g.ideal_trial_start = instruct_end_time

    for t, i, d, p in zip(trial_types, images, durations, probabilities):
            
        i[0].units = 'norm'
        i[0].size = (g.run_params['image_x'], g.run_params['image_y']) #set stimulus image size
        i[1].units = 'norm'
        i[1].size = (g.run_params['image_x'], g.run_params['image_y']) #set stimulus image size
        i[2].units = 'norm'
        i[2].size = (g.run_params['image_x'], g.run_params['image_y']) #set stimulus image size
        
        do_one_block(t, i, d, p)
        # g.trial += 1

    g.fid_fixation.draw()
    g.win.flip()
    now = g.clock.getTime()
    StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['FIXATION_ONSET'], now, 'NA', 'NA', g.run_params['lead_inout_duration'], g.session_params['signal_parallel'], g.session_params['parallel_port_address'], g.session_params['signal_serial'], g.session_params['serial_port_address'], g.session_params['baud_rate'])
    StimToolLib.just_wait(g.clock, (g.ideal_trial_start + float(g.run_params['lead_inout_duration'])))
    g.ideal_trial_start += float(g.run_params['lead_inout_duration'])
    
    g.msg.setColor([-1,-1,-1])

  
 


