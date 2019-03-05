import tkinter as     tk
from   tkinter import messagebox, simpledialog, filedialog
import json

class Top(tk.Frame):
	def __init__(self, master=None, controller=None):
		super().__init__(master)
		self.master = master
		self.controller = controller
		self.create_widgets()

	def create_widgets(self):
		self.rowconfigure(0, weight=1)
		self.columnconfigure(0, weight=1)

		self.menu = MainMenu(self, self.controller)
		self.master.config(menu=self.menu)

		self.body = ScrollableFrame(self)
		self.body.grid(sticky="nsew")
		self.rows = None

class MainMenu(tk.Menu):
	def __init__(self, master=None, controller=None):
		super().__init__(master)
		self.master = master
		self.controller = controller
		self.create_widgets()
	
	def create_widgets(self):
		self.add(tk.CASCADE, label="File", menu=self.FileMenu(self, self.controller))
		self.add(tk.CASCADE, label="Qualtrics", menu=self.QualtricsMenu(self, self.controller))

	class FileMenu(tk.Menu):
		def __init__(self, master=None, controller=None):
			super().__init__(master, tearoff=0)
			self.master = master
			self.controller = controller
			self.create_widgets()

		def create_widgets(self):
			self.add(tk.COMMAND, label="Export", command=self.controller.export)
			self.add(tk.SEPARATOR)
			self.add(tk.COMMAND, label="Debug", command=self.controller.print)
			self.add(tk.COMMAND, label="Quit", command=self.controller.quit)
	
	class QualtricsMenu(tk.Menu):
		def __init__(self, master=None, controller=None):
			super().__init__(master, tearoff=0)
			self.master = master
			self.controller = controller
			self.create_widgets()

		def create_widgets(self):
			self.add(tk.COMMAND, label="API Token", command=self.controller.populate_api_token)
			self.add(tk.SEPARATOR)
			self.add(tk.COMMAND, label="Modify Defaults", command=self.controller.modify_defaults)
			self.add(tk.SEPARATOR)
			self.add(tk.CASCADE, label="Surveys", menu=self.SurveysMenu(self, self.controller))
			#self.add(tk.CASCADE, label="Questions", menu=self.QuestionsMenu(self, self.controller))
			self.add(tk.CASCADE, label="Responses", menu=self.ResponsesMenu(self, self.controller))

		class SurveysMenu(tk.Menu):
			def __init__(self, master=None, controller=None):
				super().__init__(master, tearoff=0)
				self.master = master
				self.controller = controller
				self.create_widgets()

			def create_widgets(self):
				self.add(tk.COMMAND, label="Populate", command=self.controller.populate_surveys)
				self.select = tk.Menu(self, tearoff=0)
				self.select.add(tk.COMMAND, label="All", command=self.select_all)
				self.select.add(tk.COMMAND, label="None", command=self.select_none)
				self.add(tk.CASCADE, label="Select", menu=self.select)

			def select_all(self):
				rows = self.controller.get("components", "top").rows
				rows.select_all()

			def select_none(self):
				rows = self.controller.get("components", "top").rows
				rows.select_none()

		class QuestionsMenu(tk.Menu):
			def __init__(self, master=None, controller=None):
				super().__init__(master, tearoff=0)
				self.master = master
				self.controller = controller
				self.create_widgets()
		
			def create_widgets(self):
				self.add(tk.COMMAND, label="Populate", command=self.controller.populate_questions)

		class ResponsesMenu(tk.Menu):
			def __init__(self, master=None, controller=None):
				super().__init__(master, tearoff=0)
				self.master = master
				self.controller = controller
				self.create_widgets()
		
			def create_widgets(self):
				self.add(tk.COMMAND, label="Populate", command=self.controller.populate_responses)
		
