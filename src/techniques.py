import random

class Technique(object):
	name = "Technique"

	damage = 0
	special = 0
	inaccuracy = 0
	cost = 0

	@classmethod
	def get_chance_to_hit(cls, monster):
		rank_offset = 6
		rank_gain =1.15
		rank_effect = 15
		return min((monster.accuracy + rank_effect * (rank_offset - rank_gain * cls.inaccuracy)), 95) / 100.0

	@classmethod
	def get_stamina_cost(cls, monster):
		rank_gain = 10
		return cls.cost * rank_gain

	@classmethod
	def get_damage_dealt(cls, monster):
		rank_gain = 0.5
		per_point = 2
		return rank_gain * (cls.damage+1) * per_point * monster.attack

	@classmethod
	def get_special_chance(cls, monster):
		return 0

	@classmethod
	def use(cls, user, target):
		# Check for hit
		cth = cls.get_chance_to_hit(user)
		if random.random() > cth:
			print("Missed!")
			return

		# Check for evade
		dodge_roll = random.random()
		print(dodge_roll, target.evasion)
		if dodge_roll < target.evasion:
			print("Dodged!")
			return

		# Apply cost
		user.current_stamina -= cls.get_stamina_cost(user)

		# Apply damage
		target.current_hp -= cls.get_damage_dealt(user)


class Scratch(Technique):
	name = "Scratch"

	damage = 1
	special = 0
	inaccuracy = 1
	cost = 1