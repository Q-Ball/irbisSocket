import socket
import re
import uuid
import time
import json

counter = 1
userID = str(uuid.uuid1().int).replace("0","")[0:6]

# Main class
class irbisSocket:
	def __init__(self, serverHost, serverPort, userName, userPassword):
		self.connect = connect_irbis(self, serverHost, serverPort, userName, userPassword)
		self.serverInfo = {"serverHost":serverHost,"serverPort":serverPort,"userName":userName,"userPassword":userPassword}
	def disconnect(self):
		return disconnect_irbis(self.serverInfo)
	def searchRecords(self, dbName, query, format):
		return search_records_irbis(self.serverInfo, dbName, query, format)
	def readRecord(self, dbName, mfn, format):
		return read_record_irbis(self.serverInfo, dbName, mfn, format)
	def addField(self, dbName, mfn, field, subfield, content):
		return add_field_irbis(self.serverInfo, dbName, mfn, field, subfield, content)
	def editField(self, dbName, mfn, field, iteration, subfield, content):
		return edit_field_irbis(self.serverInfo, dbName, mfn, field, iteration, subfield, content)
	def removeField(self, dbName, mfn, field, iteration, subfield):
		return remove_field_irbis(self.serverInfo, dbName, mfn, field, iteration, subfield)
	def maxMFN(self, dbName):
		return get_max_mfn(self.serverInfo, dbName)
	def irbis2txt(self, record):
		return irbis2txt(record)

# Get all data from socket
def recvall(socket):
	data = b""
	while True:
		buf = socket.recv(64000)
		if (len(buf) == 0): break
		data += buf	
	return data

# Get record data in unifor
def get_record_unifor(serverInfo, dbName, query):
	try:
		global counter
		global userID
		counter += 1
		serverHost = serverInfo["serverHost"]
		serverPort = serverInfo["serverPort"]
		userName = serverInfo["userName"]
		userPassword = serverInfo["userPassword"]
		
		message_body = "\nK\nC\nK\n" + userID + "\n" + str(counter) + "\n" + userPassword + "\n" + userName + "\n\n\n\n" + dbName + "\n\n10000\n1\nmpl, &unifor('+0') \n0\n0\n!if " + query + " then '1' else '0' fi"
		message = str(len(message_body) - 1) + message_body # message = message_size + message_body

		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((serverHost, serverPort))
		s.send(message.encode("cp1251","ignore"))
		data = recvall(s)
		s.close()
		return data
		#result = re.search(r'[0-9A-Z_]\r\n[0-9]*?\r\n[0-9]*?\r\n[0-9]*?\r\n\r\n\r\n\r\n\r\n\r\n\r\n(.*?)\r\n[0-9]*?\r\n(.*?)\r\n', data.decode("cp1251","ignore"), re.MULTILINE)
		#return result
	except ValueError as ex:
		print("# ERROR: Exception occured while getting record data in Unifor")
		print(ex)


def send_message(serverInfo, message):
	try:
		serverHost = serverInfo["serverHost"]
		serverPort = serverInfo["serverPort"]
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((serverHost, serverPort))
		s.send(message.encode("cp1251","ignore"))
		data = recvall(s)
		#data = s.recvfrom(64000)
		s.close()
		return data
	except ValueError as ex:
		print("# ERROR: Exception occured while sending message to Irbis server")
		print(ex)

# Send record to Irbis server
def send_record(serverInfo, dbName, block_record, actualize_record, temp):
	try:
		global counter
		global userID
		counter += 1
		userName = serverInfo["userName"]
		userPassword = serverInfo["userPassword"]
		
		message_body = "\nD\nC\nD\n" + userID + "\n" + str(counter) + "\n" + userPassword + "\n" + userName + "\n\n\n\n" + dbName + "\n" + block_record + "\n" + actualize_record + "\n" + temp
		message = str(len(message_body) - 1) + message_body # message = message_size + message_body
		
		data = send_message(serverInfo, message)
		result = re.search(r'[0-9A-Z_]\r\n[0-9]*?\r\n[0-9]*?\r\n[0-9]*?\r\n\r\n\r\n\r\n\r\n\r\n\r\n(.*?)\r\n', data.decode("cp1251","ignore"), re.MULTILINE)
		return result.group(1).strip()
	except ValueError as ex:
		print("# ERROR: Exception occured while sending record data in Unifor")
		print(ex)

