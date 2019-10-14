# graphbi
Browsing graph database with graph visualization and a pivot table.

# Dependencies
- python packages: pandas, cherrypy, os, json, pydgraph
- javascript: jquery jquery-3.4.1
- dgraph 1.1.0


# Get started
1. Check the server.conf file 
-change <hostname>, if needed change also the port
- if the port for the application (default 8070) is not free, then change this too
- if you run the server locally then change '0.0.0.0' to localhost or 127.0.0.1
2. Run the server (python3 main.py)
3. Call the URL (host:port) and run a query. If you query edges, then use the @normalize directive in dgraph to flatten the result.
4. Use filter (like x > 1 or y = 'name') and group(predicate1, predicate2) 
