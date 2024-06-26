from opentrons import protocol_api
import time,math


metadata = {
    'protocolName': '50µL aliquots',
    'author': 'Shawn Laursen',
    'description': '''Put 5ml of protein into 1 x 5ml conical.
                      Robot distributes 50ul to pcr tubes.''',
    'apiLevel': '2.11'
    }

def run(protocol):
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
    global tips300, p300m, tubes, pcr_strips, tempdeck
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 4)
    p300m = protocol.load_instrument('p300_multi_gen2', 'left',
                                     tip_racks=[tips300])
    tubes = protocol.load_labware('opentrons_15_tuberack_falcon_15ml_conical', 5)
    tempdeck = protocol.load_module('temperature module gen2', 10)
    pcr_strips = tempdeck.load_labware(
                        'opentrons_96_aluminumblock_generic_pcr_strip_200ul', 6)
    tempdeck.set_temperature(celsius=4)

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
    for col in range (0,12,2):
        for row in range(0,8):
            if counter < 50:    
                p300m.aspirate(300, tubes.rows()[0][0].top(-95))
                counter = 300
            p300m.dispense(50, pcr_strips.rows()[row][col])
            counter -= 50
    p300m.drop_tip()
    tempdeck.deactivate()

