
import StimToolLib, os, random, operator
from psychopy import visual, core, event, data, gui, sound
import math
import numpy
import json
from labjack import ljm

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
        self.block_number = 0
        self.last_block = -1
        self.inner_block_trial = 0
        self.selected_slots = []
        self.total_score = 0
        self.blue = '#56B4E9'
        self.orange = '#E69F00'
        self.green = '#009E73'
        self.red = '#FF0000'

event_types = {
    'INSTRUCT_ONSET':1,
    'TASK_ONSET':2,
    'TRIAL_ONSET':3,
    'SELECTION':4,
    'OUTCOME':5,
    'JITTER':6,
    'FIXATION':7,
    'TASK_END':StimToolLib.TASK_END 
    }

def draw_slots_and_text(block_num, min_room, room_size, up_flag, selection):
    if min_room == '1':
        g.minimize.draw()
    else:
        g.maximize.draw()
    
    g.trial_block_num.setText(f"Trial Number: {g.inner_block_trial+1}\nGame Number: {str(int(g.block_number) + 1)}/{g.num_of_blocks}")
    g.score_text.setText(f"Total Points: {g.total_score}")
    g.trial_block_num.draw()
    g.score_text.draw()

    if int(room_size) == g.small_size:
        if up_flag:
            g.short_slot_bar_left_up.draw()
            g.short_slot_handle_left_up.draw()
            g.short_slot_bar_right_up.draw()
            g.short_slot_handle_right_up.draw()
        elif selection == g.run_params['left']:
            g.short_slot_bar_left_down.draw()
            g.short_slot_handle_left_down.draw()
            g.short_slot_bar_right_up.draw()
            g.short_slot_handle_right_up.draw()
        elif selection == g.run_params['right']:
            g.short_slot_bar_left_up.draw()
            g.short_slot_handle_left_up.draw()
            g.short_slot_bar_right_down.draw()
            g.short_slot_handle_right_down.draw()
    else:
        if up_flag:
            g.large_slot_bar_left_up.draw()
            g.large_slot_handle_left_up.draw()
            g.large_slot_bar_right_up.draw()
            g.large_slot_handle_right_up.draw()
        elif selection == g.run_params['left']:
            g.large_slot_bar_left_down.draw()
            g.large_slot_handle_left_down.draw()
            g.large_slot_bar_right_up.draw()
            g.large_slot_handle_right_up.draw()
        elif selection == g.run_params['right']:
            g.large_slot_bar_left_up.draw()
            g.large_slot_handle_left_up.draw()
            g.large_slot_bar_right_down.draw()
            g.large_slot_handle_right_down.draw()


    for lslot in g.left_slots[block_num]:
        lslot.draw()
    for rslot in g.right_slots[block_num]:
        rslot.draw()
    for text in g.selected_slots:
        text.draw()


