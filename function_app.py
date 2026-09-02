import azure.functions as func
 
 
app = func.FunctionApp(http_auth_level func.AuthLevel.Anonymous)
 
@app.route(root="hello")

def hello(req):

  return func.HttpResponse("Hello")

 
