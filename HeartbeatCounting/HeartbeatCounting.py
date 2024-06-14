from psychopy import prefs
import StimToolLib, os, random, operator, math
from psychopy import visual, core, event, data, gui, sound
#import VMeter

class GlobalVars:
    #This class will contain all module specific global variables
    #This way, all of the variables that need to be accessed in several functions don't need to be passed in as parameters
    #It also avoids needing to declare every global variable global at the beginning of every function that wants to use it
    def __init__(self):
        self.win = None #the window where everything is drawn
        self.clock = None #global clock used for timing
        self.output = None #The output file
        self.msg = None
        self.volume = 0.5
        self.trial = None #trial number
        self.trial_type = None #current trial type
        #self.vMeter = None
        self.subject_taps = 0
        self.vas_questions = [
        ['How intensely did you feel your heartbeat?', 'How accurate was your performance?', 'How difficult was the previous task?'],
        ['How intensely did you hear the tone?', 'How accurate was your performance?', 'How difficult was the previous task?'],
        ['How intensely did you feel your heartbeat?', 'How accurate was your performance?', 'How difficult was the previous task?'],
        ['How intensely did you feel your heartbeat?', 'How accurate was your performance?', 'How difficult was the previous task?']]


event_types = {'INSTRUCT_ONSET':1,
    'TASK_ONSET':2,
    'TRIAL_INSTRUCT_ONSET':3,
    'TRIAL_ONSET':4, 
    'TONE':5,
    'TAP':6,
    'TAP_DOWN':6,
    'TAP_UP':7,
    'TRIAL_COMPLETE':8,
    'STOP_SCREEN_END':9,
    'VAS_RATING':10,
    'TASK_END':StimToolLib.TASK_END
    }

def decrement_opacities_draw_markers():
    for i in range(len(g.scale_markers)):
        g.scale_markers[i].opacity = max(g.scale_markers[i].opacity - 0.02, 0)
        g.scale_markers[i].draw()
def draw_markers():
    for i in range(len(g.scale_markers)):
        g.scale_markers[i].draw()
def generate_tone_sequence(duration):
    #given a number beats per minute and a duration in seconds, generates times for the tones with inter-tone intervals similar to heart beat intervals
    
    bpm = 80
    rpm = 13
    
    iti_base = 60.0 / bpm #mean time between beats
    period = 60.0 / rpm #simulated respiration period
    rsa_factor = 0.1 #maximum amount RSA can change the ITI (in this case 10%)
    random_max = 0.0375 #maximum jitter from noise in seconds for an ITI (here 5% of the mean iti for 80 bpm)
    
    #ITI = ITI_base * (1 + RSA_factor*sin(t/period)) + noise
    
    tone_times = []
    next_time = 0
    while next_time < duration:
        next_time = next_time + iti_base * (1 + rsa_factor * math.sin( 2 * math.pi * next_time / period)) + random.random() * random_max
        tone_times.append(next_time)
    print(tone_times)
    return tone_times
def get_vas_ratings():
    #get all ratings for a trial
    for txt in g.vas_questions[g.trial_type]:
        rating_start_time = g.clock.getTime()
        this_rating = StimToolLib.get_one_vas_rating(g, txt)
        now = g.clock.getTime()
        StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['VAS_RATING'], now, now - rating_start_time, str(this_rating), txt, g.session_params['signal_parallel'], g.session_params['parallel_port_address'])
        
       
        
