import os.path as path

database_path = path.join(path.dirname(path.abspath(__file__)), 'db')

def get(filename):

	file_path = path.join(database_path, filename)

	if not path.isfile(file_path):
		return None

	else:
		file_content = open(file_path, 'r')
		return file_content.read()
