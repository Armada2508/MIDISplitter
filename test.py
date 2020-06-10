
example_list = [1, 2, 3, [2, 3], [3, [6, 3]]]

def highest_dimension(l):
	dimensions = []
	for e in l:
		if(isinstance(e, list)):
			dimensions.append(highest_dimension(e))
	if(len(dimensions) == 0):
		return 1
	else:
		return max(dimensions) + 1

print(highest_dimension(example_list))