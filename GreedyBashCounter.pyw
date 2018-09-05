import os
from re import sub
from time import sleep
from appJar import gui
from pygtail import Pygtail
from pywinauto import clipboard
from pywinauto.keyboard import SendKeys
from pywinauto.application import Application

greedy_strings = [
    'executes a masterful strike',
    'swings a devious blow',
    'performs a powerful attack',
    'delivers an overwhelming barrage'
]
battle_ended_string = 'as your initial cut of the booty!'
battle_began_string = 'intercepted'
fight_began_string = 'A melee breaks out between the crews!'

table_headers = [["Pirate", "LL Total", "LL Avg", "TLB", "TTB"]]

version = '2.0.1'


class GreedyBashCounter(object):
    active = False
    total_lls, average_lls, last_battle_lls, this_battle_lls, battle_count = 0, 0, 0, 0, 0
    battle_started, battle_ended, fight_started = False, False, False
    pirates = {
        'row_ids': [-1]
    }

    def __init__(self):
        self.app = gui(useSettings=True, showIcon=False)
        self.app.loadSettings()
        self.app.setTitle('GBC')
        self.app.setSize(205, 242)
        self.app.setResizable(canResize=True)
        self.app.setFont(size=10)
        self.app.setIcon('media\icon.gif')

        self.app.addMenuList('Menu', ['Log Folder', 'About', 'Clear TB Counters'],
                             [self.log_folder, self.menu, self.clear_this_battle_lls])
        self.app.createMenu('Pirates')
        self.log_folder = self.app.getSetting('log_folder')
        if self.log_folder:
            pirates = [ pirate.split('_')[0] for pirate in self.get_log_list() ]

            for pirate in sorted(pirates):
                self.app.addMenuItem('Pirates', pirate, self.set_pirate)
            pnd = pirates[0]
        else:
            self.app.addMenuItem('Pirates', 'None')
            pnd = 'Pirate not set'
        self.app.startLabelFrame("PirateNameFrame", hideTitle=True, colspan=2)
        self.app.setSticky('ew')
        self.app.addLabel('PirateNameDisplay', pnd)
        self.app.stopLabelFrame()

        self.app.startLabelFrame("Log Monitoring", colspan=2)
        self.app.setSticky('ew')
        self.app.addButton("Start", self.start_stop, 0, 0)
        self.app.addButton("Stop", self.start_stop, 0, 1)
        self.app.addButton("Reset", self.reset_stats, 1, 0)
        self.app.addButton('Override', self.show_override_window, 1, 1)
        self.app.setButtonState("Stop", "disabled")
        self.app.stopLabelFrame()

        self.app.startLabelFrame("Lavish Lockers", colspan=2)
        self.app.setSticky('ew')
        self.app.addLabel("LLTotalTitle", 'Total:', 0, 0)
        self.app.addLabel("LLTotal", '0', 0, 1)
        self.app.addLabel("LLAverageTitle", 'Average:', 0, 2)
        self.app.addLabel("LLAverage", '0', 0, 3)
        self.app.addLabel("LLLastBattleTitle", 'Last Battle:', 1, 0)
        self.app.addLabel("LLLastBattle", '0', 1, 1)
        self.app.addLabel("LLThisBattleTitle", 'This Battle:', 1, 2)
        self.app.addLabel("LLThisBattle", '0', 1, 3)
        self.app.addLabel("BattleCountTitle", 'Battles:', 2, 0)
        self.app.addLabel("BattleCount", '0', 2, 1)
        self.app.stopLabelFrame()

        self.app.startLabelFrame('Buttons', hideTitle=True, colspan=2)
        self.app.setSticky('ew')
        self.app.addButton('Send Totals', self.send_totals, 0, 0)
        self.app.addButton('Per Pirate Stats', self.pirate_stat_window, 0, 1)
        self.app.stopLabelFrame()

        self.app.startSubWindow("Per Pirate Statistics", transient=True)
        self.app.setResizable(canResize=True)
        self.app.addTable('PirateStats', table_headers, action=self.send_pirate_stats, actionHeading='PP',
                          actionButton='Send')
        self.app.stopSubWindow()

        self.app.startSubWindow("Log Folder", modal=True)
        self.app.setSticky('ew')
        self.app.addFileEntry('log_folder_entry')
        if self.app.getSetting('log_folder'):
            self.log_folder = self.app.getSetting('log_folder')
            self.app.setEntry('log_folder_entry', self.log_folder)
        else:
            self.log_folder = None
        self.app.addButton('Save', self.save_log_folder)
        self.app.addButton('Close', self.close_log_window)
        self.app.stopSubWindow()

        self.app.startSubWindow('About GBC', modal=True)
        self.app.addLabel('a1', "GreedyBashCalculator")
        self.app.addHorizontalSeparator()
        self.app.addLabel('a2', "Created by:")
        self.app.addLabel('a3', "Cajun of Obsidian")
        self.app.addLabel('a4', "Version:")
        self.app.addLabel('a5', version)
        self.app.stopSubWindow()

        self.app.startSubWindow('Override', modal=True)
        self.app.hideTitleBar()
        self.app.startLabelFrame('OverrideWindowLabel', hideTitle=True, colspan=2)
        self.app.setSticky('ew')
        self.app.addLabelEntry('LL', 0, 0)
        self.app.addLabelEntry('TB', 1, 0)
        self.app.addButton('Fix', self.fix_loss, 0, 1)
        self.app.addButton('Cancel', self.hide_override_window, 1, 1)
        self.app.stopLabelFrame()
        self.app.stopSubWindow()
        self.app.go()

    # Menus
    def menu(self):
        self.app.showSubWindow('About GBC')

    def log_folder(self):
        self.app.showSubWindow('Log Folder')
    def save_log_folder(self):
        log_folder = os.path.dirname(self.app.getEntry('log_folder_entry'))
        self.app.setSetting('log_folder', log_folder)
        self.app.saveSettings()
    def close_log_window(self):
        self.app.hideSubWindow('Log Folder')

    # Core Functions
    def get_log_list(self):
        file_list = [ file for file in os.listdir(self.log_folder)
                      if os.path.isfile(os.path.join(self.log_folder, file))]
        only_log_pirate_files = [ file for file in file_list if file.endswith('.log')]
        return only_log_pirate_files

    def set_pirate(self, pirate):
        self.app.setLabel('PirateNameDisplay', pirate)

    def individual_pirate_stat(self, pirate):
        print('Updating Individual Pirate Stat for {}'.format(pirate))
        self.app.openSubWindow("Per Pirate Statistics")
        if not self.pirates.get(pirate):
            print('Creating Pirate Dictionary')
            self.pirates[pirate] = {
                'row_id': 0,
                'll_this_battle': 0,
                'll_total': 0,
                'll_average': 0,
                'll_last_battle': 0
            }
            self.pirates[pirate]['row_id'] = max(self.pirates['row_ids']) + 1
            self.pirates['row_ids'].append(self.pirates[pirate]['row_id'])
            print('New pirate {} added with row_id {}'.format(pirate, self.pirates[pirate]['row_id']))
            row_data = [pirate, self.pirates[pirate]['ll_total'], self.pirates[pirate]['ll_average'],
                        self.pirates[pirate]['ll_last_battle'], self.pirates[pirate]['ll_this_battle']]
            self.app.addTableRow('PirateStats', row_data)
            print('Generic Pirate Row Created')

        self.pirates[pirate]['ll_this_battle'] = self.pirates[pirate]['ll_this_battle'] + 1
        print('New LL count for {} is {}'.format(pirate, self.pirates[pirate]['ll_this_battle']))
        row_data = [pirate, self.pirates[pirate]['ll_total'], self.pirates[pirate]['ll_average'],
                    self.pirates[pirate]['ll_last_battle'], self.pirates[pirate]['ll_this_battle']]
        print('Data to be added: {}'.format(row_data))

        self.app.queueFunction(self.app.replaceTableRow, 'PirateStats', self.pirates[pirate]['row_id'], row_data)
        self.app.stopSubWindow()

    def log_parser(self, lines):
        if lines:
            line_list = lines.split('\n')
            try:
                line_list.remove('')
            except ValueError:
                pass
            sanitized_lines = [sub('^\[..:..:..\] ', '', line) for line in line_list]
            print(sanitized_lines)
            if [line for line in sanitized_lines if battle_ended_string in line]:
                self.battle_ended = True
                self.battle_started = False
                self.fight_started = False
                print('battle ended')
            elif [line for line in sanitized_lines if battle_began_string in line]:
                self.battle_started = True
                self.battle_ended = False
                print('battle began')
            elif [line for line in sanitized_lines if battle_began_string in line]:
                self.fight_started = True
            greedy_sanitized_lines = [line for line in sanitized_lines if any(s for s in greedy_strings if s in line)]
            return greedy_sanitized_lines

    def read_log(self):
        log_list = self.get_log_list()
        active_pirate = self.app.getLabel('PirateNameDisplay')
        active_pirate_log = [ pirate for pirate in log_list if pirate.startswith(active_pirate) ]
        log_file = os.path.join(self.log_folder, active_pirate_log[0])
        pygtail = Pygtail(log_file, read_from_end=True)
        while self.active:
            raw_lines = pygtail.read()
            if raw_lines:
                lines = self.log_parser(raw_lines)
                if lines:
                    for line in lines:
                        pirate = line.split(' ')[0]
                        self.this_battle_lls = self.this_battle_lls + 1
                        self.app.queueFunction(self.app.setLabel, 'LLThisBattle', str(self.this_battle_lls))
                        self.app.queueFunction(self.individual_pirate_stat, pirate)
                if self.battle_ended:
                    self.app.queueFunction(self.update_major_stats)
            sleep(0.5)

    def reset_stats(self):
        self.total_lls = 0
        self.average_lls = 0
        self.last_battle_lls = 0
        self.this_battle_lls = 0
        self.battle_count = 0
        self.app.setLabel('LLTotal', str(self.total_lls))
        self.app.setLabel('LLLastBattle', str(self.last_battle_lls))
        self.app.setLabel('LLAverage', str(self.average_lls))
        self.app.setLabel('BattleCount', str(self.battle_count))
        self.app.setLabel('LLThisBattle', str(self.this_battle_lls))
        self.app.deleteAllTableRows("PirateStats")
        self.pirates = {
            'row_ids': [-1]
        }
        print('Stats Reset')

    def start_stop(self, btn):
        if btn == "Start" and not self.active:
            self.active = True
            self.app.setButtonState("Start", "disabled")
            self.app.setButtonState("Stop", "active")
            self.app.thread(self.read_log)
        elif btn == "Stop" and self.active:
            self.active = False
            self.app.setButtonState("Start", "active")
            self.app.setButtonState("Stop", "disabled")

    def update_major_stats(self):
        self.battle_count = self.battle_count + 1
        self.last_battle_lls = self.this_battle_lls
        self.total_lls = self.total_lls + self.this_battle_lls
        self.average_lls = round(self.total_lls / self.battle_count, 1)
        self.this_battle_lls = 0
        self.app.setLabel('LLTotal', str(self.total_lls))
        self.app.setLabel('LLLastBattle', str(self.last_battle_lls))
        self.app.setLabel('LLAverage', str(self.average_lls))
        self.app.setLabel('BattleCount', str(self.battle_count))
        self.app.setLabel('LLThisBattle', str(self.this_battle_lls))
        self.battle_ended = False

        for pirate in self.pirates:
            if pirate != 'row_ids':
                self.pirates[pirate]['ll_total'] = self.pirates[pirate]['ll_total'] + \
                                                   self.pirates[pirate]['ll_this_battle']
                self.pirates[pirate]['ll_last_battle'] = self.pirates[pirate]['ll_this_battle']
                self.pirates[pirate]['ll_this_battle'] = 0
                self.pirates[pirate]['ll_average'] = round(self.pirates[pirate]['ll_total'] / self.battle_count, 1)

                row_data = [pirate, self.pirates[pirate]['ll_total'], self.pirates[pirate]['ll_average'],
                            self.pirates[pirate]['ll_last_battle'], self.pirates[pirate]['ll_this_battle']]
                self.app.queueFunction(self.app.replaceTableRow, 'PirateStats',
                                       self.pirates[pirate]['row_id'], row_data)

    # SubWindow Functions
    def clear_this_battle_lls(self):
        self.this_battle_lls = 0
        self.app.queueFunction(self.app.setLabel, 'LLThisBattle', str(self.this_battle_lls))

    def fix_loss(self):
        self.total_lls = int(self.app.getEntry('LL'))
        self.battle_count = int(self.app.getEntry('TB'))
        self.app.queueFunction(self.app.setLabel, 'BattleCount', str(self.battle_count))
        self.app.queueFunction(self.app.setLabel, 'LLTotal', str(self.total_lls))
        self.hide_override_window()

    def hide_override_window(self):
        self.app.hideSubWindow('Override')

    def show_override_window(self):
        self.app.showSubWindow('Override')

    def pirate_stat_window(self):
        window = self.app.getSetting("Per Pirate Statistics", default=False)
        if not window:
            self.app.showSubWindow("Per Pirate Statistics")
            self.app.setSetting("Per Pirate Statistics", True)

        else:
            self.app.hideSubWindow("Per Pirate Statistics")
            self.app.setSetting("Per Pirate Statistics", False)

            self.app.saveSettings()

    # Send To Puzzle Pirates Functions
    def send_pirate_stats(self, row_id):
        row_data = self.app.getTableRow('PirateStats', row_id)
        formatted_data = 'Pirate: {}, Total LLs: {}, Average LLs: {},' \
                         ' Total Last Battle: {}'.format(row_data[0], row_data[1], row_data[2], row_data[3])
        self.app.info(formatted_data)
        pp_frame = Application().connect(title_re='Puzzle Pirates*')
        window = pp_frame.window()
        window.set_focus()
        clipboard.EmptyClipboard()
        clipboard.win32clipboard.OpenClipboard()
        clipboard.win32clipboard.SetClipboardText(formatted_data)
        clipboard.win32clipboard.CloseClipboard()
        SendKeys('+{INS}')
        SendKeys('{ENTER}')

    def send_totals(self):
        formatted_data = 'Total LLs: {}, Average LLs: {}, ' \
                         'LLs Last Battle: {}, Battles: {}'.format(self.total_lls, self.average_lls,
                                                                   self.last_battle_lls, self.battle_count)
        self.app.info(formatted_data)
        pp_frame = Application().connect(title_re='Puzzle Pirates*')
        window = pp_frame.window()
        window.set_focus()
        clipboard.EmptyClipboard()
        clipboard.win32clipboard.OpenClipboard()
        clipboard.win32clipboard.SetClipboardText(formatted_data)
        clipboard.win32clipboard.CloseClipboard()
        SendKeys('+{INS}')
        SendKeys('{ENTER}')


if __name__ == "__main__":
    program = GreedyBashCounter()
