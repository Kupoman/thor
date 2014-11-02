class Monster:
	def __init__(self, name="Monster", hp=100, recovery=1, damage=25):
		self.name = name
		self.hp = hp
		self.recovery = recovery

		self.damage = damage

		self.current_hp = self.hp
		self.current_stamina = 0

		self.target = None
