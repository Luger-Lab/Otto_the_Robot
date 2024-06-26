from opentrons import protocol_api
import time
import sys
import math


metadata = {
    'protocolName': 'Fast Salt screen 4x7x12 1:1 Serial Dilutions',
    'author': 'Shawn Laursen',
    'description': '''This protocol will dilute buffer and protein stocks in 96
                      well, making 4(pH)x7(salt) conditions. You will need 16
                      inputs: protien+DNA+salt, salt+DNA, protein+DNA, DNA (for
                      each pH). The program will dilute each column of the 96
                      well and combine the exta DNA columns with the even
                      columns to make 250ul for each dilution. It will then make
                      32x12well dilutions in a 384 well plate using the odd
                      columns for high protein. The dilutions are 1:1 across the
                      the plate and leave the last well of each dilution with
                      buffer (DNA) only. Control at bottom of each column.''',
    'apiLevel': '2.8'
    }

def run(protocol):
    #setup
    setup(protocol)

    #turn on robot rail lights
    strobe(5, 8, protocol)

    #make buffs
    make_mixes(True, protocol)

    #transfer buffs to 96well
    fill_96well(protocol)

    #titrate salt
    titrate_salt(protocol)

    #do titration
    for i in range(0,len(buffs)):
        titrate(titrations[i])

    #turn off robot rail lights
    strobe(5, 8, protocol)
    protocol.set_rail_lights(False)

def setup(protocol):
    global trough, tips300, tips300_2, plate96, plate384, p300m, tempdeck
    trough = protocol.load_labware('nest_12_reservoir_15ml', '2')
    tips300 = protocol.load_labware('opentrons_96_tiprack_300ul', 4)
    tips300_2 = protocol.load_labware('opentrons_96_tiprack_300ul', 8)
    plate96 = protocol.load_labware('costar_96_wellplate_200ul', 6)
    plate384 = protocol.load_labware('corning3575_384well_alt', 5)
    p300m = protocol.load_instrument('p300_multi_gen2', 'left',
                                     tip_racks=[tips300, tips300_2])
    tempdeck = protocol.load_module('temperature module gen2', 10)

    global temp_buffs, buffa, buffb, buffc, buffd, high_salt, low_salt, edta
    global water, buffs, protein, dna, dna_extra
    temp_buffs = tempdeck.load_labware(
                 'opentrons_24_aluminumblock_nest_1.5ml_snapcap')
    buffa = trough.wells()[0]
    buffb = trough.wells()[1]
    buffc = trough.wells()[2]
    buffd = trough.wells()[3]
    buffs = [buffa, buffb, buffc, buffd]
    high_salt = trough.wells()[4]
    low_salt = trough.wells()[5]
    edta = trough.wells()[6]
    water = trough.wells()[7]
    protein = temp_buffs.wells_by_name()['A1']
    dna = temp_buffs.wells_by_name()['A2']
    dna_extra = temp_buffs.wells_by_name()['D2']

    global hi_prot_dna_vol, lo_prot_dna_vol, hi_dna_vol, lo_dna_vol
    hi_prot_dna_vol = 150
    lo_prot_dna_vol = 350
    hi_dna_vol = 550
    lo_dna_vol = 1500

    global hpdv1, lpdv1, hdv1, ldv1
    hpdv1 = (hi_prot_dna_vol)/5
    lpdv1 = (lo_prot_dna_vol)/5
    hdv1 = (hi_dna_vol)/5
    ldv1 = (lo_dna_vol)/5

    global which_tips, tip
    which_tips = []
    tip = 0
    tip_row_list = ['H','G','F','E','D','C','B','A']
    for i in range(0,96):
        which_tips.append(tip_row_list[(i%8)]+str(math.floor(i/8)+1))

    global titrations
    titrations = [[1, 0, 0, 'odd', protocol], [3, 2, 0, 'even', protocol],
                  [5, 4, 12, 'odd', protocol], [7, 6, 12, 'even', protocol]]

def strobe(blinks, hz, protocol):
    i = 0
    while i < blinks:
        protocol.set_rail_lights(True)
        time.sleep(1/hz)
        protocol.set_rail_lights(False)
        time.sleep(1/hz)
        i += 1
    protocol.set_rail_lights(True)