def do_one_trial(trial_type, duration):
    #0 for heart guess, 1 for tone, 2 for heart detection, 3 for breath hold heart detection
    #g.instructions[trial_type].draw()
    #g.win.flip()
    
    #k = event.waitKeys(keyList = [g.session_params['right'], 'escape'])
    #if k[0] == 'escape':
    #    raise StimToolLib.QuitException()
    StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['TRIAL_INSTRUCT_ONSET'], g.clock.getTime(),  'NA', 'NA', 'NA', True, g.session_params['parallel_port_address'])
    
    StimToolLib.run_instructions(os.path.join(os.path.dirname(__file__), 'media', 'instructions', g.instructions[trial_type]), g)
    
    
    g.ready[trial_type].draw()
    g.win.flip()
    #StimToolLib.wait_for_tap(g.session_params['vMeter'])
    k = event.waitKeys(keyList = ['escape', g.session_params['down']])
    if k[0] == 'escape':
        raise StimToolLib.QuitException()
    if trial_type == 1: #set up tone times for tone trials
        tone_times = generate_tone_sequence(duration)
        tone_times.reverse() #so that .pop() will start with the first time
        next_tone = tone_times.pop()
    else:
        tone_times = None
        next_tone = float('inf')
    
    if not g.run_params['vis_countdown']:
        g.closed.draw()
        g.win.flip()
    if trial_type != 3: #don't play the countdown for the breath hold trial--subjects will begin the trial at the end of inspiration        
        if not g.run_params['vis_countdown']:
            g.countdown.play()
            StimToolLib.just_wait(g.clock, g.clock.getTime() + g.countdown.getDuration())
        else:
            g.count3.draw()
            g.win.flip()
            StimToolLib.just_wait(g.clock, g.clock.getTime() + 1)
            g.count2.draw()
            g.win.flip()
            StimToolLib.just_wait(g.clock, g.clock.getTime() + 2)
            g.count1.draw()
            g.win.flip()
            StimToolLib.just_wait(g.clock, g.clock.getTime() + 3)
            g.go.draw()
            g.win.flip()
            StimToolLib.just_wait(g.clock, g.clock.getTime() + 4)
            pass
    elif g.run_params['vis_countdown']:
        g.count3.draw()
        g.win.flip()
        StimToolLib.just_wait(g.clock, g.clock.getTime() + 1)
        g.count2.draw()
        g.win.flip()
        StimToolLib.just_wait(g.clock, g.clock.getTime() + 2)
        g.count1.draw()
        g.win.flip()
        StimToolLib.just_wait(g.clock, g.clock.getTime() + 3)
        g.go.draw()
        g.win.flip()
        StimToolLib.just_wait(g.clock, g.clock.getTime() + 4)
        pass
    
    start_time = g.clock.getTime()
    StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['TRIAL_ONSET'], start_time,  'NA', 'NA', 'NA', True, g.session_params['parallel_port_address'])
    trial_taps = 0
    down_time = start_time #keep track of the last time the subject's finger touched down
    up_time = start_time #allow for the subject's finger to start on or off the vMeter
    #g.session_params['vMeter'].read_multiple_events() #clear events to start the trial
    while True: 
        StimToolLib.short_wait()
        now = g.clock.getTime()
        if now - start_time >= duration:
            end_time = now
            break
        if now-start_time >= next_tone: #if it's time to play a tone, play it and setup for the next one
            now = g.clock.getTime()
            g.tone.play()
            StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['TONE'], now, 'NA', 'NA', 'NA', True, g.session_params['parallel_port_address'])
            if tone_times: #grab the next tone time
                next_tone = tone_times.pop()
            else: #all tones have been played
                next_tone = float('inf')
        if event.getKeys(["escape"]):
            raise StimToolLib.QuitException()
        k = event.getKeys([g.session_params['down'], g.session_params['up'], g.session_params['left'], g.session_params['right']])
        if k:
            StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['TAP'], now, 'NA', k[0], 'NA', True, g.session_params['parallel_port_address'])
            trial_taps = trial_taps + 1

            
    stop_time = g.clock.getTime() #end time for this trial (right after a tap could have been recorded)  This will be slightly before the screen changes (~10ms)
    StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['TRIAL_COMPLETE'], stop_time, stop_time - start_time, trial_taps, 'NA', True, g.session_params['parallel_port_address'])
    g.subject_taps = trial_taps
    #g.session_params['vMeter'].clear() #turn off the lights
    g.stop.draw()
    g.win.flip()
    g.stop_sound.play()
    
    k = event.waitKeys(keyList = ['return', 'escape'])
    if k[0] == 'escape':
        raise StimToolLib.QuitException()
    now = g.clock.getTime() 
    StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['STOP_SCREEN_END'], now, now - stop_time, 'NA', 'NA', True, g.session_params['parallel_port_address'])
    get_vas_ratings()

