#!/usr/bin/python3

import os

import logging

logger = logging.getLogger("nitsi.recipe")



class RecipeExeption(Exception):
    pass



# Should read the test, check if the syntax are valid
# and return tuples with the ( host, command ) structure
class recipe():
    def __init__(self, path, circle=[]):
        self.recipe_file = path
        try:
            self.path = os.path.dirname(self.recipe_file)
            self.name = os.path.basename(self.path)
        except BaseException as e:
            logger.error("Failed to get the name of the test to this recipe")
            raise e

        self.log = logger.getChild(self.name)
        self.log.debug("Path of recipe is: {}".format(self.recipe_file))
        self._recipe = None
        self._machines = None

        self.in_recursion = True
        if len(circle) == 0:
            self.in_recursion = False

        self.circle = circle
        self.log.debug(circle)
        self.log.debug(self.circle)

        if not os.path.isfile(self.recipe_file):
            self.log.error("No such file: {}".format(self.recipe_file))

        try:
            with open(self.recipe_file) as fobj:
                self.raw_recipe = fobj.readlines()
        except FileNotFoundError as error:
            self.log.error("No such file: {}".format(vm_xml_file))

    @property
    def recipe(self):
        if not self._recipe:
            self.parse()

        return self._recipe

    @property
    def machines(self):
        if not self._machines:
            self._machines = []
            for line in self._recipe:
                if line[0] != "all" and line[0] not in self._machines:
                    self._machines.append(line[0])

        return self._machines

    def parse(self):
        self._recipe = []
        i = 1
        for line in self.raw_recipe:
            raw_line = line.split(":")
            if len(raw_line) < 2:
                self.log.error("Error parsing the recipe in line {}".format(i))
                raise RecipeExeption
            cmd = raw_line[1].strip()
            raw_line = raw_line[0].strip().split(" ")
            if len(raw_line) == 0:
                self.log.error("Failed to parse the recipe in line {}".format(i))
                raise RecipeExeption

            if raw_line[0].strip() == "":
                    self.log.error("Failed to parse the recipe in line {}".format(i))
                    raise RecipeExeption

            machine = raw_line[0].strip()

            if len(raw_line) == 2:
                extra = raw_line[1].strip()
            else:
                extra = ""

            # We could get a machine here or a include statement
            if machine == "include":
                path = cmd.strip()
                path = os.path.normpath(self.path + "/" + path)
                path = path + "/recipe"
                if path in self.circle:
                    self.log.error("Detect import loop!")
                    raise RecipeExeption
                self.circle.append(path)
                recipe_to_include = recipe(path, circle=self.circle)

            if machine == "include":
                self._recipe.extend(recipe_to_include.recipe)
            else:
                # Support also something like 'alice,bob: echo'
                machines = machine.split(",")
                for machine in machines:
                    self._recipe.append((machine.strip(), extra.strip(), cmd.strip()))
            i = i + 1

            if not self.in_recursion:
                tmp_recipe = []
                for line in self._recipe:
                    if line[0] != "all":
                        tmp_recipe.append(line)
                    else:
                        for machine in self.machines:
                            tmp_recipe.append((machine.strip(), line[1], line[2]))

                self._recipe = tmp_recipe