def titrate(titration):
    buff_96col = titration[0]
    protien_96col = titration[1]
    start_384well = titration[2]
    which_rows = titration[3]
    protocol = titration [4]
    p300m.flow_rate.aspirate = 25

    if which_rows == 'odd':
        which_rows = 0
    elif which_rows == 'even':
        which_rows = 1
    else:
        sys.exit('Wrong value for which_rows.')

    p300m.pick_up_tip()

    if buff_96col == 1:
        p300m.transfer(125, plate96.rows()[0][8].bottom(1.75),
                       plate96.rows()[0][1],
                       new_tip='never')
    elif buff_96col == 3:
        p300m.transfer(125, plate96.rows()[0][9].bottom(1.75),
                       plate96.rows()[0][3],
                       new_tip='never')
    elif buff_96col == 5:
        p300m.transfer(125, plate96.rows()[0][10].bottom(1.75),
                       plate96.rows()[0][5],
                       new_tip='never')
    elif buff_96col == 7:
        p300m.transfer(125, plate96.rows()[0][11].bottom(1.75),
                       plate96.rows()[0][7],
                       new_tip='never')

    p300m.distribute(20, plate96.rows()[0][buff_96col].bottom(1.75),
                     plate384.rows()[which_rows][start_384well+1:start_384well+12],
                     disposal_volume=0, new_tip='never')
    p300m.blow_out()
    p300m.transfer(40, plate96.rows()[0][protien_96col].bottom(1.75),
                   plate384.rows()[which_rows][start_384well], new_tip='never')
    p300m.blow_out()
    p300m.transfer(20,
                   plate384.rows()[which_rows][start_384well:start_384well+10],
                   plate384.rows()[which_rows][start_384well+1:start_384well+11],
                   mix_after=(3, 20), new_tip='never')
    p300m.blow_out()
    p300m.aspirate(20, plate384.rows()[which_rows][start_384well+10])
    p300m.drop_tip()

def titrate_salt(protocol):
    global tip
    for column in range(0,12):
        if column in (0,2,4,6):
            p300m.pick_up_tip(tips300[which_tips[tip]])
            tip += 1
            for row in range(1,6):
                p300m.aspirate(50, plate96.rows()[row][column].bottom(1.75))
                p300m.dispense(50, plate96.rows()[row+1][column].bottom(1.75))
                p300m.mix(3,50)
            p300m.aspirate(50, plate96.rows()[6][column].bottom(1.75))
            p300m.drop_tip()
        elif column in (1,3,5,7):
            p300m.pick_up_tip(tips300[which_tips[tip]])
            tip += 1
            for row in range(1,6):
                p300m.aspirate(115, plate96.rows()[row][column].bottom(1.75))
                p300m.dispense(115, plate96.rows()[row+1][column].bottom(1.75))
                p300m.mix(3,115)
            p300m.aspirate(115, plate96.rows()[6][column].bottom(1.75))
            p300m.drop_tip()
        else:
            p300m.pick_up_tip(tips300[which_tips[tip]])
            tip += 1
            for row in range(1,6):
                p300m.aspirate(135, plate96.rows()[row][column].bottom(1.75))
                p300m.dispense(135, plate96.rows()[row+1][column].bottom(1.75))
                p300m.mix(3,135)
            p300m.aspirate(135, plate96.rows()[6][column].bottom(1.75))
            p300m.drop_tip()

