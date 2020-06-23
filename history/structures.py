MAX_SIZE = 12

class LRU():
	def add(self, key, list):
		if key in list:
			list.remove(key)
		list.append(key)
		if len(list) > MAX_SIZE:
			return list[1:]
		return list
