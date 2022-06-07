

def get_curr_programs(name):
    programs = name.split("||")
    programs = [x.strip() for x in programs]
    return programs


def get_programs(data):
    programs = data["recursive_variables"]
    for program in programs:
        programs[program] = programs[program].split("o+")
        for i in range(len(programs[program])):
            programs[program][i] = programs[program][i].strip()
    return programs


# programs is a dict program_name -> [list of nondeterministic choices [ which are list] ]
# deal with duplicates
def create_automata(data):
    initial_state = data['program']
    programs = get_programs(data)
    automata = dict()
    nodes = list()
    nodes.append(initial_state)
    while nodes:
        curr = nodes.pop()
        automata[curr] = dict()
        curr_programs = get_curr_programs(curr)
        for index,program in enumerate(curr_programs):
            if program.startswith("@Recursive("):
                program_name = program.split("@Recursive(")[1][:-1]
                for choice in programs[program_name]:
                    if check_send(choice):
                        new_node = list(curr_programs)
                        new_node[index] = get_next_state(choice)
                        pss = " "
                        for i in new_node[:-1]:
                            pss += str(i + "|| ").strip()
                        pss += str(new_node[-1]).strip()
                        ## add channel
                        pss = pss.strip()
                        if pss not in automata[curr]:
                            automata[curr][pss] = list()
                        automata[curr][pss].append( get_channel(choice) + " !")
                        if pss not in automata:
                            nodes.append(pss)
                        rcfg = check_rcfg(programs,choice,curr_programs,index)
                        if rcfg:
                            new_node = list(curr_programs)
                            new_node[index] = get_next_state(choice)
                            for tuple in rcfg:
                                new_node[tuple[0]] = tuple[1]
                            pss = " "
                            for i in new_node[:-1]:
                                pss += str(i + "|| ").strip()
                            pss += str(new_node[-1]).strip()
                            ## add channel
                            pss = pss.strip()
                            if pss not in automata[curr]:
                                automata[curr][pss] = list()
                            automata[curr][pss].append("RCFG( " + get_channel(choice) + " )")
                            if pss not in automata:
                                nodes.append(pss)

    return automata

def check_send(program):
    return (program.strip()).startswith("@Send")

def check_rcfg(programs,sending_choice,curr_programs,index_sending):
    channel = get_channel(sending_choice).strip()
    receiving = list()
    for index,program in enumerate(curr_programs):
        if index == index_sending:
            continue
        if program.startswith("@Recursive("):
            program_name = program.split("@Recursive(")[1][:-1]
            for choice in programs[program_name]:
                if check_receive(choice) and get_channel(choice) == channel:
                    receiving.append((index,get_next_state(choice)))
    return receiving

def check_receive(choice):
    return choice.startswith("@Receive")

def get_channel(program):
    channel = program.split("@Channel(")[1]
    channel = channel.split(")")[0].strip()
    return channel
def get_next_state(program):
    return "".join(program.split(";")[1:])