def run(session_params, run_params):
    global g
    g = GlobalVars()
    g.session_params = session_params
    g.run_params = StimToolLib.get_var_dict_from_file(os.path.dirname(__file__) + '/HC.Default.params', {})
    g.run_params.update(run_params)
    try:
        run_try()
        g.status = 0
    except StimToolLib.QuitException as q:
        g.status = -1
    StimToolLib.task_end(g)
    #if g.session_params['vMeter']:
    #    reset_vmeter()
    return g.status
    
#def setup_vmeter():
#    g.session_params['vMeter'].send_config(120) #set to return 127 at touch and 0 at release (119 disables)
#    g.session_params['vMeter'].send_config(123) #disable touch position output--we're only interested in touch time, not location, for this task (124 reenables it)
#    g.session_params['vMeter'].send_config(107) #don't let lights respond to touch--will control them manually and make all light up together regardless of finger position (106 reenables)
#def reset_vmeter():
#    g.session_params['vMeter'].send_config(119) #set to return 127 at touch and 0 at release (119 disables)
#    g.session_params['vMeter'].send_config(124) #disable touch position output--we're only interested in touch time, not location, for this task (124 reenables it)
#    g.session_params['vMeter'].send_config(106) #don't let lights respond to touch--will control them manually and make all light up together regardless of finger position (106 reenables)

