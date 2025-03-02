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
    beads = res.wells()[0]
    etoh1 = res.wells()[1]
    elute = res.wells()[2]
    pcr_waste = res.wells()[4]
    etoh_waste = res.wells()[5]
    pcr_consolidate = res.wells()[7]

def distribute(protocol: protocol_api.ProtocolContext):
    """Pools all PCR solution into the first column of the deepwell plate and adds magnetic beads. """
    p300m.pick_up_tip()
    dest_wells = deepwell.wells()[:8]  # First column (8 wells)
    src_wells = pcr_block.wells()
    
    # Loop through each of the 12 rows in the PCR block (12 rows * 8 columns = 96 wells)
    for row in range(12):  # 12 rows in PCR block
        # For each row, transfer the PCR solution from all 8 wells in that row to the corresponding destination well in the deepwell plate
        for i in range(8):  # 8 wells in each row
            # Transfer 100uL from each source well to the corresponding destination well
            p300m.transfer(100, src_wells[row * 8 + i], dest_wells[i], new_tip='never')

    p300m.drop_tip()

    # Add SPRI beads (720uL per well)
    p300m.pick_up_tip()
    for well in dest_wells:
        p300m.transfer(720, beads, well, mix_after=(5, 300), new_tip='never')
    p300m.drop_tip()

    protocol.delay(minutes=1)  # Incubation for bead binding. Change to 5 after testing

def clean_up(protocol: protocol_api.ProtocolContext):
    """Performs washing and elution steps. Consolidates PCR sample into one single deepwell."""
    # Engage magnets
    mag_mod.engage()
    protocol.delay(minutes=1)  # Allow beads to separate. Change to 2+ after test 
    
    # Remove supernatant leaving ~100uL. May need to adjust Z to not pick up beads.
    p300m.pick_up_tip()
    for well in deepwell.wells()[:8]:  # First column wells
        p300m.transfer(1820, well, pcr_waste, new_tip='never')
    p300m.drop_tip()

    # Disengage magnet for consolidation
    mag_mod.disengage()

    # Consolidate PCR into reservoir
    p300m.pick_up_tip()
    for well in deepwell.wells()[:8]:  # First column wells
        p300m.transfer(100, well, pcr_consolidate, new_tip='never')
    p300m.drop_tip()

    # Transfer consolidated PCR to a single deepwell
    p300m.pick_up_tip()
    p300m.transfer(800, pcr_consolidate, deepwell.wells()[0], new_tip='never')
    p300m.drop_tip()
    
    # Engage magnets
    mag_mod.engage()
    protocol.delay(minutes=1)  # Allow beads to separate. Change to 2+ after test 

    # Remove 770uL of supernatant to PCR waste
    p300m.pick_up_tip()
    p300m.transfer(770, deepwell.wells()[0], pcr_waste, new_tip='never')
    p300m.drop_tip()

    # Ethanol Wash 1
    p300m.pick_up_tip()
    p300m.transfer(1400, etoh1, deepwell.wells()[0], new_tip='never')
    protocol.delay(minutes=1)
    p300m.transfer(1400, deepwell.wells()[0], etoh_waste, new_tip='never')
    p300m.drop_tip()

    # Ethanol Wash 2
    p300m.pick_up_tip()
    p300m.transfer(1400, etoh1, deepwell.wells()[0], new_tip='never')
    protocol.delay(minutes=1)
    p300m.transfer(1420, deepwell.wells()[0], etoh_waste, new_tip='never')
    p300m.drop_tip()

    # Air-dry beads
    protocol.delay(minutes=1)  # Change to 5 after test


def elution(protocol: protocol_api.ProtocolContext):
    # Disengage magnet for elution
    mag_mod.disengage()
    
    # Add elution buffer and mix
    p20m.pick_up_tip()
    p20m.transfer(35, elute, deepwell.wells()[0], mix_after=(5, 20), new_tip='never')
    p20m.drop_tip()
    
    # Incubation for elution
    protocol.delay(minutes=1)  # Allow DNA to elute. Change to 5 after test
    
    # Engage magnet to separate beads
    mag_mod.engage()
    protocol.delay(minutes=1)  # Change to 2+ after test
    
    # Transfer eluted DNA to a different deepwell.
    p20m.pick_up_tip()
    p20m.transfer(30, deepwell.wells()[0], deepwell.wells()[1], new_tip='never')
    p20m.drop_tip()
    
    # Disengage magnet after elution
    mag_mod.disengage()
