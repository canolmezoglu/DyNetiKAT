from src.python.util import generate_error_message, generate_outfile
from src.python.netkat_parser import NetKATComm


class Lts_creator:
    def __init__(self, direct, netkat_path, netkat_version):
        self.direct = direct
        self.netkat_path = netkat_path
        self.netkat_version = netkat_version


    def get_curr_programs(self,name):
        name = name.split(",")[0]
        programs = name.split("||")
        programs = [x.strip() for x in programs]
        return programs

    def get_packages(self,packages,input):
        i = 2
        if input:
            i = 1
        packages = packages.split(",")[i]
        packages = packages.split("::")[:-1]
        ##packages = [(x[x.find("(")+1:x.find(")")+1]).strip() for x in packages]
        return packages


    def get_programs(self,data):
        programs = data["recursive_variables"]
        for program in programs:
            programs[program] = programs[program].split("o+")
            for i in range(len(programs[program])):
                programs[program][i] = programs[program][i].strip()
        return programs

    def give_packages(self,packages):
        stringi = ""
        for package in packages:
            stringi += package
            stringi += "::"

        return (stringi + "{}")


    # programs is a dict program_name -> [list of nondeterministic choices [ which are list] ]
    # deal with duplicates
    def create_automata(self,data):
        initial_state = data['program'].strip()
        programs = self.get_programs(data)
        automata = dict()
        nodes = list()
        nodes.append(initial_state)
        while nodes:
            curr = nodes.pop()
            automata[curr] = dict()
            curr_programs = self.get_curr_programs(curr)
            curr_input = self.get_packages(curr,True)
            curr_output = self.get_packages(curr, False)
            for index,program in enumerate(curr_programs):
                if program.startswith("@Recursive("):
                    program_name = program.split("@Recursive(")[1][:-1]
                    for choice in programs[program_name]:
                        if self.check_send(choice):
                            new_node = list(curr_programs)
                            new_node[index] = self.get_next_state(choice)
                            pss = " "
                            for i in new_node[:-1]:
                                pss += str(i + "|| ").strip()
                            pss += str(new_node[-1]).strip()
                            pss += "," + self.give_packages(curr_input) + "," + self.give_packages(curr_output)

                            ## add channel
                            pss = pss.strip()
                            if pss not in automata[curr]:
                                automata[curr][pss] = list()
                            automata[curr][pss].append( self.get_channel(choice) + " !")
                            if pss not in automata:
                                nodes.append(pss)
                            rcfg = self.check_rcfg(programs,choice,curr_programs,index)
                            if rcfg:
                                new_node = list(curr_programs)
                                new_node[index] = self.get_next_state(choice)
                                for tuple in rcfg:
                                    new_node[tuple[0]] = tuple[1]
                                pss = " "
                                for i in new_node[:-1]:
                                    pss += str(i + "|| ").strip()
                                pss += str(new_node[-1]).strip()
                                pss += "," + self.give_packages(curr_input) + "," + self.give_packages(curr_output)
                                ## add channel
                                pss = pss.strip()
                                if pss not in automata[curr]:
                                    automata[curr][pss] = list()
                                automata[curr][pss].append("RCFG( " + self.get_channel(choice) + " )")
                                if pss not in automata:
                                    nodes.append(pss)
                        elif self.check_netkat(choice) and curr_input:
                           new_node = list(curr_programs)
                           new_node[index] = self.get_next_state(choice)
                           netkat_parser = NetKATComm(self.direct, self.netkat_path, self.netkat_version,
                                                      generate_outfile(self.direct,
                                                                       "netkat_"  + "_" ))
                           netkat_policy = choice.split(";")[0]
                           netkat_policy = netkat_policy.split("@NetKAT(")[1]
                           netkat_policy = netkat_policy[:-3]
                           elem = curr_input[0]
                           result = netkat_parser.execute2(netkat_policy,elem)
                           if not result:
                               continue
                           new_input = list(curr_input)
                           new_input.pop(0)
                           new_output = list(curr_output)
                           new_output += result
                           pss = " "
                           for i in new_node[:-1]:
                               pss += str(i + "|| ").strip()
                           pss += str(new_node[-1]).strip()
                           pss += "," + self.give_packages(new_input) + "," + self.give_packages(new_output)
                           pss = pss.strip()
                           if pss not in automata[curr]:
                               automata[curr][pss] = list()
                           automata[curr][pss].append("netkat( " + (str(elem)) + " >> " + str(result) + " )")
                           if pss not in automata:
                               nodes.append(pss)






        return automata

    def check_send(self,program):
        return (program.strip()).startswith("@Send")
    def check_netkat(self,program):
        return (program.strip()).startswith("@NetKAT")

    def check_rcfg(self,programs,sending_choice,curr_programs,index_sending):
        channel = self.get_channel(sending_choice).strip()
        receiving = list()
        for index,program in enumerate(curr_programs):
            if index == index_sending:
                continue
            if program.startswith("@Recursive("):
                program_name = program.split("@Recursive(")[1][:-1]
                for choice in programs[program_name]:
                    if self.check_receive(choice) and self.get_channel(choice) == channel:
                        receiving.append((index,self.get_next_state(choice)))
        return receiving

    def check_receive(self,choice):
        return choice.startswith("@Receive")

    def get_channel(self,program):
        channel = program.split("@Channel(")[1]
        channel = channel.split(")")[0].strip()
        return channel

    def get_next_state(self,program):
        return "".join(program.split(";")[1:])