class SurveyRows(tk.Frame):
	def __init__(self, master=None, controller=None):
		super().__init__(master)
		self.master = master
		self.controller = controller
		self.grid()
		self.create_widgets()
	
	def create_widgets(self):
		self.rows = {}
		surveys = self.controller.get("surveys", default={})
		for sid in sorted(surveys, key=lambda sid: surveys[sid].name):
			row = self.SurveyRow(self, self.controller, sid)
			row.grid(row=len(self.rows), sticky=tk.W)
			self.rows[sid] = row

	def get_row(self, sid):
		return self.rows[sid]

	def select_all(self):
		for row in self.rows.values():
			row.check.select()
	
	def select_none(self):
		for row in self.rows.values():
			row.check.deselect()
	
	class SurveyRow(tk.Frame):
		def __init__(self, master=None, controller=None, sid=None):
			super().__init__(master)
			self.master = master
			self.controller = controller
			self.sid = sid
			self.create_widgets()

		def create_widgets(self):
			defaults = self.controller.get("defaults", "surveys", default=[])
			# get survey from model
			survey = self.controller.get("surveys", self.sid)
			if not survey:
				return
			# create variable to track check button
			self.check_variable = tk.IntVar()
			self.check_variable.trace(tk.W, 
				lambda *args: 
					self.controller.select_survey(self.sid, value=self.check_variable.get()))
			# create check button
			self.check = tk.Checkbutton(self, 
				variable=self.check_variable, 
				text=survey.name,
				anchor=tk.W,
				width=60)

			if len(defaults) > 0:
				result = self.controller.find(defaults, survey.name, key=
					lambda x:
						x.lower().strip())
				if result is not None:
					self.check.select()
			else:
				self.check.select()

			self.check.grid(row=0, column=0, sticky=tk.W)
			# create questions button
			#self.button = tk.Button(self, text="Questions", command=None)
			#self.button.grid(row=0, column=1)
			self.info_variable = tk.StringVar()
			self.info = tk.Label(self, textvariable=self.info_variable)
			self.info.grid(row=0, column=1)

		def set_error(self, text):
			self.info_variable.set(text)
			self.info.config(fg="red")

		def set_info(self, text):
			self.info_variable.set(text)
			self.info.config(fg="green")
			
		def destroy(self):
			self.controller.select_survey(self.sid, value=False)
			super().destroy()

		def create_questions_command(self, index, survey):
			def f():
				if not survey.questions:
					survey.questions = qt.get_survey_questions(self.master.master.master.master.api_token, self.rows[index][0][1].id)
				questions_dialog = QuestionsDialog(self, title="Select Questions", questions=survey.questions)
				self.rows[index][1] = (questions_dialog.get_selected(), self.rows[index][1][1])
			return f

class QuestionsDialog(simpledialog.Dialog):
	def __init__(self, master=None, controller=None, sid=None):
		self.master = master
		self.controller = controller
		self.sid = sid
		super().__init__(master, title="Questions")

	def body(self, master):
		# TODO: questions = self.controller.get("questions", self.sid)

		survey = self.model.get("surveys", {}).get(self.sid, None)
		if not survey:
			return
		if not survey.questions:
			try:
				self.controller.populate("questions", self.sid)
			except Exception as e:
				messagebox.showerror("Error", e)
				raise e
		
		self.primary = tk.Listbox(master, selectmode=tk.SINGLE, exportselection=0)
		self.primary.insert(0, *survey.questions)
		self.primary.pack(side=tk.LEFT)

		self.secondary = tk.Listbox(master, selectmode=tk.MULTIPLE, exportselection=0)
		self.secondary.insert(0, *survey.questions)
		self.secondary.pack(tk.RIGHT)

	def apply(self):
		self.controller.select("questions", 
			sid=self.sid, 
			primary=self.primary.curselection, 
			secondary=self.secondary.curselection())

class APITokenDialog(simpledialog.Dialog):
	def __init__(self, master=None, controller=None):
		self.master = master
		self.controller = controller
		super().__init__(master, title="Qualtrics API Token")

	def body(self, master):
		self.label = tk.Label(self, text="Please enter your Qualtrics API Token")
		self.label.pack()

		self.variable = tk.StringVar()
		self.variable.set(self.controller.get("api", "token", default=""))
		self.entry = tk.Entry(self, textvariable=self.variable)
		self.entry.pack()

	def apply(self):
		self.controller.set("api", "token", item=self.variable.get())

class ModifyDefaultsDialog(simpledialog.Dialog):
	def __init__(self, master=None, controller=None):
		self.master = master
		self.controller = controller
		super().__init__(master, title="Defaults")
	
	def body(self, master):
		self.container = tk.Frame(self)
		self.container.pack()

		self.surveys = LabeledListbox(self.container, self.controller, "Surveys")
		self.surveys.listbox.listbox.config(selectmode=tk.SINGLE, exportselect=0)
		index = 0
		for survey in self.controller.get("defaults", "surveys", default=[]):
			self.surveys.listbox.listbox.insert(index, survey)
			index += 1
		self.surveys.grid(row=0, column=0, sticky="nsew")

		self.primary_container = tk.Frame(self.container)
		self.primary_container.grid(row=0, column=1)

		self.primary = LabeledEntry(self.primary_container, self.controller, "Primary Question")
		self.primary.variable.set(self.controller.get("defaults", "questions", "primary", default=""))
		self.primary.grid(row=0, column=0, sticky="nwe")

		self.response_filters = LabeledListbox(self.primary_container, self.controller, "Response Filters")
		self.response_filters.listbox.listbox.config(selectmode=tk.SINGLE, exportselect=0)
		index = 0
		for response_filter in self.controller.get("defaults", "responses", "filter", "primary", default=[]):
			self.response_filters.listbox.listbox.insert(index, response_filter)
			index += 1
		self.response_filters.grid(row=1, column=0, sticky="nsew")

		self.secondary = LabeledListbox(self.container, self.controller, "Secondary Questions")
		self.secondary.listbox.listbox.config(selectmode=tk.SINGLE, exportselect=0)
		index = 0
		for question in self.controller.get("defaults", "questions", "secondary", default=[]):
			self.secondary.listbox.listbox.insert(index, question)
			index += 1
		self.secondary.grid(row=0, column=2, sticky="nsew")

	def apply(self):
		self.controller.set("defaults", "surveys", item=list(self.surveys.listbox.listbox.get(0, tk.END)))
		self.controller.set("defaults", "questions", "primary", item=self.primary.variable.get())
		self.controller.set("defaults", "questions", "secondary", item=list(self.secondary.listbox.listbox.get(0, tk.END)))
		self.controller.set("defaults", "responses", "filter", "primary", item=list(self.response_filters.listbox.listbox.get(0, tk.END)))
		
		retry = True
		while retry:
			try:
				with open("defaults.json", "w") as f:
					f.write(json.dumps(self.controller.get("defaults", default={}), indent=2))
				retry = False
			except Exception as e:
				retry = messagebox.askretrycancel(
					"Error", 
					"An error prevented default settings from being saved. Do you want to try again?")
				if not retry:
					raise e


