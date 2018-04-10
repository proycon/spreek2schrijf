import sys
import spreek2schrijf.webservice.spreek2schrijf as config
import clam.clamservice
application = clam.clamservice.run_wsgi(config)