# Get max mfn
def get_max_mfn(serverInfo, dbName):
	try:
		serverHost = serverInfo["serverHost"]
		serverPort = serverInfo["serverPort"]
		message_body = "\nO\nC\nO\n" + userID +"\n" + str(counter) + "\n\n\n\n\n\n" + dbName + "\n"
		message = str(len(message_body) - 1) + message_body
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((serverHost, serverPort))
		s.send(message.encode())
		data = recvall(s)
		s.close()
		result = re.search(r'[0-9A-Z_]\r\n[0-9]*?\r\n[0-9]*?\r\n[0-9]*?\r\n\r\n\r\n\r\n\r\n\r\n\r\n(.*?)\r\n', data.decode("utf-8"), re.MULTILINE)
		status = result.group(1).strip()
		if ("-" not in status):
			return status
		else:
			print("# ERROR: Encountered error while reading Irbis records (Error code: " + status +")")
			return 0
	except ValueError as ex:
		print("# ERROR: Exception occured while getting max MFN:")
		print(ex)

# Convert Irbis format to JSON
def irbis2json(record):
	record = re.search(r'([0-9]*?)#(.*?)$', record, re.MULTILINE)
	mfn = record.group(1).strip()
	fields = {}
	rows = record.group(2).strip().split("\x1f")
	del rows[:3] # Remove first 3 rows - useless data
	for row in rows:
		temp = re.search(r'^([0-9]*?)#(.*?)$', row)
		#num = "0"
		if temp.group(1).strip() in fields:
			num = str(len(fields[temp.group(1).strip()]))
		else:
			num = "0"
			fields[temp.group(1).strip()] = {}
		subfields = {}
		for (code, data, dummy) in re.findall(r'(?<=\^)([A-Za-z0-9]{1})(.*?)(\^|$)', temp.group(2).strip(), re.DOTALL):
			subfields[code] = data
		if (len(subfields)>0):
			fields[temp.group(1).strip()][num] = subfields
		else:
			fields[temp.group(1).strip()][num] = temp.group(2).strip()
	return '{ "' + mfn + '": ' + json.dumps(fields, ensure_ascii=False) + ' }'

# Convert Irbis format to TXT
def irbis2txt(record):
	rows = record.split("\x1f")
	del rows[:3] # Remove first 3 rows - useless data
	temp = []
	for row in rows: temp.append(re.sub(r'^([0-9]*?)#(.*?)$', r'#\1: \2', row))
	record = '\n'.join(temp)
	return record + "*****\n"

# Connect
def connect_irbis(self, serverHost, serverPort, userName, userPassword):
	try:
		global counter
		global userID
		message_body = "\nA\nC\nA\n" + userID +"\n" + str(counter) + "\n" + userPassword + "\n" + userName + "\n\n\n\n" + userName + "\n" + userPassword
		message = str(len(message_body) - 1) + message_body # message = message_size + message_body
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((serverHost, serverPort))
		s.send(message.encode())
		data = s.recvfrom(64000)
		s.close()

		result = re.search(r'.{1}\r\n[0-9a-zA-Z]*?\r\n[0-9]*?\r\n[0-9]*?\r\n[0-9.]*?\r\n\r\n\r\n\r\n\r\n\r\n(.*?)\r\n', data[0].decode("cp1251","ignore"), re.MULTILINE).group(1).strip()
		if (result == '0'):
			counter += 1
			#print("# Connected")
			return self
		else:
			print("# ERROR: Couldn't connect to Irbis server (Error code: " + result +")")
	except ValueError as ex:
		print("# ERROR: Exception occured while getting max MFN:")
		print(ex)

