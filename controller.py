from model import Model
from components import *
import json
import os
import csv

class Controller:
	def __init__(self, model=None):
		self.model = model if model is not None else Model()

	def get(self, *keys, default=None):
		return self.model.get(*keys, default=default)

	def set(self, *keys, item=None, function=None):
		self.model.set(*keys, item=item, function=function)	
	
	def populate_api_token(self):
		APITokenDialog(self.get("components", "root"), self)

	def get_or_populate_api_token(self):
		token = self.get("api", "token", default=None)
		if token is None:
			APITokenDialog(self.get("components", "root"), self)
			token = self.get("api", "token")
		return token
	
	def populate_surveys(self):
		token = self.get_or_populate_api_token()
		if token is None:
			return
		# populate model with surveys
		api = self.get("api", "gateway")
		try:
			for survey in api.get_surveys(token):
				self.set("surveys", survey.id, item=survey)
		except Exception as e:
			messagebox.showerror("Error", e)
			raise e
		# show surveys in grid
		top = self.get("components", "top")
		if top.rows:
			top.rows.destroy()
		top.rows = SurveyRows(top.body.interior, self)
	
	def populate_responses(self):
		# ensure api token is set
		token = self.get_or_populate_api_token()
		if token is None:
			return
		# ensure surveys are populated
		rows = self.get("components", "top").rows
		if rows is None:
			self.populate_surveys()
			rows = self.get("components", "top").rows
			if rows is None:
				return
		for sid in self.get("surveys"):
			rows.get_row(sid).set_info("")
		# get response object in model
		responses = self.get("responses")
		if responses is None:
			responses = {}
			self.set("responses", item=responses)
		else:
			# clear if it is already populated 
			responses.clear()
		# build up responses for selected surveys	
		selected = self.get("select", "surveys")
		for sid in selected:
			# ensure survey exists
			survey = self.get("surveys", sid)
			if survey is None:
				messagebox.showerror("Error", "Survey not found: {}".format(sid))
				return
			# ensure primary question is set
			primary = self.get("defaults", "questions", "primary")
			if primary is None:
				messagebox.showerror("Error", "Primary question not found, please set default question.")
				return
			# ensure secondary questions are set
			secondary = self.get("defaults", "questions", "secondary")
			if secondary is None or len(secondary) == 0:
				messagebox.showerror("Error", "Secondary questions not found, please set default questions.")
				return
			# request survey responses and extract relevant data
			results = None
			try:
				api = self.get("api", "gateway")
				results = self.extract(api.get_survey_responses(token, survey), primary, secondary)
				rows.get_row(sid).set_info("OK")
			except Exception as e:
				rows.get_row(sid).set_error(e)
				continue
			# build up responses in model
			for primary, secondary in results.items():
				value = responses.get(primary.upper().strip(), None)
				if value is None:
					responses[primary.upper().strip()] = value = {}
				value[sid] = secondary

	def find(self, items, target, key=lambda x: x):
		result = None
		for index in range(len(items)):
			if key(items[index]) == key(target):
				result = index
				break
		return result

	def extract(self, rows, primary, secondary):
		indices = {}
		questions = [primary] + secondary
		for question in questions:
			index = self.find(rows[1], question, key=lambda x: x.strip().lower())
			if index is not None:
				indices[question] = index
		# determine if any questions are missing
		missing = set(questions) ^ set(indices)
		if len(missing) > 0:
			raise Exception("could not find questions: {}".format(missing))
		# pull responses
		result = {}
		for row in rows[3:-1]:
			current = result.get(row[indices[primary]], None)
			if current is None:
				current = []
				result[row[indices[primary]]] = current
			current.append([row[indices[i]] for i in secondary])
		return result

	def select_survey(self, sid, value=True):
		surveys = self.get("select", "surveys")
		if surveys is None:
			surveys = set()
			self.set("select", "surveys", item=surveys)
		if value:
			surveys.add(sid)
		else:
			if sid in surveys:
				surveys.remove(sid)

	def modify_defaults(self):
		ModifyDefaultsDialog(self.get("components", "root"), self)

	def export(self):
		path = filedialog.asksaveasfilename(
			parent=self.get("components", "root"),
			initialdir=os.getcwd(),
			title="Save as ...")
		if not path:
			return

		usefilter = messagebox.askyesno("Filtering", "Do you want to filter responses?")
		if usefilter is None:
			usefilter = True
		try:
			defaults = self.get("defaults", "responses", "filter", "primary", default=[])
			with open(path, 'w', newline='') as f:
				writer = csv.writer(f)
	
				selected = self.get("select", "surveys", default=[])
				surveys = sorted([self.get("surveys", sid) for sid in selected], key=lambda x: x.name)
				
				labels = [self.get("defaults", "questions", "primary")] + [survey.name for survey in surveys]
				writer.writerow(labels)
				for primary in sorted(self.get("responses")):
					if usefilter:
						# filter out unwanted primary question responses
						result = self.find(defaults, primary, key=
							lambda x:
								x.upper().strip())
						if result is not None:
							continue

					values = [primary]
					for survey in surveys:
						secondary = self.get("responses", primary, survey.id, default=[])
						result = ""
						for x in secondary:
							if len(x) > 1:
								x = ", ".join(x)
							result += str(x)
							if x != secondary[-1]:
								result += "\n"
						values.append(result)
					writer.writerow(values)
		except Exception as e:
			messagebox.showerror("Error", "Failed to export file!")
			raise e
		else:
			messagebox.showinfo("Export", "Succesfully exported file!")


	def quit(self):
		self.get("components", "root").destroy()

	def print(self):
		print(self.model.items)
