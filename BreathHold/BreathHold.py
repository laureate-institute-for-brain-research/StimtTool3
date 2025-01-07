
import StimToolLib, os, random, operator
from psychopy import visual, core, event, data, gui, sound, prefs

class GlobalVars:
    #This class will contain all module specific global variables
    #This way, all of the variables that need to be accessed in several functions don't need to be passed in as parameters
    #It also avoids needing to declare every global variable global at the beginning of every function that wants to use it
    def __init__(self):
        self.win = None #the window where everything is drawn
        self.clock = None #global clock used for timing
        self.output = None #The output file
        self.msg = None
        self.trial = None #trial number
        self.trial_type = None #current trial type
        self.vas_questions = None
        self.previous_vas_time = 0
        self.marker_range = 998
        self.marker_start_y = -499
        self.marker_start_x = -69
        self.effort_anchors = ['not at all', 'a little', 'moderately', 'a lot', 'extremely']
        self.effort_question_text = 'How hard did you TRY to hold your breath for as long as you could tolerate?'
        


event_types = {'INSTRUCT_ONSET':1,
    'TASK_ONSET':2,
    'BASELINE_BREATHS':3,
    'TRIAL_INSTRUCT_ONSET':4,
    'TRIAL_ONSET':5, 
    'TRIAL_COMPLETE':6,
    'VAS_RATING':7,
    #'MARKER_LOCATION':8,
    'CALIBRATION_1':8,
    'CALIBRATION_2':9,
    'TASK_END':StimToolLib.TASK_END
}
def get_effort_rating():
    #get an effort rating that is on a vas that has the same length and number of anchors as the pain scale used in the cold pressor task
    start_time = g.clock.getTime()
    rating = StimToolLib.get_effort_rating(g, g.effort_question_text)
    now = g.clock.getTime()
    StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['VAS_RATING'], now, now - start_time, rating, g.effort_question_text, True, g.session_params['parallel_port_address'])

    
    
def set_anchor_text(anchor_list): #should be a list of 5 anchors to draw at the appropriate places
    for a, i in zip(anchor_list, range(5)):
        g.anchors[i].setText(a)
def draw_anchors():
    for a in g.anchors:
        a.draw()
def initialize_anchors():
    g.anchors = []
    for i in range(5):
        g.anchors.append(visual.TextStim(g.win,text="",units='pix',pos=[0,g.marker_start_y + 5 + i*250],color=[1,1,1] ,height=30,wrapWidth=int(1600), alignHoriz='left'))
        
def get_vas_ratings():
    get_effort_rating()
    #get all ratings for a trial
    for txt in g.vas_questions:
        rating_start_time = g.clock.getTime()
        this_rating = StimToolLib.get_one_vas_rating(g, txt.rstrip('\n'))
        now = g.clock.getTime()
        StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['VAS_RATING'], now, now - rating_start_time, str(this_rating), txt.rstrip(), g.session_params['signal_parallel'], g.session_params['parallel_port_address'])

