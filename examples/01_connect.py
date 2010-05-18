##############################################################################
## File:  01_connect.py
##
## Copyright (C) 2009, Apache License 2.0 
## The Institute for System Programming of the Russian Academy of Sciences
## 
## This is an example application that works with Sedna XML DBMS through 
## Python API using sedna module. The application opens a session to "testdb" 
## database and closes the session.
##############################################################################

import sys
import sedna

try:
    # Connect to the testdb database which is located on localhost
    conn = sedna.SednaConnection('localhost', 'testdb')
    sys.stdout.write("Connection has been successfully established\n")

    # Close connection
    conn.close()

except sedna.SednaException as ex:
    sys.stderr.write("Failed to connect to the testdb\n")
    sys.stderr.write("%s\n" % str(ex))
