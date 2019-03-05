import json
import qualtrics as qt

class Model:
	def __init__(self, items={}, functions={}):
		self.items = items
		self.functions = functions

	def get(self, *keys, default=None):
		current = self.items
		for key in keys[:-1]:
			current = current.get(key, None)
			if type(current) is not dict:
				return default
		return current.get(keys[-1], default)

	def set(self, *keys, item=None, function=None):
		if item is not None:
			current = self.items
			for key in keys[:-1]:
				result = current.get(key, None)
				if type(result) is not dict:
					if result is None:
						current[key] = result = {}
					else:
						raise KeyError(keys)
				current = result
			current[keys[-1]] = item
		if function is not None:
			current = self.functions
			for key in keys[:-1]:
				result = current.get(key, None)
				if type(result) is not dict:
					if result is None:
						current[key] = result = {}
					else:
						raise KeyError(keys)
				current = result
			current[keys[-1]] = function


	def invoke(self, *keys, **kwargs):
		current = self.functions
		for key in keys[:-1]:
			current = current.get(key, None)
			if type(current) is not dict:
				raise KeyError(keys)
		return current.get(keys[-1])(**kwargs)
	
	class JSONEncoder(json.JSONEncoder):
		def default(self, obj):
			if type(obj) not in { dict, set, list, str, int, float }:
				obj = str(obj)
			return obj