def do_one_trial(trial_type, fix_duration, post_out_duration, pre_out_duration, reward):
    
    min_room = trial_type.split("_")[0]
    room_size = trial_type.split("_")[1]
    g.block_number = trial_type.split("_")[2]
    forced_choice = trial_type.split("_")[3]
    left_reward = reward.split("_")[0]
    right_reward = reward.split("_")[1]

    if g.block_number != g.last_block:
        g.selected_slots = []
        g.inner_block_trial = 0
    
    # print(f"BLOCK NUM {g.block_number}")
    # print(f"INNER BLOCK TRIAL {g.inner_block_trial}")
    
    # start at top of slot machine (-1 to account for zero indexing)
    active_slot_num = (int(room_size) - 1) - g.inner_block_trial
    # set active slot color and forced choice key list
    if forced_choice == 'L':
        key_list = [g.run_params['left']]
        g.left_slots[g.block_number][active_slot_num].fillColor = g.red
    elif forced_choice == 'R':
        key_list = [g.run_params['right']]
        g.right_slots[g.block_number][active_slot_num].fillColor = g.red
    elif forced_choice == 'X':
        key_list = [g.run_params['left'], g.run_params['right']]
        g.left_slots[g.block_number][active_slot_num].fillColor = g.green
        g.right_slots[g.block_number][active_slot_num].fillColor = g.green

    # Capture the selection
    responded = False
    event.clearEvents()
    StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['TRIAL_ONSET'], g.clock.getTime(), 'NA', 'NA', 'NA', g.session_params['signal_parallel'], g.session_params['parallel_port_address'], g.session_params['signal_serial'], g.session_params['serial_port_address'], g.session_params['baud_rate'])
    start_time = g.clock.getTime()
    while not responded:
        draw_slots_and_text(g.block_number, min_room, room_size, True, None)
        if event.getKeys(["escape"]):
            raise StimToolLib.QuitException()
        resp = event.getKeys(key_list)
        if resp:
            responded = True
            response_time = g.clock.getTime() - start_time
            marked_response = 'left' if resp[0] == g.run_params['left'] else 'right'
            marked_reward = left_reward if resp[0] == g.run_params['left'] else right_reward
            StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['SELECTION'], g.clock.getTime(), response_time, marked_response, marked_reward, g.session_params['signal_parallel'], g.session_params['parallel_port_address'], g.session_params['signal_serial'], g.session_params['serial_port_address'], g.session_params['baud_rate'])
        g.win.flip()
    loop_time = g.clock.getTime() - start_time

    # MARK THE BEGINNING OF PRE OUTCOME JITTER. It includeds the time for performing the operations between here and the just_wait()
    StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['JITTER'], g.clock.getTime(), 'NA', 'NA', 'NA', g.session_params['signal_parallel'], g.session_params['parallel_port_address'], g.session_params['signal_serial'], g.session_params['serial_port_address'], g.session_params['baud_rate'])

    # revert back to normal slot background color
    g.left_slots[g.block_number][active_slot_num].fillColor = 'black'
    g.right_slots[g.block_number][active_slot_num].fillColor = 'black'
    
    # Populate the text
    if resp[0] == g.run_params['left']:
        if min_room == "1":
            g.total_score -= int(left_reward)
            left_reward = "-" + left_reward
        else:
            g.total_score += int(left_reward)
        g.left_texts[g.block_number][active_slot_num].setText(left_reward)
        g.selected_slots.append(g.left_texts[g.block_number][active_slot_num])
        g.right_texts[g.block_number][active_slot_num].setText('X')
        g.selected_slots.append(g.right_texts[g.block_number][active_slot_num])
    if resp[0] == g.run_params['right']:
        if min_room == "1":
            g.total_score -= int(right_reward)
            right_reward = "-" + right_reward
        else:
            g.total_score += int(right_reward)
        g.right_texts[g.block_number][active_slot_num].setText(right_reward)
        g.selected_slots.append(g.right_texts[g.block_number][active_slot_num])
        g.left_texts[g.block_number][active_slot_num].setText('X')
        g.selected_slots.append(g.left_texts[g.block_number][active_slot_num])
    
    StimToolLib.just_wait(g.clock, g.ideal_trial_start + loop_time + pre_out_duration) # final waiting part for PRE OUTCOME JITTER

    draw_slots_and_text(g.block_number, min_room, room_size, False, resp[0])
    g.win.flip()
    StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['OUTCOME'], g.clock.getTime(), 'NA', marked_reward, g.total_score, g.session_params['signal_parallel'], g.session_params['parallel_port_address'], g.session_params['signal_serial'], g.session_params['serial_port_address'], g.session_params['baud_rate'])

    # keep track of blocks and inner blocks trial count
    g.inner_block_trial += 1
    g.last_block = g.block_number
    StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['JITTER'], g.clock.getTime(), 'NA', 'NA', 'NA', g.session_params['signal_parallel'], g.session_params['parallel_port_address'], g.session_params['signal_serial'], g.session_params['serial_port_address'], g.session_params['baud_rate'])
    StimToolLib.just_wait(g.clock, g.ideal_trial_start + loop_time + pre_out_duration + post_out_duration)

    if fix_duration != 0.0:
        g.fixation.draw()
        g.win.flip()
        StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['FIXATION'], g.clock.getTime(), 'NA', 'NA', 'NA', g.session_params['signal_parallel'], g.session_params['parallel_port_address'], g.session_params['signal_serial'], g.session_params['serial_port_address'], g.session_params['baud_rate'])
        StimToolLib.just_wait(g.clock, g.ideal_trial_start + loop_time + pre_out_duration + post_out_duration + fix_duration)
    
    g.ideal_trial_start = g.ideal_trial_start + loop_time + pre_out_duration + post_out_duration + fix_duration

def run(session_params, run_params):
    global g
    g = GlobalVars()
    g.session_params = session_params
    g.run_params = StimToolLib.get_var_dict_from_file(os.path.dirname(__file__) + '/HZ.Default.params', {})
    g.run_params.update(run_params)
    try:
        run_try()
        g.status = 0
    except StimToolLib.QuitException as q:
        g.status = -1
    StimToolLib.task_end(g)
    return g.status
    