def make_mixes(make_high, protocol):
    global tip
    #make high protein + DNA
    if make_high:
        #add edta
        p300m.pick_up_tip(tips300[which_tips[tip]])
        tip += 1
        for buff in range(0,len(buffs)):
                p300m.aspirate((hpdv1+lpdv1+hdv1), edta)
                p300m.dispense(hpdv1, temp_buffs.rows()[0][buff+2].top())
                p300m.touch_tip()
                p300m.dispense(lpdv1, temp_buffs.rows()[1][buff+2].top())
                p300m.touch_tip()
                p300m.dispense(hdv1, temp_buffs.rows()[2][buff+2].top())
                p300m.touch_tip()
                p300m.blow_out(edta)
                p300m.aspirate((ldv1), edta)
                p300m.dispense(ldv1, temp_buffs.rows()[3][buff+2].top())
                p300m.touch_tip()
                p300m.blow_out(edta)
        p300m.drop_tip()

        #add high_salt
        p300m.pick_up_tip(tips300[which_tips[tip]])
        tip += 1
        for buff in range(0,len(buffs)):
                p300m.aspirate((hpdv1+hdv1), high_salt)
                p300m.dispense(hpdv1, temp_buffs.rows()[0][buff+2].top())
                p300m.touch_tip()
                p300m.dispense(hdv1, temp_buffs.rows()[2][buff+2].top())
                p300m.touch_tip()
                p300m.blow_out(high_salt)
        p300m.drop_tip()

        #add low_salt
        p300m.pick_up_tip(tips300[which_tips[tip]])
        tip += 1
        for buff in range(0,len(buffs)):
                p300m.aspirate((lpdv1), low_salt)
                p300m.dispense(lpdv1, temp_buffs.rows()[1][buff+2].top())
                p300m.touch_tip()
                p300m.blow_out(low_salt)
                p300m.aspirate((ldv1), low_salt)
                p300m.dispense(ldv1, temp_buffs.rows()[3][buff+2].top())
                p300m.touch_tip()
                p300m.blow_out(low_salt)
        p300m.drop_tip()

        #add water
        p300m.pick_up_tip(tips300[which_tips[tip]])
        tip += 1
        for buff in range(0,len(buffs)):
                p300m.aspirate((hdv1), water)
                p300m.dispense(hdv1, temp_buffs.rows()[2][buff+2].top())
                p300m.touch_tip()
                p300m.blow_out(water)
                p300m.aspirate((ldv1), water)
                p300m.dispense(ldv1, temp_buffs.rows()[3][buff+2].top())
                p300m.touch_tip()
                p300m.blow_out(water)
        p300m.drop_tip()

        #add protein
        p300m.pick_up_tip(tips300[which_tips[tip]])
        tip += 1
        for buff in range(0,len(buffs)):
                p300m.aspirate((hpdv1+lpdv1), protein.bottom(-2))
                p300m.dispense(hpdv1, temp_buffs.rows()[0][buff+2].top())
                p300m.touch_tip()
                p300m.dispense(lpdv1, temp_buffs.rows()[1][buff+2].top())
                p300m.touch_tip()
                p300m.blow_out(protein)
        p300m.drop_tip()

        #add DNA
        p300m.pick_up_tip(tips300[which_tips[tip]])
        tip += 1
        for buff in range(0,len(buffs)):
                p300m.aspirate((hpdv1+lpdv1+hdv1), dna.bottom(-2))
                p300m.dispense(hpdv1, temp_buffs.rows()[0][buff+2].top())
                p300m.touch_tip()
                p300m.dispense(lpdv1, temp_buffs.rows()[1][buff+2].top())
                p300m.touch_tip()
                p300m.dispense(hdv1, temp_buffs.rows()[2][buff+2].top())
                p300m.touch_tip()
                p300m.blow_out(dna)
                p300m.aspirate((ldv1), dna_extra.bottom(-2))
                p300m.dispense(ldv1, temp_buffs.rows()[3][buff+2].top())
                p300m.touch_tip()
                p300m.blow_out(dna_extra)
        p300m.drop_tip()

        #add buff
        for buff in range(0,len(buffs)):
                p300m.pick_up_tip(tips300[which_tips[tip]])
                tip += 1
                p300m.aspirate((hpdv1+lpdv1+hdv1), buffs[buff])
                p300m.dispense(hpdv1, temp_buffs.rows()[0][buff+2].top())
                p300m.touch_tip()
                p300m.dispense(lpdv1, temp_buffs.rows()[1][buff+2].top())
                p300m.touch_tip()
                p300m.dispense(hdv1, temp_buffs.rows()[2][buff+2].top())
                p300m.touch_tip()
                p300m.blow_out(buffs[buff])
                p300m.aspirate((ldv1), buffs[buff])
                p300m.dispense(ldv1, temp_buffs.rows()[3][buff+2].top())
                p300m.touch_tip()
                p300m.blow_out(buffs[buff])
                p300m.drop_tip()
    else:
        #add edta
        p300m.pick_up_tip(tips300[which_tips[tip]])
        tip += 1
        for buff in range(0,len(buffs)):
                p300m.aspirate((lpdv1), edta)
                p300m.dispense(lpdv1, temp_buffs.rows()[1][buff+2].top())
                p300m.touch_tip()
                p300m.blow_out(edta)
                p300m.aspirate((ldv1), edta)
                p300m.dispense(ldv1, temp_buffs.rows()[3][buff+2].top())
                p300m.touch_tip()
                p300m.blow_out(edta)
        p300m.drop_tip()

        #add low_salt
        p300m.pick_up_tip(tips300[which_tips[tip]])
        tip += 1
        for buff in range(0,len(buffs)):
                p300m.aspirate((lpdv1), low_salt)
                p300m.dispense(lpdv1, temp_buffs.rows()[1][buff+2].top())
                p300m.touch_tip()
                p300m.blow_out(low_salt)
                p300m.aspirate((ldv1), low_salt)
                p300m.dispense(ldv1, temp_buffs.rows()[3][buff+2].top())
                p300m.touch_tip()
                p300m.blow_out(low_salt)
        p300m.drop_tip()

        #add water
        p300m.pick_up_tip(tips300[which_tips[tip]])
        tip += 1
        for buff in range(0,len(buffs)):
                p300m.aspirate((ldv1), water)
                p300m.dispense(ldv1, temp_buffs.rows()[3][buff+2].top())
                p300m.touch_tip()
                p300m.blow_out(water)
        p300m.drop_tip()

        #add protein
        p300m.pick_up_tip(tips300[which_tips[tip]])
        tip += 1
        for buff in range(0,len(buffs)):
                p300m.aspirate((lpdv1), protein.bottom(-2))
                p300m.dispense(lpdv1, temp_buffs.rows()[1][buff+2].top())
                p300m.touch_tip()
                p300m.blow_out(protein)
        p300m.drop_tip()

        #add DNA
        p300m.pick_up_tip(tips300[which_tips[tip]])
        tip += 1
        for buff in range(0,len(buffs)):
                p300m.aspirate((lpdv1), dna.bottom(-2))
                p300m.dispense(lpdv1, temp_buffs.rows()[1][buff+2].top())
                p300m.touch_tip()
                p300m.blow_out(dna)
                p300m.aspirate((ldv1), dna_extra.bottom(-2))
                p300m.dispense(ldv1, temp_buffs.rows()[3][buff+2].top())
                p300m.touch_tip()
                p300m.blow_out(dna_extra)
        p300m.drop_tip()

        #add buff
        for buff in range(0,len(buffs)):
                p300m.pick_up_tip(tips300[which_tips[tip]])
                tip += 1
                p300m.aspirate((lpdv1), buffs[buff])
                p300m.dispense(lpdv1, temp_buffs.rows()[1][buff+2].top())
                p300m.touch_tip()
                p300m.blow_out(buffs[buff])
                p300m.aspirate((ldv1), buffs[buff])
                p300m.dispense(ldv1, temp_buffs.rows()[3][buff+2].top())
                p300m.touch_tip()
                p300m.blow_out(buffs[buff])