# Search
def search_records_irbis(serverInfo, dbName, query, format):
	try:
		global counter


















		data = get_record_unifor(serverInfo, dbName, query)
		result = re.search(r'[0-9A-Z_]\r\n[0-9]*?\r\n[0-9]*?\r\n[0-9]*?\r\n\r\n\r\n\r\n\r\n\r\n\r\n(.*?)\r\n', data.decode("cp1251","ignore"), re.MULTILINE)
		status = result.group(1).strip()
		if (status == '0'):
			records = []

			for record in data.decode("utf-8","ignore").split("\r\n"): # quick-fix to get data from irbis' answer
				if re.search(r'^[0-9]*?#(.*?)$', record):

					if (format == "json"):
						records.append(irbis2json(record))
					else:
						records.append(record)


			counter += 1
			return records

		else:
			print("# ERROR: Encountered error while reading Irbis records (Error code: " + status +")")
	except ValueError as ex:
		print("# ERROR: Exception occured while reading Irbis records: ")
		print(ex)

# Get specific record by mfn
def read_record_irbis(serverInfo, dbName, mfn, format):
	try:
		global counter


















		data = get_record_unifor(serverInfo, dbName, "mfn="+mfn)
		result = re.search(r'[0-9A-Z_]\r\n[0-9]*?\r\n[0-9]*?\r\n[0-9]*?\r\n\r\n\r\n\r\n\r\n\r\n\r\n(.*?)\r\n', data.decode("cp1251","ignore"), re.MULTILINE)
		status = result.group(1).strip()
		if (status == '0'):
			records = []

			for record in data.decode("utf-8","ignore").split("\r\n"): # quick-fix to get data from irbis' answer
				if re.search(r'^[0-9]*?#(.*?)$', record):

					if (format == "json"):
						records.append(irbis2json(record))
					else:
						records.append(record)

			counter += 1
			return records

		else:
			print("# ERROR: Encountered error while reading Irbis records (Error code: " + status +")")
	except ValueError as ex:
		print("# ERROR: Exception occured while reading Irbis records: ")
		print(ex)

# Add field to the specific record
def add_field_irbis(serverInfo, dbName, mfn, field, subfield, content):
	try:






		block_record = "0"
		actualize_record = "1"




		# Get record before modification



		data = get_record_unifor(serverInfo, dbName, "mfn="+mfn)
		result = re.search(r'[0-9A-Z_]\r\n[0-9]*?\r\n[0-9]*?\r\n[0-9]*?\r\n\r\n\r\n\r\n\r\n\r\n\r\n(.*?)\r\n[0-9]*?\r\n(.*?)\r\n', data.decode("cp1251","ignore"), re.MULTILINE)
		
		# Add new field
		temp = re.sub(r'(^[0-9]*?)#[0-9]*?\x1f(.*?)', r'\2', result.group(2).strip()) + '\x1f' + field + '#' + ('^' if subfield != '' else '') + content.encode("utf-8","ignore").decode("cp1251","ignore") +  "\n"

		# Send record to Irbis server











		status = send_record(serverInfo, dbName, block_record, actualize_record, temp)
		if ("-" in status):
		#if ("-" not in status):
		#	print("# Record successfully saved!")
		#else:
			print("# ERROR: Encountered error while reading Irbis records (Error code: " + status +")")
	except ValueError as ex:
		print("# ERROR: Exception occured while reading Irbis records: ")
		print(ex)

