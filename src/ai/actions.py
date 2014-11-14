def use_tech(data):
	if data.stamina < 20:
		return
	print(data.data.name, "uses a technique!")
	data.stamina -= 20