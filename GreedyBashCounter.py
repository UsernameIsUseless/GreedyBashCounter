from time import sleep
from helpers import log_parser
from appJar import gui
from pygtail import Pygtail


def start_stop(btn):
    global ACTIVE
    if btn == "Start" and not ACTIVE:
        ACTIVE = True
        app.setButtonState("Start", "disabled")
        app.setButtonState("Stop", "active")
        app.setLocation(0, 0)
        app.thread(read_log)
    elif btn == "Stop" and ACTIVE:
        ACTIVE = False
        app.setButtonState("Start", "active")
        app.setButtonState("Stop", "disabled")


def get_log():
    log = app.openBox(title="Get Puzzle Pirates Log", dirName=None, fileTypes=[('log', '*.log')],
                      asFile=False, parent=None)
    if not app.getEntry('File'):
        app.setSetting('log_path', log)
        app.saveSettings()
    app.setEntry("File", log)
    app.setButtonState("Start", "active")


def read_log():
    global LL_THIS_BATTLE
    pygtail = Pygtail(app.getEntry("File"), read_from_end=True)
    while ACTIVE:
        raw_lines = pygtail.read()
        if raw_lines:
            lines, battle_began, battle_ended = log_parser(raw_lines)
            if lines:
                for line in lines:
                    pirate = line.split(' ')[0]
                    LL_THIS_BATTLE = LL_THIS_BATTLE + 1
                    app.queueFunction(app.setLabel, 'LLThisBattle', str(LL_THIS_BATTLE))
                    app.queueFunction(individual_pirate_stat, pirate)
            if battle_ended:
                app.queueFunction(update_major_stats)
        sleep(0.5)


def update_major_stats():
    global BATTLES, LL_AVERAGE, LL_LAST_BATTLE, LL_TOTAL, LL_THIS_BATTLE, pirates
    BATTLES = BATTLES + 1
    LL_LAST_BATTLE = LL_THIS_BATTLE
    LL_TOTAL = LL_TOTAL + LL_THIS_BATTLE
    LL_AVERAGE = round(LL_TOTAL / BATTLES, 1)
    LL_THIS_BATTLE = 0
    app.setLabel('LLTotal', str(LL_TOTAL))
    app.setLabel('LLLastBattle', str(LL_LAST_BATTLE))
    app.setLabel('LLAverage', str(LL_AVERAGE))
    app.setLabel('BattleCount', str(BATTLES))
    app.setLabel('LLThisBattle', str(LL_THIS_BATTLE))

    for pirate in pirates:
        if pirate != 'row_ids':
            pirates[pirate]['ll_total'] = pirates[pirate]['ll_total'] + pirates[pirate]['ll_this_battle']
            pirates[pirate]['ll_last_battle'] = pirates[pirate]['ll_this_battle']
            pirates[pirate]['ll_this_battle'] = 0
            pirates[pirate]['ll_average'] = round(pirates[pirate]['ll_total'] / BATTLES, 1)

            row_data = [pirate, pirates[pirate]['ll_total'], pirates[pirate]['ll_average'],
                        pirates[pirate]['ll_last_battle'], pirates[pirate]['ll_this_battle']]
            app.queueFunction(app.replaceTableRow, 'PirateStats', pirates[pirate]['row_id'], row_data)


def reset_stats():
    global BATTLES, LL_AVERAGE, LL_LAST_BATTLE, LL_TOTAL, LL_THIS_BATTLE, pirates
    LL_TOTAL = 0
    LL_AVERAGE = 0
    LL_LAST_BATTLE = 0
    LL_THIS_BATTLE = 0
    BATTLES = 0
    app.setLabel('LLTotal', str(LL_TOTAL))
    app.setLabel('LLLastBattle', str(LL_LAST_BATTLE))
    app.setLabel('LLAverage', str(LL_AVERAGE))
    app.setLabel('BattleCount', str(BATTLES))
    app.setLabel('LLThisBattle', str(LL_THIS_BATTLE))
    app.deleteAllTableRows("PirateStats")
    pirates = {
        'row_ids': [-1]
    }
    print('Stats Reset')


