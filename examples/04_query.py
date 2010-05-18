##############################################################################
## File:  04_query.py
##
## Copyright (C) 2009, Apache License 2.0 
## The Institute for System Programming of the Russian Academy of Sciences
## 
## The application opens a session to "testdb" database, executes the query: 
##   "Construct category page: list all parent categories; list all 
##    pages in the category".
##
## NOTE: this example uses data from collection 'wikidb' and document 
##       'categories'. Run subsequently 02_load, 03_load_coll to create them.
##############################################################################

import sys
import sedna
import os

conn = None

# This query builds small HTML document using data from collection 'wikidb' 
query = """let $c:='Category:Anarchism'
return
<html>
    <h1>{$c}</h1>
    <br/>
    <i>Parent categories:</i>
    <ul>
        {for $p in doc('categories')/categories/category[@id=$c]/parent
         return <li>{$p//@id/string()}</li>}
    </ul>
    <br/>
    <i>Articles in this category:</i>
    <ul>
        {for $a in collection('wikidb')/page[.//catlink/@href=$c]
         return <li>{$a/title/text()}</li>}
    </ul>
</html>"""

try:
    # Connect to the testdb database which is located on localhost
    conn = sedna.SednaConnection('localhost', 'testdb')
    sys.stdout.write("Connection has been successfully established\n")

    # Transaction must be started before executing a query
    conn.beginTransaction()
    
    # Execute query ...
    conn.execute(query)
    
    # ... and write result
    for res in conn.resultSequence():
        sys.stderr.write(res)
    
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
