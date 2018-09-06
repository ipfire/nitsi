

class CMD():
    def __init__(self, prompt="", help={}, intro = ""):
        self.prompt = "nitsi: "
        self.help_min = {"help": "Shows this help message", "?": "Same as 'help'"}
        self.help = help

        if prompt != "":
            self.prompt = prompt

        self.intro = ""

        if intro != "":
            self.intro = intro

    def print_intro(self, intro=""):
        if intro == "":
            intro = self.intro
        self.print_to_cmd(intro)

    def print_to_cmd(self, string):
        print(string, end="\n")

    def read_from_cmd(self, prompt=""):
        if prompt == "":
            prompt = self.prompt
        return input(prompt)

    def get_input(self, valid_commands=[], help={}):
        valid_commands = valid_commands + [ "?", "help" ]
        input=""

        while True:
            input = self.read_from_cmd()
            if input not in valid_commands:
                self.print_to_cmd("{} is not valid command.".format(input))
                continue

            # print help
            if input == "help" or input == "?":
                self.print_help(help=help)
                continue

            # if we get here we get a valid input
            break

        return input

    def print_help(self, help={}):
        if len(help) == 0:
            help = self.help

        # Update help with help_min
        tmp_help = self.help_min
        tmp_help.update(help)
        help = tmp_help

        for key in help:
            self.print_to_cmd("{}: {}".format(key, help[key]))