def pirate_stat_window():
    window = app.getSetting("Per Pirate Statistics")
    if not window:
        app.showSubWindow("Per Pirate Statistics")
        app.setSetting("Per Pirate Statistics", True)

    else:
        app.hideSubWindow("Per Pirate Statistics")
        app.setSetting("Per Pirate Statistics", False)

    app.saveSettings()


def individual_pirate_stat(pirate):
    global pirates
    print('Updating Individual Pirate Stat for {}'.format(pirate))
    app.openSubWindow("Per Pirate Statistics")
    if not pirates.get(pirate):
        print('Creating Pirate Dictionary')
        pirates[pirate] = {
            'row_id': 0,
            'll_this_battle': 0,
            'll_total': 0,
            'll_average': 0,
            'll_last_battle': 0
        }
        pirates[pirate]['row_id'] = max(pirates['row_ids']) + 1
        pirates['row_ids'].append(pirates[pirate]['row_id'])
        print('New pirate {} added with row_id {}'.format(pirate, pirates[pirate]['row_id']))
        row_data = [pirate, pirates[pirate]['ll_total'], pirates[pirate]['ll_average'],
                    pirates[pirate]['ll_last_battle'], pirates[pirate]['ll_this_battle']]
        app.addTableRow('PirateStats', row_data)
        print('Generic Pirate Row Created')

    pirates[pirate]['ll_this_battle'] = pirates[pirate]['ll_this_battle'] + 1
    print('New LL count for {} is {}'.format(pirate, pirates[pirate]['ll_this_battle']))
    row_data = [pirate, pirates[pirate]['ll_total'], pirates[pirate]['ll_average'],
                pirates[pirate]['ll_last_battle'], pirates[pirate]['ll_this_battle']]
    print('Data to be added: {}'.format(row_data))

    app.queueFunction(app.replaceTableRow, 'PirateStats', pirates[pirate]['row_id'], row_data)
    app.stopSubWindow()


ACTIVE = False
LL_TOTAL = 0
LL_AVERAGE = 0
LL_LAST_BATTLE = 0
LL_THIS_BATTLE = 0
BATTLES = 0

app = gui(useSettings=True, showIcon=False)

app.loadSettings()
app.setTitle('GBC')
app.setSize(205, 242)
app.setResizable(canResize=False)
app.setFont(size=10)
app.setIcon('media/icon.gif')
app.addEntry("File", 0, 0)
app.setEntryState("File", "disabled")
app.setEntry('File', app.getSetting('log_path', default=''))
app.addButton("Set Log", get_log, 0, 1)

app.startLabelFrame("Log Monitoring", colspan=2)
app.setSticky('ew')
app.addButton("Start", start_stop, 0, 0)
app.addButton("Stop", start_stop, 0, 1)
if not app.getSetting('log_path', default=''):
    app.setButtonState("Start", "disabled")
app.addButton("Reset", reset_stats, colspan=2)
app.setButtonState("Stop", "disabled")
app.stopLabelFrame()

app.startLabelFrame("Lavish Lockers", colspan=2)
app.setSticky('ew')
app.addLabel("LLTotalTitle", 'Total:', 0, 0)
app.addLabel("LLTotal", '0', 0, 1)
app.addLabel("LLLastBattleTitle", 'Last Battle:', 0, 2)
app.addLabel("LLLastBattle", '0', 0, 3)
app.addLabel("LLAverageTitle", 'Average:', 1, 0)
app.addLabel("LLAverage", '0', 1, 1)
app.addLabel("BattleCountTitle", 'Battles:', 1, 2)
app.addLabel("BattleCount", '0', 1, 3)
app.addLabel("LLThisBattleTitle", 'This Battle:', 2, 0)
app.addLabel("LLThisBattle", '0', 2, 1)
app.addButton('Per Pirate Stats', pirate_stat_window, colspan=4)
app.stopLabelFrame()


initial_table = [["Pirate", "LL Total", "LL Avg", "TLB", "TTB"]]
pirates = {
    'row_ids': [-1]
}

app.startSubWindow("Per Pirate Statistics", transient=True)
app.setResizable(canResize=False)
app.addTable('PirateStats', initial_table)
app.stopSubWindow()

app.go()
