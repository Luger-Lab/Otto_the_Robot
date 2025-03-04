from opentrons import protocol_api
import time
import math
import sys
import random
import subprocess

metadata = {
    'protocolName': 'PCR Mag Bead Clean Up 400>600bp',
    'author': 'Alexandria Fiorenza',
    'description': '''Full plate PCR (100uL per well) clean up by Beckman SPRI mag beads. Good for dsDNA 400>600bp''',
    'apiLevel': '2.18'
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

def setup(protocol: protocol_api.ProtocolContext):
    # equipment
    global mag_mod, deepwell, pcr_block, res, tips300, tips20, p300m, p20m
    mag_mod = protocol.load_module('magnetic module gen2', 1) 
    deepwell = mag_mod.load_labware('nest_96_wellplate_2ml_deep')
    pcr_block = protocol.load_labware('opentrons_96_aluminumblock_generic_pcr_strip_200ul', 3)
    res = protocol.load_labware('nest_12_reservoir_15ml', 6)
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 8)
    tips20 = protocol.load_labware('opentrons_96_tiprack_20ul', 9)
    p300m = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tips300])
    p20m = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=[tips20])

    # reagents 
    global beads, etoh1, elute, pcr_waste, etoh_waste, pcr_consolidate
    beads = res.wells()[0]
    etoh1 = res.wells()[1]
    elute = res.wells()[2]
    pcr_waste = res.wells()[4]
    etoh_waste = res.wells()[5]
    pcr_consolidate = res.wells()[7]

def distribute(protocol: protocol_api.ProtocolContext):
    # consolidate all pcr tubes to first column deepwell block (~1.2mL/well)
    p300m.consolidate(100, pcr_block.columns(), deepwell.columns()[0])

    # add SPRI beads (0.6X * 1.2mL = 720uL per well, ~1.9mL/well)
    p300m.transfer(720, beads, deepwell.columns()[0], mix_after=(1, 300))
    protocol.delay(seconds=10)  # Incubation for bead binding. Change to 5 mins after testing
    
    # engage magnets
    #mag_mod.engage() #need to adjust height because it keeps moving the plate.  
    #protocol.delay(seconds=10)  # Allow beads to separate. Change to 2+ after test 

    #remove majority of pcr supernatant
    p300m.pick_up_tip()
    p300m.aspirate(300, deepwell.well(0).bottom(5))
    p300m.dispense(300, pcr_waste)
    p300m.drop_tip()
    
    # disengage magnet for consolidation
    #mag_mod.disengage()
