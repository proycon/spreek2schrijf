import sys
#sys.path.append("/vol/tensusers/eyilmaz/FAME/webservice/spreek2schrijf")
import spreek2schrijf.webservice
import clam.clamservice
application = clam.clamservice.run_wsgi(spreek2schrijf.webservice.spreek2schrijf)
