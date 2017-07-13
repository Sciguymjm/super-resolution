# input file name
filename = "latlon.bin"
# Start position to read from the file (x,y)
from_position = [10, 12]
# End position in (x,y). All the contents between these coordinates will be read.
to_position = [20, 50]

# Some info to user
rows_to_read = to_position[0] - from_position[0]
cols_to_read = to_position[1] - from_position[1] + 1
print("Going to read", rows_to_read, "rows","and",cols_to_read,"columns from file",filename)

print("------------ Contents ------------")
# Openbinary file to read
with open(filename, "rb") as binary_file:
	# Start loop for reading specific rows. This will read only rows that falls
	# in above mentioned positions.
	for row in range(from_position[0], to_position[0]+1):
		# Set the reading head to specific row. We are not reading the whole file.
		binary_file.seek(row)
		# Extract the required content from the line
		content = binary_file.read()[from_position[1]:to_position[1]+1]
		# Print or store as per your need.
		print(content)

print("----------------------------------")
# Close the file.
binary_file.close()
# End of the code