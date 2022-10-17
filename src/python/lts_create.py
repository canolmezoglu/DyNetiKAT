from src.python.util import generate_error_message, generate_outfile
from src.python.netkat_parser import NetKATComm
from gvgen import GvGen

class Lts_creator:
    def __init__(self, direct, netkat_path, netkat_version):
        self.direct = direct
        self.netkat_path = netkat_path
        self.netkat_version = netkat_version

    def get_curr_programs(self, name, grr):
        name = name.split(",")[0]
        programs = name.split("||")
        programs = [x.strip() for x in programs]
        final_programs = list()
        for program in programs:
            # eger recursive bisi okuyosam
            if program.startswith("@Recursive("):
                # programin ismini aliyorum
                program_name = program.split("@Recursive(")[1]
                program_name = program_name.split(")")[0]
                program_name = program_name.strip()
                if "||" in grr[program_name]:
                    unfolded = grr[program_name].split("||")
                    # nondeterministic choice check -FOTGOTTEN GUARDED RECURAS
                    while any([x.startswith("@Recursive(") for x in unfolded]):
                        new = list()
                        for i in unfolded:
                            if i.startswith("@Recursive("):
                                program_name = i.split("@Recursive(")[1]
                                program_name = program_name.split(")")[0]
                                new += grr[program_name].split("||")
                            else:
                                new.append(i)
                        unfolded = new
                    final_programs += unfolded
                else:
                    final_programs.append(grr[program_name])
            else:
                final_programs.append(program)
        return final_programs, programs

    def get_packages(self, packages, input):
        i = 2
        if input:
            i = 1
        packages = packages.split(",")[i]
        packages = packages.split("::")[:-1]
        ##packages = [(x[x.find("(")+1:x.find(")")+1]).strip() for x in packages]
        return packages

    def get_programs(self, data):
        programs = data["recursive_variables"]
        for program in programs:
            programs[program] = programs[program].strip()
        return programs

    def give_packages(self, packages):
        stringi = ""
        for package in packages:
            stringi += package
            stringi += "::"

        return (stringi + "{}")

    # programs is a dict program_name -> [list of nondeterministic choices [ which are list] ]
    # deal with duplicates
    def create_automata(self, data):
        automata = dict()
        nodes = list()
        nodes.append(data['program'].strip())
        initial_state = nodes[0]
        programs = self.get_programs(data)
        while nodes:
            curr = nodes.pop()
            automata[curr] = dict()
            P, recursive = self.get_curr_programs(curr, programs)
            H = self.get_packages(curr, True)
            HPrime = self.get_packages(curr, False)
            for index, program in enumerate(P):
                if "o+" in program:
                    choices = program.split("o+")
                    choices = [c.strip() for c in choices]
                    for choice in choices:
                        if self.check_send(choice) or self.check_receive(choice):
                            new_node = list(P)
                            new_node[index] = self.get_next_state(choice)
                            pss = self.get_next_program(choice, index, programs, P, H, HPrime)
                            if pss not in automata[curr]:
                                automata[curr][pss] = list()
                            if self.check_send(choice):
                                automata[curr][pss].append(self.get_channel(choice) + " !")
                            else:
                                 automata[curr][pss].append(self.get_channel(choice) + " ?")
                            if pss not in automata:
                                nodes.append(pss)
                            rcfg = self.check_rcfg(P, choice, index)
                            if rcfg and self.check_send(choice):
                                pss = self.get_next_program(choice, index, programs, P, H, HPrime, rcfg=rcfg)
                                ## add channel
                                pss = pss.strip()
                                if pss not in automata[curr]:
                                    automata[curr][pss] = list()
                                automata[curr][pss].append("RCFG( " + self.get_channel(choice) + " )")
                                if pss not in automata:
                                    nodes.append(pss)
                        elif self.check_netkat(choice) and H:
                            netkat_parser = NetKATComm(self.direct, self.netkat_path, self.netkat_version,
                                                       generate_outfile(self.direct,
                                                                        "netkat_" + "_"))
                            netkat_policy = choice.split(";")[0]
                            netkat_policy = netkat_policy.split("@NetKAT(")[1]
                            netkat_policy = netkat_policy[:-3]
                            elem = H[0]
                            result = netkat_parser.execute2(netkat_policy, elem)
                            if not result:
                                continue
                            pss = self.get_next_program(choice, index, programs, P, H, HPrime, NetKAT_output=result)
                            if pss not in automata[curr]:
                                automata[curr][pss] = list()
                            automata[curr][pss].append("netkat( " + (str(elem)) + " >> " + str(result) + " )")
                            if pss not in automata:
                                nodes.append(pss)
                elif self.check_send(program) or self.check_receive(program):
                    pss = self.get_next_program(program, index, programs, P, H, HPrime)
                    if pss not in automata[curr]:
                        automata[curr][pss] = list()
                    if self.check_send(program):
                        automata[curr][pss].append(self.get_channel(program) + " !")
                    else:
                        automata[curr][pss].append(self.get_channel(program) + " ?")
                    if pss not in automata:
                        nodes.append(pss)
                    rcfg = self.check_rcfg(P, program, index)
                    if rcfg and self.check_send(program):
                        pss = self.get_next_program(program, index, programs, P, H, HPrime, rcfg=rcfg)
                        ## add channel
                        pss = pss.strip()
                        if pss not in automata[curr]:
                            automata[curr][pss] = list()
                        automata[curr][pss].append("RCFG( " + self.get_channel(program) + " )")
                        if pss not in automata:
                            nodes.append(pss)
                elif self.check_netkat(program) and H:
                    netkat_parser = NetKATComm(self.direct, self.netkat_path, self.netkat_version,
                                               generate_outfile(self.direct,
                                                                "netkat_" + "_"))
                    netkat_policy = program.split(";")[0]
                    netkat_policy = netkat_policy.split("@NetKAT(")[1]
                    netkat_policy = netkat_policy[:-3]
                    elem = H[0]
                    result = netkat_parser.execute2(netkat_policy, elem)
                    if not result:
                        continue
                    pss = self.get_next_program(program, index, programs, P, H, HPrime, NetKAT_output=result)
                    if pss not in automata[curr]:
                        automata[curr][pss] = list()
                    automata[curr][pss].append("netkat( " + (str(elem)) + " >> " + str(result) + " )")
                    if pss not in automata:
                        nodes.append(pss)
        dotfile = self.create_dot_file(automata,initial_state)
        print(dotfile)
        return automata

    def check_send(self, program):
        return (program.strip()).startswith("@Send") or (program.strip()).startswith("(@Send")

    def check_netkat(self, program):
        return (program.strip()).startswith("@NetKAT")

    def check_rcfg(self, P, sending_choice, index_sending):
        channel = self.get_channel(sending_choice).strip()
        receiving = list()
        for index, program in enumerate(P):
            if index == index_sending:
                continue
            if "o+" in program:
                choices = program.split("o+")
                choices = [c.strip() for c in choices]
                for choice in choices:
                    if self.check_receive(choice) and self.get_channel(choice) == channel:
                        receiving.append((index, self.get_next_state(choice)))
            else:
                if self.check_receive(program) and self.get_channel(program) == channel:
                    receiving.append((index, self.get_next_state(program)))
        return receiving

    def check_receive(self, choice):
        return choice.startswith("@Receive") or (choice.strip()).startswith("(@Receive")

    def create_dot_file(self, automata, initial):
        dotlines = ["digraph automaton {"]
        dotlines.append("	graph[fontsize=8]")
        dotlines.append("	rankdir=LR; " )
        dotlines.append("	graph[fontsize=8]")
        numbered_automata = self.number_automata(automata,initial)
        for node in numbered_automata:
            dotlines.append(" node{} [label = \"{}\"];".format(numbered_automata[node], node))
        print("node count: " + str(len(automata)))
        edge_count = 0
        for node in automata:
            for node2 in automata[node]:
                for labels in automata[node][node2]:
                    edge_count += 1
                    if labels.startswith("netkat"):
                        labels = labels[6:]
                        labels = labels.replace(">>",",")
                    dotlines.append(" node{}->node{} [label = \"{}\"];".format(numbered_automata[node],numbered_automata[node2], labels))
        dotlines.append('}')
        print("edge count: " + str(edge_count))
        dot = "\n".join(dotlines)
        return dot

    def number_automata(self,automata,initial):
        newdict= dict()
        newdict[initial] = 1
        for node in automata:
            if node not in newdict:
                newdict[node] = len(newdict) + 1
        return newdict
    def get_channel(self, program):
        channel = program.split("@Channel(")[1]
        channel = channel.split(")")[0].strip()
        return channel

    def get_next_state(self, program):
        ccc = program.split(";")[1:]
        if len(ccc) == 2:
            temp = ccc.pop()
            ccc.append(";")
            ccc.append(temp)
        return "".join(ccc)

    def get_recursive_name(self, programs, value):
        for k in programs:
            if programs[k] == value:
                return "@Recursive(" + k + ")"
        return -1

    def get_next_program(self, choice, index, programs, P, H, HPrime, rcfg=None, NetKAT_output=None):
        new_node = list(P)
        new_node[index] = self.get_next_state(choice)
        if rcfg is not None:
            for tuple in rcfg:
                new_node[tuple[0]] = tuple[1]
        pss = " "
        for i in new_node[:-1]:
            i = i.strip()
            if (i != "bot" and i != "bot)") and self.get_recursive_name(programs, i) != -1:
                pss += str(self.get_recursive_name(programs, i) + "|| ").strip()
            elif (i != "bot" and i != "bot)"):
                pss += str(i + "|| ").strip()
        if (i != "bot" and i != "bot)") and self.get_recursive_name(programs, new_node[-1]) != -1:
            pss += str(self.get_recursive_name(programs, new_node[-1])).strip()
        elif (i != "bot" and i != "bot)"):
            pss += str(new_node[-1]).strip()
        if NetKAT_output is None or len(NetKAT_output) == 0:
            ## add channel
            pss = pss.strip()
            pss += "," + self.give_packages(H) + "," + self.give_packages(HPrime)
            return pss
        new_input = list(H)
        new_input.pop(0)
        new_output = list(HPrime)
        new_output += NetKAT_output
        pss += "," + self.give_packages(new_input) + "," + self.give_packages(new_output)
        pss = pss.strip()
        return pss