def run_try():  
    prefs.general['audioLib'] = [u'pyo', u'pygame']
    prefs.general[u'audioDriver'] = [u'ASIO4ALL', u'ASIO', u'Audigy']
    
    
    schedules = [f for f in os.listdir(os.path.dirname(__file__)) if f.endswith('.schedule')]
    if not g.session_params['auto_advance']:
        myDlg = gui.Dlg(title="HC")
        myDlg.addField('Run Number', choices=schedules, initial=g.run_params['run'])
        myDlg.show()  # show dialog and wait for OK or Cancel
        if myDlg.OK:  # then the user pressed OK
            thisInfo = myDlg.data
        else:
            print('QUIT!')
            return -1#the user hit cancel so exit 
        g.run_params['run'] = thisInfo[0]
    
    schedule_file = os.path.join(os.path.dirname(__file__), g.run_params['run'])
    param_file = g.run_params['run'][0:-9] + '.params' #every .schedule file can (probably should) have a .params file associated with it to specify running parameters
    StimToolLib.get_var_dict_from_file(os.path.join(os.path.dirname(__file__), param_file), g.run_params)
    g.prefix = StimToolLib.generate_prefix(g)
    StimToolLib.general_setup(g)
    
    #VMeter.print_devices()
    #try:
    #    g.vMeter = VMeter.VMeter()
    #except:
    #    StimToolLib.error_popup('Could not open VMeter')
    #if not g.session_params['vMeter']:
    #    StimToolLib.error_popup('No vMeter Connected/Open')
    #StimToolLib.check_retry_vMeter(g)
    #g.session_params['vMeter'].clear() #turn off all the lights
    #setup_vmeter() #for this task, only report touch/release, not location
    trial_types,images,durations,sound_files = StimToolLib.read_trial_structure(schedule_file, g.win, g.msg)
    durations = durations[0]
    
    g.instructions = []
    #g.instructions.append(visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media', 'instructions', 'HC_G.PNG'), pos=[0,0], units='pix') ) #guess
    #g.instructions.append(visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media', 'instructions', 'HC_T.PNG'), pos=[0,0], units='pix') ) #tone
    #g.instructions.append(visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media', 'instructions', 'HC_NG.PNG'), pos=[0,0], units='pix') ) #no guess
    #g.instructions.append(visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media', 'instructions', 'HC_B.PNG'), pos=[0,0], units='pix') ) #breath hold
    if not g.run_params['vis_countdown'] and not g.run_params['new_instructions']:
        g.instructions = ['HC_instruct_G.csv', 'HC_instruct_T.csv', 'HC_instruct_NG.csv', 'HC_instruct_B.csv']
    elif g.run_params['new_instructions']:
        g.instructions = ['HC_new_instruct_1.csv', 'HC_new_instruct_2.csv', 'HC_new_instruct_3.csv', 'HC_new_instruct_4.csv']
    else:
        g.instructions = ['HC_WB_instruct_1.csv', 'HC_WB_instruct_2.csv', 'HC_WB_instruct_3.csv', 'HC_WB_instruct_4.csv']
        
    g.go = visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media', 'CountGo.PNG'), pos=[0,0], units='pix')
    g.count3 = visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media', 'Count3.PNG'), pos=[0,0], units='pix')
    g.count2 = visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media', 'Count2.PNG'), pos=[0,0], units='pix')
    g.count1 = visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media', 'Count1.PNG'), pos=[0,0], units='pix')
        
        
    g.countdown = sound.Sound(value=os.path.join(os.path.dirname(__file__), 'media', 'countdown.aiff'), volume=g.session_params['instruction_volume'])
    
    g.closed = visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media', 'instructions', 'HC_C.PNG'), pos=[0,0], units='pix')
    g.stop = visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media', 'instructions', 'HC_S.PNG'), pos=[0,0], units='pix')
    g.stop_sound = sound.Sound(value=os.path.join(os.path.dirname(__file__), 'media', 'stop.aiff'), volume=g.session_params['instruction_volume'])
    
    g.ready = []
    g.ready.append(visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media', 'instructions', 'HC_R.PNG'), pos=[0,0], units='pix')) #ready to start--all but breath hold trials
    g.ready.append(visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media', 'instructions', 'HC_R.PNG'), pos=[0,0], units='pix')) #ready to start--all but breath hold trials
    g.ready.append(visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media', 'instructions', 'HC_R.PNG'), pos=[0,0], units='pix')) #ready to start--all but breath hold trials
    g.ready.append(visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media', 'instructions', 'HC_B_4.PNG'), pos=[0,0], units='pix')) #ready to start--breath hold trials
    
    g.tone = sound.Sound(value=os.path.join(os.path.dirname(__file__), 'media', 't1000Hz.wav'), volume=0.08)
    
    start_time = data.getDateStr()
    fileName = os.path.join(g.prefix + '.csv')
    g.output = open(fileName, 'w')
    
    sorted_events = sorted(event_types.items(), key=lambda item: item[1])

    g.output.write('Administrator:,' + g.session_params['admin_id'] + ',Original File Name:,' + fileName + ',Time:,' + start_time + ',Parameter File:,' +  param_file + ',Event Codes:,' + str(sorted_events) + '\n')
    g.output.write('trial_number,trial_type,event_code,absolute_time,response_time,response,result\n')
    

    
    StimToolLib.task_start(StimToolLib.HEARTBEAT_CODE, g)

    
    instruct_start_time = g.clock.getTime()
    StimToolLib.mark_event(g.output, 'NA', 'NA', event_types['INSTRUCT_ONSET'], instruct_start_time, 'NA', 'NA', 'NA', True, g.session_params['parallel_port_address'])
    #show_intro_instructions()
    StimToolLib.run_instructions(os.path.join(os.path.dirname(__file__), 'media', 'instructions', g.run_params['instruction_schedule']), g)
    # StimToolLib.run_instructions(os.path.join(os.path.dirname(__file__), 'media', 'instructions', 'HC_instruct_schedule.csv'), g)
    instruct_end_time = g.clock.getTime()
    StimToolLib.mark_event(g.output, 'NA', 'NA', event_types['TASK_ONSET'], instruct_end_time, instruct_end_time - instruct_start_time, 'NA', 'NA', True, g.session_params['parallel_port_address'])
    g.trial = 0
    for t, d in zip(trial_types, durations):
        g.trial_type = int(t)
        do_one_trial(int(t), d)
        g.trial = g.trial + 1
        

  
 