def do_one_trial(trial_type, duration):
    
    #g.instructions[int(trial_type)].draw() #may be 0: expiration, 1: inspiration, 2: break
    #g.win.flip()
    if trial_type == '2': #break trial
        #g.instructions[int(trial_type)].draw() #may be 0: expiration, 1: inspiration, 2: break
        if duration < g.previous_vas_time: #don't flash the break screen if the subject took too long on the previous VAS ratings
            return
        g.timed_break.draw()
        g.win.flip()
        break_start = g.clock.getTime()
        StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['TRIAL_ONSET'], break_start, 'NA', 'NA', 'NA', True, g.session_params['parallel_port_address'])
        StimToolLib.just_wait(g.clock, break_start + duration - g.previous_vas_time)
        g.win.flip()
        now = g.clock.getTime()
        StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['TRIAL_COMPLETE'], now, now - break_start, 'NA', 'NA', True, g.session_params['parallel_port_address'])
        return
        
    StimToolLib.run_instructions(os.path.join(os.path.dirname(__file__), 'media', 'instructions', 'BH_baseline.csv'), g)
    StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['BASELINE_BREATHS'], g.clock.getTime(), 'NA', 'NA', 'NA', True, g.session_params['parallel_port_address'])
    g.five_breaths.draw()
    g.win.flip()
    k = event.waitKeys(keyList = ['return'])
    
    
    instruct_onset_time = g.clock.getTime()
    StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['TRIAL_INSTRUCT_ONSET'], instruct_onset_time, 'NA', 'NA', 'NA', True, g.session_params['parallel_port_address'])
    StimToolLib.run_instructions(os.path.join(os.path.dirname(__file__), 'media', 'instructions', 'BH_inhale.csv'), g)
    g.holding.draw() #will be shown when the subject starts holding his breath
    
    start_time = g.clock.getTime()
    StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['TRIAL_ONSET'], start_time, start_time - instruct_onset_time, 'NA', 'NA', True, g.session_params['parallel_port_address'])
    g.win.flip() #shows "Holding" screen
        
    k = event.waitKeys(keyList = ['return'], maxWait=g.run_params['maximum_hold'])
    if not k: #only play the stop sound if the subject made it the full time
        g.stop_sound.play()

    now = g.clock.getTime()
    StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['TRIAL_COMPLETE'], now, now - start_time, 'NA', 'NA', True, g.session_params['parallel_port_address'])
    get_vas_ratings()
    vas_end = g.clock.getTime()
    g.previous_vas_time = vas_end - now #will be used to shorten breaks so they have a minimum amount of time between the previous breath hold and the next trial *including* time spent on ratings
    #now = g.clock.getTime()
    #record trial info
    #StimToolLib.mark_event(g.output, g.trial, g.trial_type, event_types['TRIAL_COMPLETE'], now, now - start_time, 'NA', 'NA', True, g.session_params['parallel_port_address']) 

def run(session_params, run_params):
    global g
    g = GlobalVars()
    g.session_params = session_params
    g.run_params = StimToolLib.get_var_dict_from_file(os.path.dirname(__file__) + '/BH.Default.params', {})
    g.run_params.update(run_params)
    try:
        run_try()
        g.status = 0
    except StimToolLib.QuitException as q:
        g.status = -1
    StimToolLib.task_end(g)
    return g.status
    
    
