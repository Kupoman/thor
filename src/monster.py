class Monster:
	def __init__(self, name="Monster", attack=1, defense=1, intelligence=1,
			stamina=1, speed=1):
		self.name = name

		# Base Stats
		self.attack = attack
		self.defense = defense
		self.intelligence = intelligence
		self.stamina = stamina
		self.speed = speed

		# Derived stats
		self.damage = self.attack * 10
		self.hp = self.defense * 10
		self.command_count = self.intelligence
		self.initiative = self.speed
		self.recovery = self.stamina
		self.special_attack = 0.5 * (self.attack + self.intelligence)
		self.special_defense = 0.5 * (self.defense + self.intelligence)
		self.accuracy = 0.5 * (self.attack + self.speed)
		self.evasion = 0.5 * (self.defense + self.speed)

		self.current_hp = self.hp
		self.current_stamina = 0

		self.target = None
