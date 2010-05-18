##############################################################################
## File:  03_load_coll.py
##
## Copyright (C) 2009, Apache License 2.0 
## The Institute for System Programming of the Russian Academy of Sciences
## 
## This is an example application that works with Sedna XML DBMS through 
## Python API using sedna module. The application opens a session to "testdb" 
## database, loads all the documents from the file system directory into 
## a collection "wikidb".
##############################################################################

import sys
import sedna
import os

conn = None

try:
    # Connect to the testdb database which is located on localhost
    conn = sedna.SednaConnection('localhost', 'testdb')
    sys.stdout.write("Connection has been successfully established\n")

    # Transaction must be started before executing a query
    conn.beginTransaction()
    
    # Create collection "wikidb"
    conn.execute("create collection 'wikidb'")
    sys.stdout.write("Collection has been created successfully\n")
    
    # We have a set of documents (page*.xml) with similar structure -
    # load them into a collection to save space!
    # In real application you can load unlimited number of documents
    # into a single collection (we tried 500 000+).
    counter = 0;
    for f in os.listdir("data"):
        if f.startswith("page") and f.endswith(".xml"):
            page = file(os.path.join('data', f), 'rb')
            conn.loadDocument(page, 'page%d' % counter, 'wikidb')
            page.close()
            sys.stdout.write("Document %s has been successfully loaded\n" % f)
            counter += 1
    
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
