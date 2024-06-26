from opentrons import protocol_api
import time,math
import subprocess


metadata = {
    'protocolName': 'PCR distribute',
    'author': 'Shawn Laursen',
    'description': '''Put 10ml of PCR into 2 x 5ml conical.
                      Robot distributes 100ul to pcr strips.''',
    'apiLevel': '2.18'
    }

def add_parameters(parameters: protocol_api.Parameters):
    parameters.add_str(
        variable_name="song",
        display_name="Song",
        choices=[
            {"display_name": "None", "value": "None"},
            {"display_name": "2001", "value": "2001.mp3"},
            {"display_name": "Puccini", "value": "puccini.mp3"},
            {"display_name": "Verdi", "value": "verdi.mp3"},
            {"display_name": "Mozart", "value": "mozart.mp3"},
            {"display_name": "Haydn", "value": "haydn.mp3"},
            {"display_name": "Beethoven", "value": "beethoven.mp3"},
            {"display_name": "BEP", "value": "get_it_started.mp3"},
            {"display_name": "Rockabye", "value": "rockabye.mp3"},
        ],
        default="None",
    )

def run(protocol):
    music(protocol.params.song, protocol)
    strobe(12, 8, True, protocol)
    setup(protocol)
    distribute(protocol)
    strobe(12, 8, False, protocol)

def strobe(blinks, hz, leave_on, protocol):
    i = 0
    while i < blinks:
        protocol.set_rail_lights(True)
        time.sleep(1/hz)
        protocol.set_rail_lights(False)
        time.sleep(1/hz)
        i += 1
    protocol.set_rail_lights(leave_on)

def setup(protocol):
    #equiptment
    global tips300, p300m, tubes, pcr_strips
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 4)
    p300m = protocol.load_instrument('p300_multi_gen2', 'left',
                                     tip_racks=[tips300])
    tubes = protocol.load_labware('opentrons_15_tuberack_falcon_15ml_conical', 5)
    pcr_strips = protocol.load_labware(
                        'opentrons_96_aluminumblock_nest_wellplate_100ul', 6)
    

    #single tips
    global which_tips300, tip300
    which_tips300 = []
    tip300 = 0
    tip_row_list = ['H','G','F','E','D','C','B','A']
    for i in range(0,96):
        which_tips300.append(tip_row_list[(i%8)]+str(math.floor(i/8)+1))

def pickup_tips(number, pipette, protocol):
    global tip300
   
    if pipette == p300m:
        if (tip300 % number) != 0:
            while (tip300 % 8) != 0:
                tip300 += 1
        tip300 += number-1
        p300m.pick_up_tip(tips300[which_tips300[tip300]])
        tip300 += 1

def distribute(protocol):
    pickup_tips(1, p300m, protocol)
    counter = 0
    for col in range (0,6):
        for row in range(0,8):
            if counter < 100:    
                p300m.aspirate(300, tubes.rows()[0][0].top(-95))
                counter = 300
            p300m.dispense(100, pcr_strips.rows()[row][col])
            counter -= 100
    for col in range (6,12):
        for row in range(0,8):
            if counter < 100:    
                p300m.aspirate(300, tubes.rows()[0][1].top(-95))
                counter = 300
            p300m.dispense(100, pcr_strips.rows()[row][col])
            counter -= 100
    p300m.drop_tip()

def run_quiet_process(command):
    subprocess.Popen('{} &'.format(command), shell=True)

def music(song, protocol):
    print('Speaker')
    print('Next\t--> CTRL-C')
    if song != "None":
        try:
            if not protocol.is_simulating():
                run_quiet_process('mpg123 {}'.format(song))
            else:
                print('Not playing mp3, simulating')
        except KeyboardInterrupt:
            pass
            print()
