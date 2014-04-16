# simple_server.py

import SimpleHTTPServer
import SocketServer

port = 8001
Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
httpd = SocketServer.TCPServer(("", port), Handler)

print "Serving HTTP at localhost:%s in case your browser doesn't allow loading of json files from disk with javascript and requires HTTP GET requests." % port
httpd.serve_forever()