def fill_96well(protocol):
    global tip
    #move protein wells
    column = 0
    for buff in range(0,len(buffs)):
        p300m.pick_up_tip(tips300[which_tips[tip]])
        tip += 1
        p300m.mix(3,50, temp_buffs.rows()[0][buff+2])
        p300m.aspirate(100, temp_buffs.rows()[0][buff+2].bottom(-2))
        p300m.dispense(100, plate96.rows()[1][column].bottom(1.75))
        p300m.blow_out(plate96.rows()[1][column])
        p300m.drop_tip()

        p300m.pick_up_tip(tips300[which_tips[tip]])
        tip += 1
        p300m.mix(3,100, temp_buffs.rows()[1][buff+2])
        p300m.aspirate(300, temp_buffs.rows()[1][buff+2].bottom(-2))
        for row in range(2,8):
            p300m.dispense(50, plate96.rows()[row][column].bottom(1.75))
        p300m.blow_out(plate96.rows()[2][column])
        p300m.drop_tip()
        column += 2

    #move buff wells
    column = 1
    extra = 8
    for buff in range(0,len(buffs)):
        p300m.pick_up_tip(tips300[which_tips[tip]])
        tip += 1
        p300m.mix(3,250, temp_buffs.rows()[2][buff+2])
        p300m.aspirate(270, temp_buffs.rows()[2][buff+2].bottom(-2))
        p300m.dispense(270, plate96.rows()[1][extra].bottom(1.75))
        p300m.blow_out(plate96.rows()[1][extra].bottom(1.75))
        p300m.aspirate(230, temp_buffs.rows()[2][buff+2].bottom(-2))
        p300m.dispense(230, plate96.rows()[1][column].bottom(1.75))
        p300m.blow_out(plate96.rows()[1][column])
        p300m.drop_tip()

        p300m.pick_up_tip(tips300[which_tips[tip]])
        tip += 1
        p300m.mix(3,250, temp_buffs.rows()[3][buff+2])
        for row in range(2,8):
            p300m.aspirate(250, temp_buffs.rows()[3][buff+2].bottom(-2))
            p300m.dispense(135, plate96.rows()[row][extra].bottom(1.75))
            p300m.dispense(115, plate96.rows()[row][column].bottom(1.75))
            p300m.blow_out(plate96.rows()[row][extra])
        p300m.drop_tip()
        column += 2
        extra += 1

    #move controls
    p300m.pick_up_tip(tips300[which_tips[tip]])
    tip += 1
    p300m.mix(3,50, temp_buffs.rows()[1][0])
    p300m.aspirate(100, temp_buffs.rows()[1][0].bottom(-2))
    p300m.dispense(50, plate96.rows()[0][0].bottom(1.75))
    p300m.dispense(50, plate96.rows()[0][2].bottom(1.75))
    p300m.blow_out(temp_buffs.rows()[1][0])
    p300m.drop_tip()

    p300m.pick_up_tip(tips300[which_tips[tip]])
    tip += 1
    p300m.mix(3,50, temp_buffs.rows()[2][0])
    p300m.aspirate(100, temp_buffs.rows()[2][0].bottom(-2))
    p300m.dispense(50, plate96.rows()[0][4].bottom(1.75))
    p300m.dispense(50, plate96.rows()[0][6].bottom(1.75))
    p300m.blow_out(temp_buffs.rows()[2][0])
    p300m.drop_tip()

    p300m.pick_up_tip(tips300[which_tips[tip]])
    tip += 1
    p300m.mix(3,250, temp_buffs.rows()[1][1])
    p300m.aspirate(230, temp_buffs.rows()[1][1].bottom(-2))
    p300m.dispense(115, plate96.rows()[0][1].bottom(1.75))
    p300m.dispense(115, plate96.rows()[0][3].bottom(1.75))
    p300m.blow_out(temp_buffs.rows()[1][1])
    p300m.aspirate(270, temp_buffs.rows()[1][1].bottom(-2))
    p300m.dispense(135, plate96.rows()[0][8].bottom(1.75))
    p300m.dispense(135, plate96.rows()[0][9].bottom(1.75))
    p300m.blow_out(temp_buffs.rows()[1][1])
    p300m.drop_tip()

    p300m.pick_up_tip(tips300[which_tips[tip]])
    tip += 1
    p300m.mix(3,250, temp_buffs.rows()[2][1])
    p300m.aspirate(230, temp_buffs.rows()[2][1].bottom(-2))
    p300m.dispense(115, plate96.rows()[0][5].bottom(1.75))
    p300m.dispense(115, plate96.rows()[0][7].bottom(1.75))
    p300m.blow_out(temp_buffs.rows()[2][1])
    p300m.aspirate(270, temp_buffs.rows()[2][1].bottom(-2))
    p300m.dispense(135, plate96.rows()[0][10].bottom(1.75))
    p300m.dispense(135, plate96.rows()[0][11].bottom(1.75))
    p300m.blow_out(temp_buffs.rows()[2][1])
    p300m.drop_tip()
