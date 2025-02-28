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
    # Equipment setup
    global mag_mod, deepwell, pcr_block, res, tips300, tips20, p300m, p20m
    mag_mod = protocol.load_module('magnetic module gen2', 1) 
    deepwell = mag_mod.load_labware('nest_96_wellplate_2ml_deep')
    pcr_block = protocol.load_labware('opentrons_96_aluminumblock_generic_pcr_strip_200ul', 3)
    res = protocol.load_labware('nest_12_reservoir_15ml', 6)
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 8)
    tips20 = protocol.load_labware('opentrons_96_tiprack_20ul', 9)
    p300m = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tips300])
    p20m = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=[tips20])

    # Liquids setup
    global beads, etoh1, elute, pcr_waste, etoh_waste, pcr_consolidate
    beads = res.wells()[1]
    etoh1 = res.wells()[2]
    elute = res.wells()[3]
    pcr_waste = res.wells()[5]
    etoh_waste = res.wells()[6]
    pcr_consolidate = res.wells()[8]

def distribute(protocol: protocol_api.ProtocolContext):
    """Pools all PCR solution into the first well (A1) of the deepwell plate and adds magnetic beads."""
    
    dest_well = deepwell.wells()[0]  # Target A1 in the deepwell plate

    p300m.pick_up_tip()  # Pick up a single tip before starting

    for col in pcr_block.columns():  # Loop through all 8 columns
        p300m.transfer(100, col, dest_well, new_tip='never')  # Transfer 100 µL from each row to A1

    p300m.drop_tip()  # Drop the tip after finishing all rows

    