def run_try():    
    
    schedules = [f for f in os.listdir(os.path.dirname(__file__)) if f.endswith('.schedule')]
    if not g.session_params['auto_advance']:
        myDlg = gui.Dlg(title="HZ")
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
    g.win.flip()
    g.win.flip()

    trial_types,images,durations,junk = StimToolLib.read_trial_structure(schedule_file, g.win, g.msg)
    fixation_durations = durations[0]
    post_outcome_durations = durations[1]
    pre_outcome_durations = durations[2]
    rewards = junk[0]

    g.num_of_blocks = 0 # using existing logic below to determine number of blocks

    g.left_slots = {}
    g.right_slots = {}
    g.left_texts = {}
    g.right_texts = {}
    posts_size = [0.2, 0.12]
    room_size_list = []
    for trial in trial_types:
        block_num = trial.split("_")[2]
        room_size = trial.split("_")[1]
        room_size_list.append(room_size)
        min_room = trial.split("_")[0]
        if min_room == "1":
            text_color = g.red
        else:
            text_color = 'green'
        if g.left_slots.get(block_num) is None:
            g.num_of_blocks += 1 # Each entry into this location represents a new block
            g.left_slots[block_num] = []
            g.left_texts[block_num] = []
            posts_pos = [0.2, -0.44]
            for x in range(int(room_size)):
                g.left_slots[block_num].append(visual.Rect(g.win, size=posts_size, lineColor=g.blue, fillColor='black', lineWidth=1, pos=[-posts_pos[0],posts_pos[1]], units='norm'))
                g.left_texts[block_num].append(visual.TextStim(g.win, height=0.1, text='', pos=[-posts_pos[0],posts_pos[1]], units='norm', color=text_color))
                posts_pos[1] += posts_size[1]
        if g.right_slots.get(block_num) is None:
            g.right_slots[block_num] = []
            g.right_texts[block_num] = []
            posts_pos = [0.2, -0.44]
            for x in range(int(room_size)):
                g.right_slots[block_num].append(visual.Rect(g.win, size=posts_size, lineColor=g.orange, fillColor='black', lineWidth=1, pos=[posts_pos[0],posts_pos[1]], units='norm'))
                g.right_texts[block_num].append(visual.TextStim(g.win, height=0.1, text='', pos=[posts_pos[0],posts_pos[1]], units='norm', color=text_color))
                posts_pos[1] += posts_size[1]
    
    room_size_list.sort()
    g.small_size = int(room_size_list.pop())
    g.large_size = int(room_size_list.pop(0))
    posts_pos = [0.2, -0.44]

    #set up stimuli
    short_left_pos_start = [(-posts_pos[0] - posts_size[0]/2 + posts_size[0]/8),(posts_pos[1] + posts_size[1]*(g.small_size-1))]
    short_right_pos_start = [(posts_pos[0] + posts_size[0]/2 - posts_size[0]/8),(posts_pos[1] + posts_size[1]*(g.small_size-1))]
    large_left_pos_start = [(-posts_pos[0] - posts_size[0]/2 + posts_size[0]/8),(posts_pos[1] + posts_size[1]*(g.large_size-1))]
    large_right_pos_start = [(posts_pos[0] + posts_size[0]/2 - posts_size[0]/8),(posts_pos[1] + posts_size[1]*(g.large_size-1))]

    g.short_slot_bar_left_up = visual.Line(g.win, lineColor=g.blue, lineWidth=14, start = short_left_pos_start, end = [short_left_pos_start[0] - 0.2, short_left_pos_start[1] + 0.25], units='norm')
    g.short_slot_bar_left_down = visual.Line(g.win, lineColor=g.blue, lineWidth=14, start = short_left_pos_start, end = [short_left_pos_start[0] - 0.2, short_left_pos_start[1] - 0.25], units='norm')
    g.large_slot_bar_left_up = visual.Line(g.win, lineColor=g.blue, lineWidth=14, start = large_left_pos_start, end = [large_left_pos_start[0] - 0.2, large_left_pos_start[1] + 0.25], units='norm')
    g.large_slot_bar_left_down = visual.Line(g.win, lineColor=g.blue, lineWidth=14, start = large_left_pos_start, end = [large_left_pos_start[0] - 0.2, large_left_pos_start[1] - 0.25], units='norm')
    g.short_slot_bar_right_up = visual.Line(g.win, lineColor=g.orange, lineWidth=14, start = short_right_pos_start, end = [short_right_pos_start[0] + 0.2, short_right_pos_start[1] + 0.25], units='norm')
    g.short_slot_bar_right_down = visual.Line(g.win, lineColor=g.orange, lineWidth=14, start = short_right_pos_start, end = [short_right_pos_start[0] + 0.2, short_right_pos_start[1] - 0.25], units='norm')
    g.large_slot_bar_right_up = visual.Line(g.win, lineColor=g.orange, lineWidth=14, start = large_right_pos_start, end = [large_right_pos_start[0] + 0.2, large_right_pos_start[1] + 0.25], units='norm')
    g.large_slot_bar_right_down = visual.Line(g.win, lineColor=g.orange, lineWidth=14, start = large_right_pos_start, end = [large_right_pos_start[0] + 0.2, large_right_pos_start[1] - 0.25], units='norm')

    g.short_slot_handle_left_up = visual.Circle(g.win, lineColor=g.blue, fillColor=g.blue, lineWidth=1, pos= [short_left_pos_start[0] - 0.2, short_left_pos_start[1] + 0.25], units='norm', radius=0.04)
    g.short_slot_handle_left_down = visual.Circle(g.win, lineColor=g.blue, fillColor=g.blue, lineWidth=1, pos= [short_left_pos_start[0] - 0.2, short_left_pos_start[1] - 0.25], units='norm', radius=0.04)
    g.large_slot_handle_left_up = visual.Circle(g.win, lineColor=g.blue, fillColor=g.blue, lineWidth=1, pos= [large_left_pos_start[0] - 0.2, large_left_pos_start[1] + 0.25], units='norm', radius=0.04)
    g.large_slot_handle_left_down = visual.Circle(g.win, lineColor=g.blue, fillColor=g.blue, lineWidth=1, pos= [large_left_pos_start[0] - 0.2, large_left_pos_start[1] - 0.25], units='norm', radius=0.04)
    g.short_slot_handle_right_up = visual.Circle(g.win, lineColor=g.orange, fillColor=g.orange, lineWidth=1, pos= [short_right_pos_start[0] + 0.2, short_right_pos_start[1] + 0.25], units='norm', radius=0.04)
    g.short_slot_handle_right_down = visual.Circle(g.win, lineColor=g.orange, fillColor=g.orange, lineWidth=1, pos= [short_right_pos_start[0] + 0.2, short_right_pos_start[1] - 0.25], units='norm', radius=0.04)
    g.large_slot_handle_right_up = visual.Circle(g.win, lineColor=g.orange, fillColor=g.orange, lineWidth=1, pos= [large_right_pos_start[0] + 0.2, large_right_pos_start[1] + 0.25], units='norm', radius=0.04)
    g.large_slot_handle_right_down = visual.Circle(g.win, lineColor=g.orange, fillColor=g.orange, lineWidth=1, pos= [large_right_pos_start[0] + 0.2, large_right_pos_start[1] - 0.25], units='norm', radius=0.04)

    g.fixation = visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media/fixation.png'), pos=[0,0], units='norm')
    g.maximize = visual.TextStim(g.win, text='Maximize Wins', height=0.1, pos=[0,0.8], units='norm', color='green')
    g.minimize = visual.TextStim(g.win, text='Minimize Losses', height=0.1, pos=[0,0.8], units='norm', color=g.red)
    g.trial_block_num = visual.TextStim(g.win, text='', height=0.1, pos=[0,-0.64], units='norm', color='white')
    g.score_text = visual.TextStim(g.win, text='', height=0.1, pos=[0,-0.82], units='norm', color='green')
    
    start_time = data.getDateStr()
    fileName = os.path.join(g.prefix + '.csv')
    
    g.output = open(fileName, 'w')
    
    sorted_events = sorted(event_types.items(), key=lambda item: item[1])
    g.output.write('Administrator:,' + g.session_params['admin_id'] + ',Original File Name:,' + fileName + ',Time:,' + start_time + ',Parameter File:,' +  param_file + ',Event Codes:,' + str(sorted_events) + '\n')
    g.output.write('trial_number,trial_type,event_code,absolute_time,response_time,response,result\n')
    StimToolLib.task_start(StimToolLib.HORIZON_CODE, g)
    instruct_start_time = g.clock.getTime()
    StimToolLib.mark_event(g.output, 'NA', 'NA', event_types['INSTRUCT_ONSET'], instruct_start_time, 'NA', 'NA', 'NA', g.session_params['signal_parallel'], g.session_params['parallel_port_address'], g.session_params['signal_serial'], g.session_params['serial_port_address'], g.session_params['baud_rate'])

    StimToolLib.run_instructions_keyselect(os.path.join(os.path.dirname(__file__), 'media', 'instructions', g.run_params['instruction_schedule']), g)

    g.trial = 0
    StimToolLib.wait_start(g.win)
    instruct_end_time = g.clock.getTime()
    StimToolLib.mark_event(g.output, 'NA', 'NA', event_types['TASK_ONSET'], instruct_end_time, instruct_end_time - instruct_start_time, 'NA', 'NA', g.session_params['signal_parallel'], g.session_params['parallel_port_address'], g.session_params['signal_serial'], g.session_params['serial_port_address'], g.session_params['baud_rate'])
    g.ideal_trial_start = instruct_end_time

    for t,fd,d1,d2,r in zip(trial_types,fixation_durations,post_outcome_durations,pre_outcome_durations,rewards):
        g.trial_type = t

        do_one_trial(t, fd, d1, d2, r)

        g.trial = g.trial + 1

    g.msg.setColor([-1,-1,-1])
