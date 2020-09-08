import re
import server_data_access

def get(filename):

	file_content = server_data_access.get(filename)

	if file_content:

		file_content = file_content.replace('\n', ' ').strip()
		file_content = re.sub(' +', ' ', file_content)

		word_list = file_content.split(' ')

		word_counter = {}

		for word in word_list:
			if word not in word_counter:
				word_counter[word] = 0
			
			word_counter[word] += 1

		word_counter_sorted_ten_first = sorted(word_counter.items(), reverse=True, key=lambda item: item[1])[:10]

		return word_counter_sorted_ten_first

	else:
		return None