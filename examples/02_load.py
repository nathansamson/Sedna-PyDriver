##############################################################################
## File:  02_load.py
##
## Copyright (C) 2009, Apache License 2.0 
## The Institute for System Programming of the Russian Academy of Sciences
## 
## This is an example application that works with Sedna XML DBMS through 
## Python API using sedna module. The application opens a session to "testdb" 
## database, loads document "categories.xml" as a standalone document.
##############################################################################

import sys
import sedna

conn = None

try:
    # Connect to the testdb database which is located on localhost
    conn = sedna.SednaConnection('localhost', 'testdb')
    sys.stdout.write("Connection has been successfully established\n")

    # Transaction must be started before executing a query
    conn.beginTransaction()
    
    # Load document "categories.xml" into database 'testdb'
    cat = file('data/categories.xml', 'rb')
    conn.loadDocument(cat, 'categories')
    cat.close()
    sys.stdout.write("File 'categories.xml' has been successfully loaded\n")
    
    # Commit transaction after executing a query
    conn.endTransaction('commit')
    
except sedna.SednaException as ex:
    sys.stderr.write("Something went wrong while executing\n")
    sys.stderr.write("%s\n" % str(ex))


try:
    # Check connection status and close it
    if conn != None and conn.status() == 'ok':
        conn.close()
except sedna.SednaException as ex:
    sys.stderr.write("Cannot close connection\n")
    sys.stderr.write("%s\n" % str(ex))
