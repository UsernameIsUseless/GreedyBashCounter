from re import sub
greedy_strings = [
    'executes a masterful strike',
    'swings a devious blow',
    'performs a powerful attack',
    'delivers an overwhelming barrage'
]
battle_ended_string = 'as your initial cut of the booty!'
battle_began_string = 'intercepted'

def log_parser(lines):
    if lines:
        line_list = lines.split('\n')
        try:
            line_list.remove('')
        except ValueError:
            pass
        battle_began, battle_ended = False, False
        sanitized_lines = [ sub('^\[..\:..\:..\] ', '', line) for line in line_list ]
        print(sanitized_lines)
        if [ line for line in sanitized_lines if battle_ended_string in line ]:
            battle_ended = True
            print('battle ended')
        elif [ line for line in sanitized_lines if battle_began_string in line ]:
            battle_began = True
            print('battle began')
        greedy_sanitized_lines = [ line for line in sanitized_lines if any(s for s in greedy_strings if s in line) ]
        return greedy_sanitized_lines, battle_began, battle_ended

