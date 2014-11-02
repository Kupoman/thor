import techniques


class Monster(object):
	@classmethod
	def deserialize(cls, json_dictionary):
		return Monster(**json_dictionary)

	def __init__(self, name="Monster", attack=20, defense=20, intelligence=20,
			stamina=20, speed=20):
		self.name = name
		self.race = "Unknown"

		# Base Stats
		self.attack = attack
		self.defense = defense
		self.intelligence = intelligence
		self.stamina = stamina
		self.speed = speed

		# Derived stats
			# self.damage
			# self.hp
			# self.command_count
			# self.initiative
			# self.recovery
			# self.special_attack
			# self.special_defense
			# self.accuracy
			# self.evasion

		self.current_hp = 0
		self.current_stamina = 0

		self.target = None
		self.techniques = [techniques.Scratch]

	@property
	def damage(self):
		return self.attack * 10

	@property
	def hp(self):
		return self.defense * 10

	@property
	def command_count(self):
		return self.intelligence / 5

	@property
	def initiative(self):
		return self.speed

	@property
	def recovery(self):
		return 0.125 * self.stamina

	@property
	def special_attack(self):
		return 0.5 * (self.attack + self.intelligence)

	@property
	def sepcial_defense(self):
		return 0.5 * (self.defense + self.intelligence)

	@property
	def accuracy(self):
		return 0.5 * (self.attack + self.speed)

	@property
	def evasion(self):
		return 0.5 * (self.defense + self.speed) / 100.0

	def serialize(self):
		data = {}
		data['name'] = self.name
		data['attack'] = self.attack
		data['defense'] = self.defense
		data['intelligence'] = self.intelligence
		data['stamina'] = self.stamina
		data['speed'] = self.speed

		return data
