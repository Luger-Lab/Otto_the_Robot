from opentrons import protocol_api
import time
import sys
import math


metadata = {
    'protocolName': 'Crosslinker titration',
    'author': 'Shawn Laursen',
    'description': '''This protocol will do a crosslinking reaction at 3 concentrations of BS3.
                      Liquids:
                      - Put 50µL of sample into pcr tray (every third column)
                      - Fill up 1ml tube of buff in first position
                      - Fill up >(10µL * num samples) 1ml tube of 2x BS3 in second position
                      - Fill up >(10µL * num samples) tube of 2000x BS3 in third position
                      - Fill up >(40µL * num samples) tube of SDS buff in fourth position
                      ''',
    'apiLevel': '2.18'
    }

def add_parameters(parameters: protocol_api.Parameters):
    parameters.add_int(
        variable_name="num_samples",
        display_name="Number of samples",
        description="Number of samples.",
        default=8,
        minimum=1,
        maximum=32,
        unit="samples"
    )
    parameters.add_int(
        variable_name="temp_96start",
        display_name="Temp 96 well start",
        description="Which column to start in. Indexed from 1.",
        default=1,
        minimum=1,
        maximum=12,
        unit="column"
    )
    parameters.add_int(
        variable_name="incubation_temp",
        display_name="Incubation temp",
        description="Incubation temp of reaction.",
        default=20,
        minimum=4,
        maximum=95,
        unit="C"
    )
    parameters.add_int(
        variable_name="incubation_time",
        display_name="Incubation time",
        description="Incubation duration.",
        default=20,
        minimum=0,
        maximum=1000,
        unit="min"
    )
    parameters.add_int(
        variable_name="quench_temp",
        display_name="Quenching temp",
        description="Queching temp of proteinase K.",
        default=37,
        minimum=4,
        maximum=95,
        unit="C"
    )
    parameters.add_int(
        variable_name="quench_time",
        display_name="Quenching time",
        description="Queching duration of proteinase K.",
        default=30,
        minimum=0,
        maximum=1000,
        unit="min"
    )
    parameters.add_int(
        variable_name="denature_temp",
        display_name="Denaturing temp",
        description="Temp to denature after quenching.",
        default=95,
        minimum=4,
        maximum=95,
        unit="C"
    )
    parameters.add_int(
        variable_name="denature_time",
        display_name="Denaturing time",
        description="Amount of time to denature after quench.",
        default=5,
        minimum=0,
        maximum=1000,
        unit="min"
    )