def run_try():  
#def run_try(SID, raID, scan, resk, run_num='Practice'):
    #joystick.backend='pyglet'
    #nJoysticks=joystick.getNumJoysticks()

    prefs.general['audioLib'] = [u'pyo', u'pygame']
    prefs.general[u'audioDriver'] = [u'ASIO4ALL', u'ASIO', u'Audigy']
    
    
    schedules = [f for f in os.listdir(os.path.dirname(__file__)) if f.endswith('.schedule')]
    if not g.session_params['auto_advance']:
        myDlg = gui.Dlg(title="BH")
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

    #if not g.session_params['vMeter']:
    #    StimToolLib.error_popup('No vMeter Connected/Open')
    
    StimToolLib.general_setup(g)
    
    start_time = data.getDateStr()
    fileName = os.path.join(g.prefix + '.csv')
    g.output = open(fileName, 'w')
    
    sorted_events = sorted(event_types.items(), key=lambda item: item[1])
    g.output.write('Administrator:,' + g.session_params['admin_id'] + ',Original File Name:,' + fileName + ',Time:,' + start_time + ',Event Codes:,' + str(sorted_events) + '\n')
    g.output.write('trial_number,trial_type,event_code,absolute_time,response_time,response,result\n')
    

    trial_types,images,durations,sound_files = StimToolLib.read_trial_structure(schedule_file, g.win, g.msg)
    durations = durations[0]
    
    #g.instructions = []
    #g.instructions.append(visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media', 'instructions', 'BH_E.PNG'), pos=[0,0], units='pix') ) #expiration
    #g.instructions.append(visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media', 'instructions', 'BH_I.PNG'), pos=[0,0], units='pix') ) #inspiration
    
    g.timed_break = visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media', 'instructions', 'BH_B.PNG'), pos=[0,0], units='pix')  #break
    g.holding = visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media', 'instructions', 'BH_H.PNG'), pos=[0,0], units='pix')
    g.ready_to_start = visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media', 'instructions', 'BH_R.PNG'), pos=[0,0], units='pix')
    g.stop_sound = sound.Sound(value=os.path.join(os.path.dirname(__file__), 'media', 'instructions', 'stop_blow.aiff'), volume=g.session_params['instruction_volume'])
    
    g.rating_scale = visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media/rating_scale.bmp'), pos=[0,0], units='pix')
    g.scale_marker = visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media/scale_marker.bmp'), pos=[g.marker_start_x,g.marker_start_y], units='pix', mask=os.path.join(os.path.dirname(__file__),  'media/scale_marker_mask.bmp'))
    
    g.effort_question = visual.TextStim(g.win,text=g.effort_question_text,units='pix',pos=[-800,0],color=[1,1,1] ,height=50,wrapWidth=int(700), alignHoriz='left')
    
    g.five_breaths = visual.ImageStim(g.win, image=os.path.join(os.path.dirname(__file__),  'media/instructions/BH_B_2.PNG'), pos=[0,0], units='pix')
    
    vas_question_file = open(os.path.join(os.path.dirname(__file__),  'VAS_questions.txt'), 'r')
    g.vas_questions = vas_question_file.readlines()
    initialize_anchors()
    set_anchor_text(g.effort_anchors)
    
    StimToolLib.task_start(StimToolLib.BREATH_HOLD_CODE, g)
    

    instruct_start_time = g.clock.getTime()
    StimToolLib.mark_event(g.output, 'NA', 'NA', event_types['INSTRUCT_ONSET'], instruct_start_time, 'NA', 'NA', 'NA', True, g.session_params['parallel_port_address'])
    #StimToolLib.run_instructions(os.path.join(os.path.dirname(__file__), 'media', 'instructions', 'BH_instruct_schedule.csv'), g)
    
    StimToolLib.run_instructions(os.path.join(os.path.dirname(__file__), 'media', 'instructions', 'BH_cal_1.csv'), g)
    now = g.clock.getTime()
    StimToolLib.mark_event(g.output, 'NA', 'NA', event_types['CALIBRATION_1'], now, 'NA', 'NA', 'NA', True, g.session_params['parallel_port_address'])
    StimToolLib.just_wait(g.clock, g.clock.getTime() + 20)
    
    StimToolLib.run_instructions(os.path.join(os.path.dirname(__file__), 'media', 'instructions', 'BH_cal_2.csv'), g)
    now = g.clock.getTime()
    StimToolLib.mark_event(g.output, 'NA', 'NA', event_types['CALIBRATION_2'], now, 'NA', 'NA', 'NA', True, g.session_params['parallel_port_address'])
    StimToolLib.just_wait(g.clock, g.clock.getTime() + 20)
    
    StimToolLib.run_instructions(os.path.join(os.path.dirname(__file__), 'media', 'instructions', 'BH_SU.csv'), g)
    
    
    
    #show_intro_instructions()
    instruct_end_time = g.clock.getTime()
    StimToolLib.mark_event(g.output, 'NA', 'NA', event_types['TASK_ONSET'], instruct_end_time, instruct_end_time - instruct_start_time, 'NA', 'NA', True, g.session_params['parallel_port_address'])
    g.trial = 0    
    print(trial_types)
    print(durations)
    for t, d in zip(trial_types, durations):
        g.trial_type = int(t)
        do_one_trial(t, d)
        g.trial = g.trial + 1
        
    

  
 


