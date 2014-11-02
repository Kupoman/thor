import random


_ICON_DIR = "art/attacks/"


class Command(object):
	name = "Command"
	icon = _ICON_DIR + "attack_mask.png"

	@classmethod
	def run(monster):
		raise NotImplementedError("Do not use the base Command")


class Attack(Command):
	name = "Attack"
	icon = _ICON_DIR + "meteor.png"

	@classmethod
	def run(cls, monster):
		if not monster.target:
			print("No target")
			return

		possible_techs = [tech for tech in monster.techniques
			if tech.get_stamina_cost(monster) <= monster.current_stamina]

		if not possible_techs:
			print(monster.techniques)
			print("No technique to use")
			return

		tech = random.choice(possible_techs)
		tech.use(monster, monster.target)


class Wait(Command):
	name = "Wait"
	icon = _ICON_DIR + "black-hole.png"

	@classmethod
	def run(cls, monster):
		pass
