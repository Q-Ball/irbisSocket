# irbisSocket
Simple Python class to work with Irbis64 server over TCP.

Written by Nick Drozdovskiy


## Description
This simple Python class allows you to connect to the Irbis64 server and do some basic commands. This is a work in progress and is pretty buggy, USE AT YOUR OWN RISK!
List of currently working functions:
- Find records by MFN or by a special search query;
- Output records in json, unifor or txt formats;
- Add, edit or remove specific fields.
It has been tested with Python 3.5 and has no dependencies beyond the standard Python libraries.


## Usage

`from irbis_socket import irbisSocket`: Add to the project

`irbisSocket = irbisSocket(serverHost, serverPort, userName, userPassword)`: Establish connection to the irbis server
Required parameters:
- _serverHost_: server hostname (string)
- _serverPort_: server port (integer)
- _userName_: username (string)
- _userPassword_: password (string)

`records = irbisSocket.searchRecords(dbName, query, format)`: Return a list of records in the specified format
Required parameters:
- _dbName_: database name (string)
- _query_: search query in the irbis format (string)
- _format_: output format (string), accepted values - "json", "unifor"

`record = irbisSocket.readRecord(dbName, mfn, format)`: Return a record found by MFN number
Required parameters:
- _dbName_: database name (string)
- _mfn_: mfn number of the specific irbis record (string)
- _format_: output format (string), accepted values - "json", "unifor"

`txt = irbisSocket.irbis2txt(record)`: Convert unifor record into plain TXT format
Required parameters:
- _record_: record obtained from searchRecords or readRecord

`irbisSocket.addField(dbName, mfn, field, subfield, content)`: Add a field/subfield at the end of the record
Required parameters:
- _dbName_: database name (string)
- _mfn_: mfn number of the specific irbis record (string)
- _field_: field number (string)
- _subfield_: subfield number, leave empty if field has no subfields (string)
- _content_: field/subfield contents (string)

`irbisSocket.editField(dbName, mfn, field, occurence, subfield, content)`: Edit specified occurence of the field/subfield in the record
Required parameters:
- _dbName_: database name (string)
- _mfn_: mfn number of the specific irbis record (string)
- _field_: field number (string)
- _occurence_: field occurence (integer/string), use integers starting from 0 to specify the field number, use character "L" to specify the last field
- _subfield_: subfield number, leave empty if want to edit entire field and not just subfield (string)
- _content_: field/subfield contents (string)

`irbisSocket.removeField(dbName, mfn, field, occurence, subfield)`: Remove specified occurence of the field/subfield in the record
Required parameters:
- _dbName_: database name (string)
- _mfn_: mfn number of the specific irbis record (string)
- _field_: field number (string)
- _occurence_: field occurence (integer/string), use integers starting from 0 to specify the field number, use character "L" to specify the last field
- _subfield_: subfield number, leave empty if want to remove entire field and not just subfield (string)

`irbisSocket.addRecord(dbName, record, format)`: Add new record to the database
Required parameters:
- _dbName_: database name (string)
- _record_: record in unifor or json formats (string) - uses the structure returned by readRecord/searchRecords functions
- _format_: output format (string), accepted values - "json", "unifor"

`irbisSocket.editRecord(dbName, mfn, record, format)`: Edit entire record in the database
Required parameters:
- _dbName_: database name (string)
- _mfn_: mfn number of the specific irbis record (string)
- _record_: record in unifor or json formats (string) - uses the structure returned by readRecord/searchRecords functions
- _format_: output format (string), accepted values - "json", "unifor"

`mfn = irbisSocket.maxMFN(dbName)`: Get the number of last MFN in the database
Required parameters:
- _dbName_: database name (string)

`irbisSocket.disconnect()`: Disconnect from the Irbis server


## Example
	from irbis_socket import irbisSocket
  
	irbisSocket = irbisSocket("127.0.0.1", 6666, "username", "password")
  
	records = irbisSocket.searchRecords("DATABASE", "v463^J='2018'", "json")
	record = irbisSocket.readRecord("DATABASE", "86165", "unifor")
	irbisSocket.addField("DATABASE", "86165", "907", "", "^A20180227^BExportBot")
	irbisSocket.editField("DATABASE", "86165", "907", 0, "B", "NewUserName")
	irbisSocket.removeField("DATABASE", "86165", "910", "L", "")
  
	irbisSocket.disconnect()
	
