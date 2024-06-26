from opentrons import protocol_api
import time
import sys
import math


metadata = {
    'protocolName': 'BCA (Pierce) - manual load, 2 samples',
    'author': 'Shawn Laursen',
    'description': '''This protocol will perform the Pierce BCA protocol.
                      Place 500ul of 2mg/ml BSA in A1 of Temp deck 24well.
                      Place 2 x 8 strip tubes in 96well aluminum block.
                      Place 25ul protein in wells of 3rd column of 96well plate.
                      Place dilution buffer in column 1 of trough.
                      Place 200ul x # samples + 5000ul of mixed BCA reagent
                      in column 2 of trough. Robot will make BSA standard dilution
                      in first 2 columns specified, put 60ul your protein(s) in
                      first tube of third (and on strips). 
                      Robot will add 200ul of working reagent to each well (25ul 
                      of protein is used in all wells). Don't forget to alter the 
                      program with where to start on the 96well plate (indexed
                      from 0) Dilutions are: 2, 1.4, 0.8, 0.2, 0.14, 0.08, 0.02, 0.
                      ''',
    'apiLevel': '2.11'
    }

def run(protocol):
    num_samples = 2
    well_96start = 9 #index from 0

    strobe(12, 8, True, protocol)
    setup(well_96start, protocol)
    make_standards(protocol)
    add_wr(num_samples, protocol)
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

def setup(well_96start, protocol):
    #equiptment
    global tips300, tips300_2, trough, p300m, plate96, pcr_strips
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 4)
    tips300_2 = protocol.load_labware('opentrons_96_tiprack_300ul', 8)
    trough = protocol.load_labware('nest_12_reservoir_15ml', '2')
    p300m = protocol.load_instrument('p300_multi_gen2', 'left',
                                     tip_racks=[tips300, tips300_2])
    p300m.flow_rate.aspirate = 40
    p300m.flow_rate.dispense = 40
    plate96 = protocol.load_labware('costar_96_wellplate_200ul', 5)
    pcr_strips = protocol.load_labware(
                 'opentrons_96_aluminumblock_generic_pcr_strip_200ul', 6)
    tempdeck = protocol.load_module('temperature module gen2', 10)
    global temp_buffs
    temp_buffs = tempdeck.load_labware(
                 'opentrons_24_aluminumblock_nest_1.5ml_snapcap')

    global buffer, working, working1, working2, bsa
    buffer = trough.wells()[0]
    working = trough.wells()[1]
    working1 = trough.wells()[2]
    bsa = temp_buffs.wells_by_name()['A1'].bottom(-2)

    global start_96well
    start_96well = well_96start

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
        if tip300 < 96:
            p300m.pick_up_tip(tips300[which_tips300[tip300]])
        else:
            p300m.pick_up_tip(tips300_2[which_tips300[tip300-96]])
        tip300 += 1

def make_standards(protocol):
    dilutants = [30,60,180,180,180,180,100]
    for strip in [0,1]:
        pickup_tips(1, p300m, protocol)
        count = 1
        for dilute in dilutants:
            p300m.aspirate(dilute, buffer)
            p300m.dispense(dilute, pcr_strips.rows()[count][strip])
            count += 1
        p300m.drop_tip()

        count = 0
        standards = [[100, bsa],
                     [70, bsa],
                     [40, bsa],
                     [20, bsa]]

        for standard in standards:
            pickup_tips(1, p300m, protocol)
            p300m.aspirate(standard[0], standard[1])
            p300m.dispense(standard[0], pcr_strips.rows()[count][strip])
            p300m.mix(10,80)
            p300m.drop_tip()
            count += 1
        
        pickup_tips(3, p300m, protocol)
        p300m.aspirate(20, pcr_strips.rows()[1][strip])
        p300m.dispense(20, pcr_strips.rows()[4][strip])
        p300m.mix(10,160)
        p300m.drop_tip()
        count += 1

        pickup_tips(8, p300m, protocol)
        p300m.transfer(25, pcr_strips.rows()[0][strip],
                       plate96.rows()[0][start_96well+strip],
                       new_tip='never')
        p300m.drop_tip()

def add_wr(num_samples, protocol):
    pickup_tips(8, p300m, protocol)
    for col in range(start_96well, start_96well+2):
        p300m.transfer(200, working, plate96.rows()[0][col].top(),
                         disposal_volume=0, new_tip='never',
                         blow_out='true', blowout_location='destination well')
    p300m.drop_tip()
    pickup_tips(num_samples, p300m, protocol)    
    p300m.transfer(200, working, plate96.rows()[0][start_96well+2].top(),
                         disposal_volume=0, new_tip='never',
                         blow_out='true', blowout_location='destination well')
    p300m.drop_tip()
