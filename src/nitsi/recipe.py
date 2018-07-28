#!/usr/bin/python3

import logging
import os

logger = logging.getLogger("nitsi.recipe")



class RecipeExeption(Exception):
    def __init__(self, message):
        self.message = message



# Should read the test, check if the syntax are valid
# and return tuples with the ( host, command ) structure
class Recipe():
    def __init__(self, path, circle=[], machines=[], fallback_machines=[]):
        self.recipe_file = path
        try:
            self.path = os.path.dirname(self.recipe_file)
            self.path = os.path.abspath(self.path)
            self.name = os.path.basename(self.path)
        except BaseException as e:
            logger.error("Failed to get the path to this recipe")
            raise e

        self.log = logger.getChild(self.name)
        self.log.debug("Path of recipe is: {}".format(self.recipe_file))
        self._recipe = None
        self._machines = machines
        self._fallback_machines = fallback_machines

        self.log.debug("Machine names we use when we substitute the all statement: {}".format(self._machines))

        self.log.debug("Length of the cirle list {}".format(len(circle)))
        self.in_recursion = True
        if len(circle) == 0:
            self.in_recursion = False

        self.log.debug("We are in a recursion: {}".format(self.in_recursion))

        self.circle = circle
        self.log.debug("Recipes we have already included: {}".format(self.circle))

        if not os.path.isfile(self.recipe_file):
            self.log.error("{} is not a file".format(self.recipe_file))
            raise RecipeExeption("{} is not a file".format(self.recipe_file))

        try:
            with open(self.recipe_file) as fobj:
                self.raw_recipe = fobj.readlines()
        except FileNotFoundError as error:
            self.log.error("No such file: {}".format(self.recipe_file))
            raise error

    @property
    def recipe(self):
        if not self._recipe:
            self.parse()

        return self._recipe

    @property
    def machines(self):
        return self._machines

    def parse(self):
        self._recipe = []
        i = 1
        for line in self.raw_recipe:
            # Check if the line is empty
            if line.strip() == "":
                self.log.debug("Skipping empty line {}".format(i))
                i = i + 1
                continue

            # Check if the line is a comment
            if line.strip().startswith("#"):
                self.log.debug("Skipping comment in line {}".format(i))
                i = i + 1
                continue

            raw_line = line.split(":", 1)
            if len(raw_line) < 2:
                self.log.error("Error parsing the recipe in line {}".format(i))
                raise RecipeExeption("Error parsing the recipe in line {}".format(i))
            cmd = raw_line[1].strip()

            raw_line = raw_line[0].strip().split(" ")
            if len(raw_line) == 0:
                self.log.error("Failed to parse the recipe in line {}".format(i))
                raise RecipeExeption("Failed to parse the recipe in line {}".format(i))

            if raw_line[0].strip() == "":
                    self.log.error("Failed to parse the recipe in line {}".format(i))
                    raise RecipeExeption("Failed to parse the recipe in line {}".format(i))

            machine = raw_line[0].strip()

            if len(raw_line) == 2:
                extra = raw_line[1].strip()
            else:
                extra = ""

            # We could get a machine here or a include statement
            if machine == "include":
                path = cmd.strip()
                path = os.path.normpath(self.path + "/" + path)

                # If we did not get a valid file we asume that we get a valid path to a test.
                if os.path.isdir(path):
                    path = path + "/recipe"

                if path in self.circle:
                    self.log.error("Detect import loop!")
                    raise RecipeExeption("Detect import loop!")
                self.circle.append(path)
                recipe_to_include = Recipe(path, circle=self.circle)

            if machine == "include":
                self._recipe.extend(recipe_to_include.recipe)
            else:
                # Support also something like 'alice,bob: echo'
                machines = machine.split(",")
                for machine in machines:
                    self._recipe.append((machine.strip(), extra.strip(), cmd.strip()))

            # Increase the line number by one
            i = i + 1

        # Substitue the all statement
        if not self.in_recursion:
            self.log.debug("We are not in a recursion")
            # We will store the machine names we use to substitute the all statement
            # in tmp_machines to keep the code which actually does the substitution clear
            tmp_machines = None

            # Check if we get a setting to substitute the all statement
            if len(self.machines) != 0:
                tmp_machines = self.machines

            # Second try to fill tmp_machines
            if not tmp_machines:
                #  dertermine machines we use in this recipe
                tmp = []
                for line in self.recipe:
                    self.log.debug(line)
                    if not line[0] in tmp and line[0] != "all":
                        tmp.append(line[0])

                self.log.debug("Machines except all in the recipe: {}".format(tmp))

                # Check if we got anything else then all: in th recipe
                if len(tmp) != 0:
                    tmp_machines = tmp

            # If we get here we are using all machines in the virtual environment as fallback value
            if not tmp_machines:
                tmp_machines = self._fallback_machines

            tmp_recipe = []
            for line in self._recipe:
                if line[0] != "all":
                    tmp_recipe.append(line)
                else:
                    for machine in tmp_machines:
                        tmp_recipe.append((machine.strip(), line[1], line[2]))

            self._recipe = tmp_recipe