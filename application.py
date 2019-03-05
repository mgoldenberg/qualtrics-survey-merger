import tkinter    as     tk
import traceback  as     tb
from   tkinter    import messagebox
from   components import *
from   controller import Controller
from   qualtrics  import Qualtrics
from   model      import Model


def main():
	tk.Tk.report_callback_exception = show_error
	root = tk.Tk()
	root.rowconfigure(0, weight=1)
	root.columnconfigure(0, weight=1)

	defaults, error = read_defaults()
	if error:
		messagebox.showwarning("Warning", "Error reading default settings")	

	controller = Controller()
	controller.set("components", "root", item=root)
	controller.set("defaults", item=defaults)
	controller.set("api", "gateway", item=Qualtrics())

	top = Top(master=root, controller=controller)
	top.grid(sticky="nsew")
	controller.set("components", "top", item=top)

	root.mainloop()

def show_error(self, *args):
	lines = tb.format_exception(*args)
	text = ''.join(lines)
	print(text)
	messagebox.showerror("Error", text)	

def read_defaults():
	error = None
	result = {}
	try:
		with open("defaults.json", "r") as f:
			 result = json.loads(f.read())
	except FileNotFoundError:
		pass
	except Exception as e:
		error = e
	return (result, error)

if __name__ == "__main__":
	main()