def run(protocol):
    global num_samples, well_96start, temp_96start
    num_samples = protocol.params.num_samples
    temp_96start = protocol.params.temp_96start - 1
    incubation_temp = protocol.params.incubation_temp
    incubation_time = protocol.params.incubation_time
    quench_temp = protocol.params.quench_temp
    quench_time = protocol.params.quench_time
    denature_temp = protocol.params.quench_time
    denature_time = protocol.params.quench_time

    strobe(12, 8, True, protocol)
    setup(protocol)
    
    distribute_samples(protocol)
    add_crosslinker(protocol)
    incubate(incubation_temp, incubation_time, protocol)
    quench(quench_temp, quench_time, protocol)
    add_sample_buff(protocol)
    denature(denature_temp, denature_time, protocol)
    
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
    # equiptment
    global tips300, tips20, trough, p300m, p20m, tempdeck, temp_pcr, rt_24, glycine
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 6)
    tips20 = protocol.load_labware('opentrons_96_tiprack_20ul', 5)
    trough = protocol.load_labware('nest_12_reservoir_15ml', 4)
    p300m = protocol.load_instrument('p300_multi_gen2', 'left',
                                     tip_racks=[tips300])
    p20m = protocol.load_instrument('p20_multi_gen2', 'right',
                                     tip_racks=[tips20])
    tempdeck = protocol.load_module('temperature module gen2', 10)
    temp_pcr = tempdeck.load_labware(
                 'opentrons_96_aluminumblock_generic_pcr_strip_200ul')
    rt_24 = protocol.load_labware('opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', 7)
    glycine = trough.wells()[0]

    # liquids
    yellowSamples = protocol.define_liquid(
        name="Samples",
        description="Samples",
        display_color="#FFFF00",
    )
    for i in range(0, (32 // 8)):
        col = (i*3) 
        for j in range(0, 8):
            temp_pcr.rows()[j][col].load_liquid(liquid=yellowSamples, volume=50)

    greenGlycine = protocol.define_liquid(
        name="Glycine",
        description="Glycine",
        display_color="#00FF00",
    )
    glycine.load_liquid(liquid=greenGlycine, volume=2000)

    grayBuff = protocol.define_liquid(
        name="Buff",
        description="Buff used for no BS3 control",
        display_color="#AAAAAA",
    )
    rt_24.rows()[0][0].load_liquid(liquid=grayBuff, volume=1600)

    redXL = protocol.define_liquid(
        name="2x BS3",
        description="2x BS3 that will be 1x final when added",
        display_color="#AA0000",
    )
    rt_24.rows()[0][1].load_liquid(liquid=redXL, volume=1600)

    redishXL = protocol.define_liquid(
        name="2000x BS3",
        description="2000x BS3 that will be 1000x final when added",
        display_color="#FF0000",
    )
    rt_24.rows()[0][2].load_liquid(liquid=redishXL, volume=1600)

    blueSDS = protocol.define_liquid(
        name="SDS buff",
        description="SDS buff",
        display_color="#0000FF",
    )
    rt_24.rows()[0][3].load_liquid(liquid=blueSDS, volume=1600)

    #single tips
    global which_tips20, tip20
    which_tips20 = []
    tip20 = 0
    tip_row_list = ['H','G','F','E','D','C','B','A']
    for i in range(0,96):
        which_tips20.append(tip_row_list[(i%8)]+str(math.floor(i/8)+1))

    #single tips
    global which_tips300, tip300
    which_tips300 = []
    tip300 = 0
    tip_row_list = ['H','G','F','E','D','C','B','A']
    for i in range(0,96):
        which_tips300.append(tip_row_list[(i%8)]+str(math.floor(i/8)+1))

def pickup_tips(number, pipette, protocol):
    global tip300, tip20
    if pipette == p20m:
        if (tip20 % number) != 0:
            while (tip20 % 8) != 0:
                tip20 += 1
        tip20 += number-1
        p20m.pick_up_tip(tips20[which_tips20[tip20]])
        tip20 += 1 
    if pipette == p300m:
        if (tip300 % number) != 0:
            while (tip300 % 8) != 0:
                tip300 += 1
        tip300 += number-1
        p300m.pick_up_tip(tips300[which_tips300[tip300]])
        tip300 += 1

def distribute_samples(protocol):
    # full 8 cols
    for i in range(0, (num_samples // 8)):
        col = (i*3) + temp_96start
        pickup_tips(8, p20m, protocol)
        p20m.distribute(10, temp_pcr.rows()[0][col], 
                      temp_pcr.rows()[0][col+1:col+3],
                      disposal_volume=0, new_tip='never')
        p20m.drop_tip()

    # remainder rows in last col
    remainder = num_samples % 8
    if remainder != 0:
        try:
            col += 3
        except:
            col = 0
        pickup_tips(remainder, p20m, protocol)
        p20m.distribute(10, temp_pcr.rows()[0][col], 
                        temp_pcr.rows()[0][col+1:col+3],
                        disposal_volume=0, new_tip='never')
        p20m.drop_tip()

def add_crosslinker(protocol):
    # add 0, 1, 1000x crosslinker
    for i in range(0, num_samples):
        col = ((num_samples // 8)*3) + temp_96start 
        row = num_samples % 8
        pickup_tips(1, p20m, protocol)
        p20m.aspirate(10,rt_24.rows()[0][0])
        p20m.dispense(10,temp_pcr.rows()[col][row])
        p20m.mix(3,10)
        p20m.drop_tip()
        pickup_tips(1, p20m, protocol)
        p20m.aspirate(10,rt_24.rows()[0][1])
        p20m.dispense(10,temp_pcr.rows()[col+1][row])
        p20m.mix(3,10)
        p20m.drop_tip()
        pickup_tips(1, p20m, protocol)
        p20m.aspirate(10,rt_24.rows()[0][2])
        p20m.dispense(10,temp_pcr.rows()[col+2][row])
        p20m.mix(3,10)
        p20m.drop_tip()

def incubate(incubation_temp, incubation_time, protocol):
    tempdeck.set_temperature(celsius=incubation_temp)
    protocol.delay(minutes=incubation_time)

def quench(quench_temp, quench_time, protocol):
    # do it slowly to get equal time on heat block
    for i in range(0, num_samples):
        col = ((num_samples // 8)*3) + temp_96start 
        row = num_samples % 8
        pickup_tips(1, p20m, protocol)
        p20m.aspirate(10,glycine)
        p20m.dispense(10,temp_pcr.rows()[col][row])
        p20m.mix(3,20)
        p20m.drop_tip()
        pickup_tips(1, p20m, protocol)
        p20m.aspirate(10,glycine)
        p20m.dispense(10,temp_pcr.rows()[col+1][row])
        p20m.mix(3,20)
        p20m.drop_tip()
        pickup_tips(1, p20m, protocol)
        p20m.aspirate(10,glycine)
        p20m.dispense(10,temp_pcr.rows()[col+2][row])
        p20m.mix(3,20)
        p20m.drop_tip()

def add_sample_buff(protocol):   
    for i in range(0, num_samples):
        col = ((num_samples // 8)*3) + temp_96start 
        row = num_samples % 8
        pickup_tips(1, p300m, protocol)
        p300m.aspirate(40,rt_24.rows()[0][3])
        p300m.dispense(40,temp_pcr.rows()[col][row])
        p300m.mix(3,40)
        p300m.drop_tip()
        pickup_tips(1, p300m, protocol)
        p300m.aspirate(40,rt_24.rows()[0][3])
        p300m.dispense(40,temp_pcr.rows()[col+1][row])
        p300m.mix(3,40)
        p300m.drop_tip()
        pickup_tips(1, p300m, protocol)
        p300m.aspirate(40,rt_24.rows()[0][3])
        p300m.dispense(40,temp_pcr.rows()[col+2][row])
        p300m.mix(3,40)
        p300m.drop_tip()

def denature(denature_temp, denature_time, protocol):
    tempdeck.set_temperature(celsius=denature_temp)
    protocol.delay(minutes=denature_time)
    tempdeck.deactivate()