# Edit field of the specific record
def edit_field_irbis(serverInfo, dbName, mfn, field, iteration, subfield, content):
	try:






		block_record = "0"
		actualize_record = "1"
		content = content.encode("utf-8","ignore").decode("cp1251","ignore")




		# Get record before modification



		data = get_record_unifor(serverInfo, dbName, "mfn="+mfn)
		result = re.search(r'[0-9A-Z_]\r\n[0-9]*?\r\n[0-9]*?\r\n[0-9]*?\r\n\r\n\r\n\r\n\r\n\r\n\r\n(.*?)\r\n[0-9]*?\r\n(.*?)\r\n', data.decode("cp1251","ignore"), re.MULTILINE)
		
		# Edit field
		temp = re.sub(r'(^[0-9]*?)#[0-9]*?\x1f(.*?)', r'\2', result.group(2).strip()) # remove useless rows

		field_iterations = re.findall(field + r'#(.*?)(\x1f|$)', temp, re.DOTALL)
		if (str(iteration) == "L"): iteration = len(field_iterations)-1 # get last occurence
		field_iteration = field_iterations[iteration] # find specific field occurence
		replaced_subfield = ''



		if (subfield == ''):
			replaced_subfield = content
		else:
			if ('^'+subfield in field_iteration[0]):
				replaced_subfield = re.sub(r'(?<=\^)' + subfield + '(.*?)(\^|\x1f|$)', subfield + content + r'\2', field_iteration[0])
			elif ('^' in field_iteration[0]):
				replaced_subfield = field_iteration[0] + '^' + subfield + content
			else:
				replaced_subfield = content
		temp = temp.replace(field_iteration[0], replaced_subfield)

		# Send record to Irbis server











		status = send_record(serverInfo, dbName, block_record, actualize_record, temp)
		if ("-" in status):
		#if ("-" not in status):
		#	print("# Record successfully saved!")
		#else:
			print("# ERROR: Encountered error while reading Irbis records (Error code: " + status +")")
	except ValueError as ex:
		print("# ERROR: Exception occured while reading Irbis records: ")
		print(ex)

# Remove field of the specific record
def remove_field_irbis(serverInfo, dbName, mfn, field, iteration, subfield):
	try:






		block_record = "0"
		actualize_record = "1"




		# Get record before modification



		data = get_record_unifor(serverInfo, dbName, "mfn="+mfn)
		result = re.search(r'[0-9A-Z_]\r\n[0-9]*?\r\n[0-9]*?\r\n[0-9]*?\r\n\r\n\r\n\r\n\r\n\r\n\r\n(.*?)\r\n[0-9]*?\r\n(.*?)\r\n', data.decode("cp1251","ignore"), re.MULTILINE)
		
		# Remove field/subfield
		temp = re.sub(r'(^[0-9]*?)#[0-9]*?\x1f(.*?)', r'\2', result.group(2).strip()) # remove useless rows
		field_iterations = re.findall(field + r'#(.*?)(\x1f|$)', temp, re.DOTALL)
		if (str(iteration) == "L"): iteration = len(field_iterations)-1 # get last occurence
		field_iteration = field_iterations[iteration] # find specific field occurence

		if (subfield == ''):
			temp = temp.replace("\x1f"+field+"#"+field_iteration[0], '')
		else:
			replaced_subfield = ''
			if ('^' in field_iteration[0]):
				replaced_subfield = re.sub(r'(?<=\^)' + subfield + '(.*?)(\^|\x1f|$)', '', field_iteration[0])
			temp = temp.replace(field_iteration[0], replaced_subfield)

		# Send record to Irbis server











		status = send_record(serverInfo, dbName, block_record, actualize_record, temp)
		if ("-" in status):
		#if ("-" not in status):
		#	print("# Record successfully saved!")
		#else:
			print("# ERROR: Encountered error while reading Irbis records (Error code: " + status +")")
	except ValueError as ex:
		print("# ERROR: Exception occured while reading Irbis records: ")
		print(ex)

# Disconnect
def disconnect_irbis(serverInfo):
	global counter
	global userID
	serverHost = serverInfo["serverHost"]
	serverPort = serverInfo["serverPort"]
	userName = serverInfo["userName"]
	userPassword = serverInfo["userPassword"]
	message_body = "\nB\nC\nB\n" + userID + "\n" + str(counter) + "\n" + userPassword + "\n" + userName + "\n\n\n\n" + userName + "\n" + userPassword
	message = str(len(message_body) - 1) + message_body # message = message_size + message_body
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((serverHost, serverPort))
	s.send(message.encode())
	data = s.recvfrom(64000)
	s.close()

	result = re.search(r'.{1}\r\n[0-9a-zA-Z]*?\r\n[0-9]*?\r\n[0-9]*?\r\n\r\n\r\n\r\n\r\n\r\n\r\n(.*?)\r\n', data[0].decode("cp1251","ignore"), re.MULTILINE).group(1).strip()
	if (result != '0'):
	#if (result == '0'):
	#	print("# Disconnected")
	#else:
		print("# ERROR: Couldn't disconnect from Irbis server (Error code: " + result +")")