class LabeledEntry(tk.LabelFrame):
	def __init__(self, master=None, controller=None, text=""):
		super().__init__(master, text=text)
		self.master = master
		self.controller = controller
		self.text = text
		self.create_widgets()
	
	def create_widgets(self):
		self.variable = tk.StringVar()
		self.entry = tk.Entry(self, textvariable=self.variable)
		self.entry.pack()

class LabeledListbox(tk.LabelFrame):
	def __init__(self, master=None, controller=None, text=""):
		super().__init__(master, text=text)
		self.master = master
		self.controller = controller
		self.text = text
		self.create_widgets()
	
	def create_widgets(self):
		self.listbox = EditableListbox(self, self.controller)
		self.listbox.pack(fill=tk.BOTH, expand=True)


class EditableListbox(tk.Frame):
	def __init__(self, master=None, controller=None):
		super().__init__(master)
		self.master = master
		self.controller = controller
		self.create_widgets()

	def create_widgets(self):
		self.listbox = tk.Listbox(self)
		self.listbox.pack(fill=tk.BOTH, expand=True)

		self.edit = tk.Button(self, text="Edit", command=self.edit_item)
		self.edit.pack(side=tk.LEFT)
		self.add = tk.Button(self, text="Add", command=self.add_item)
		self.add.pack(side=tk.LEFT)
		self.remove = tk.Button(self, text="Remove", command=self.remove_item)
		self.remove.pack(side=tk.LEFT)

	def edit_item(self):
		selection = self.listbox.curselection()
		if not selection:
			return
		value = self.listbox.get(selection[0])
		answer = simpledialog.askstring("Edit", "",
			initialvalue=value,
			parent=self.controller.get("components", "root"))
		if not answer:
			return
		self.listbox.delete(selection[0])
		self.listbox.insert(selection[0], answer)

	def add_item(self):
		index = tk.END
		selection = self.listbox.curselection()
		if selection:
			index = selection[0] + 1
		answer = simpledialog.askstring("Add", "",
			parent=self.controller.get("components", "root"))
		self.listbox.insert(index, answer)
	
	def remove_item(self):
		selection = self.listbox.curselection()
		if not selection:
			return
		self.listbox.delete(selection[0])	

class ScrollableFrame(tk.Frame):
	def __init__(self, master=None, controller=None):
		super().__init__(master)
		self.master = master
		self.controller = controller
		self.create_widgets()

	def create_widgets(self):
		self.yscrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)	
		self.yscrollbar.grid(row=0, column=0, sticky="nsew")

		self.xscrollbar = tk.Scrollbar(self, orient=tk.HORIZONTAL)
		self.xscrollbar.grid(row=1, column=1, sticky="nsew")

		self.canvas = tk.Canvas(self,
			xscrollcommand=self.xscrollbar.set,
			yscrollcommand=self.yscrollbar.set)	
		self.canvas.grid(row=0, column=1, sticky="nsew")

		self.xscrollbar.config(command=self.canvas.xview)
		self.yscrollbar.config(command=self.canvas.yview)

		tk.Grid.rowconfigure(self, 0, weight=1)
		tk.Grid.columnconfigure(self, 1, weight=1)
			
		self.interior = tk.Frame(self.canvas)
		self.interior_id = self.canvas.create_window(0, 0, window=self.interior, anchor=tk.NW)

		self.interior.bind("<Configure>", lambda event: 
			self.canvas.config(scrollregion=(0, 0, 
				self.interior.winfo_reqwidth(), 
				self.interior.winfo_reqheight())))	
