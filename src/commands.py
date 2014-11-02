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

		cost = 15
		if monster.current_stamina >= cost:
			monster.current_stamina -= cost
			monster.target.current_hp -= 25


class Wait(Command):
	name = "Wait"
	icon = _ICON_DIR + "black-hole.png"

	@classmethod
	def run(cls, monster):
		pass
