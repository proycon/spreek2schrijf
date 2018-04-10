import sys
import spreek2schrijf.webservice
import clam.clamservice
application = clam.clamservice.run_wsgi(spreek2schrijf.webservice.spreek2schrijf)
