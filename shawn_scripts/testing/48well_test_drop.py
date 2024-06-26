from opentrons import protocol_api
import time
import sys


metadata = {
    'protocolName': 'test_48well',
    'author': 'Shawn Laursen',
    'description': '''Test of 48well.''',
    'apiLevel': '2.11'
    }

def run(protocol):
    #setup
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 5)
    #plate48_well = protocol.load_labware('hampton_48_wellplate_200ul', 6)
    plate48_drop = protocol.load_labware('hampton_48_wellplate_10ul', 6)
    p300m = protocol.load_instrument('p300_multi_gen2', 'left',
                                     tip_racks=[tips300])
    tips20 = protocol.load_labware('opentrons_96_tiprack_20ul', 4)
    p20m = protocol.load_instrument('p20_multi_gen2', 'right',
                                     tip_racks=[tips20])
    
    # p300m.pick_up_tip()
    # p300m.transfer(20, 
    #                plate48_well.rows()[0][0:4],
    #                plate48_well.rows()[0][1:5], 
    #                new_tip='never')
    # p300m.drop_tip()
    strobe(12, 8, True, protocol)
    p20m.pick_up_tip()
    p20m.transfer(2, 
                   plate48_drop.rows()[0][0:5],
                   plate48_drop.rows()[0][1:6], 
                   new_tip='never')
    p20m.drop_tip()
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
    
 
