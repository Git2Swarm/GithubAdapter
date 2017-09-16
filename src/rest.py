from flask import Flask
from flask import jsonify
from flask import request
from flask import make_response

import requests
import logging
import base64
import json

app = Flask(__name__)

with open('/src/config.json') as data:
  config = json.load(data)

gitCommitterName  = "agileclouds"
gitCommitterEmail = "admin@agileclouds.com"

def getAuth():
  return (config['auth']['user'], config['auth']['token'])

def isValidRoute(route):
  if route in config['store'].keys():
    return True
  else:
    return False

def getGithubOrg(route):
  return config['store'][route]['org']

def getGithubRepo(route):
  return config['store'][route]['repo']

def _listFiles(route):
  gitContentUrl = "https://api.github.com/repos/" + \
                  getGithubOrg(route) + "/" + \
                  getGithubRepo(route) + "/contents/"

  req = requests.get( gitContentUrl,
                      auth = getAuth())

  if req.status_code != 200:
    logging.warning("status: " + str(req.status_code))
    logging.warning("error msg: " + req.text)
    response = jsonify ( {'status': req.status_code, 'error': req.text} )
    response.status_code = req.status_code
    return response

  data = req.json()
  logging.warning(json.dumps(data, indent=2))

  filearr=[]
  for index in range(len(data)):
    filearr.append ({"name": data[index]['name'],
                     "type": data[index]['type'],
                     "size": data[index]['size'],
                     "sha" : data[index]['sha']})

  return jsonify(filearr)

def _createFile(route, filename, content):
  payload = { 'message': 'automated upload', 'committer': { 'name': gitCommitterName, 'email': gitCommitterEmail}, 'content': content}
  logging.warning(json.dumps(payload, indent=2))

  gitContentUrl = "https://api.github.com/repos/" + \
                  getGithubOrg(route) + "/" + \
                  getGithubRepo(route) + "/contents/"

  req = requests.put( gitContentUrl + filename,
		      auth = getAuth(),
                      json = payload)

  logging.warning("status: " + str(req.status_code))
  logging.warning(json.dumps(req.text, indent=2))

  if req.status_code == 201:
    response = jsonify ( {
                  'status': req.status_code, 
                  'msg': "file " + filename + " created",
                  'sha': req.json()['content']['sha']
                  } )
    response.status_code = req.status_code
    return response

  if req.status_code == 422:
    response = jsonify ( {'status': req.status_code, 'error': "file " + filename + " already exists"} )
    response.status_code = req.status_code
    return response

  response = jsonify ( {'status': req.status_code, 'error': req.text} )
  response.status_code = req.status_code
  return response

def _updateFile(route, filename, content):
  
   gitContentUrl = "https://api.github.com/repos/" + \
                  getGithubOrg(route) + "/" + \
                  getGithubRepo(route) + "/contents/" + \
                  filename

   req = requests.get( gitContentUrl,
		      auth = getAuth())

   logging.warning("status: " + str(req.status_code))
   logging.warning(json.dumps(req.text, indent=2))
   if req.status_code == 404:
     return _createFile(route, filename, content)

   payload = { 'message': 'automated update', 
               'committer': { 'name': gitCommitterName, 'email': gitCommitterEmail}, 
               'sha': req.json()['sha'], 
               'content': content}

   logging.warning(json.dumps(payload, indent=2))


   req = requests.put( gitContentUrl,
		      auth = getAuth(),
                      json = payload)

   logging.warning("url: " + gitContentUrl)
   logging.warning("status: " + str(req.status_code))
   logging.warning(json.dumps(req.text, indent=2))
  
   if req.status_code == 200:
      response = jsonify ( {
                  'status': req.status_code,
                  'msg': "file " + filename + " updated",
                  'sha': req.json()['content']['sha']
                  } )
      response.status_code = req.status_code
      return response

   response = jsonify ( {'status': req.status_code, 'error': req.text} )
   response.status_code = req.status_code
   return response
	
def _getFile(route, filename):
  gitContentUrl = "https://api.github.com/repos/" + \
                  getGithubOrg(route) + "/" + \
                  getGithubRepo(route) + "/contents/" + \
                  filename
  req = requests.get( gitContentUrl,
		      auth = getAuth())

  if req.status_code != 200:
    logging.warning("status : " + str(req.status_code))
    logging.warning(json.dumps(req.text, indent=2))
    response = jsonify ( {'status': req.status_code, 'error': "could not retrieve sha"} )
    response.status_code = req.status_code
    return response

  data = req.json()
 
  content = base64.b64decode(data['content']).decode('utf-8')
  response = jsonify ( {
              'filename': data['name'],
              'sha': data['sha'],
              'content': content
              } )
  response.status_code = req.status_code
  return response

def _deleteFile(route, filename):
  gitContentUrl = "https://api.github.com/repos/" + \
                  getGithubOrg(route) + "/" + \
                  getGithubRepo(route) + "/contents/" + \
                  filename

  req = requests.get( gitContentUrl,
		      auth = getAuth())

  if req.status_code != 200:
    logging.warning("status: " + str(req.status_code))
    logging.warning(json.dumps(req.text, indent=2))
    response = jsonify ( {'status': req.status_code, 'error': "could not retrieve sha"} )
    response.status_code = req.status_code
    return response

  payload = { 'message': 'automated upload', 
              'committer': { 'name': gitCommitterName, 'email': gitCommitterEmail}, 
              'sha': req.json()['sha'] }

  req = requests.get( gitContentUrl,
		      auth = getAuth(),
                      json = payload )

  if req.status_code == 200:
    response = jsonify ( {'status': req.status_code, 'msg': "file is successfully deleted"} )
    return response

  logging.warning("status: " + str(req.status_code))
  logging.warning(json.dumps(req.text, indent=2))
  response = jsonify ( {'status': req.status_code, 'error': "could not delete file"} )
  response.status_code = req.status_code
  return response

@app.route('/<route>/files', methods=['GET'])
def listFiles(route):
  return _listFiles(route)
    
@app.route('/<route>/files/<filename>', methods=['GET'])
def getFile(route, filename):
  return _getFile(route, filename)
	
@app.route('/<route>/files/<filename>', methods=['POST'])
def createFile(route, filename):

  if request.data:
    if request.json:
      jsonData = request.get_json(silent=True)
      content = base64.b64encode(json.dumps(jsonData, indent=2))
      return _createFile(route, filename, content)

    # request has data but not json, so it must be file upload
    content = base64.b64encode( request.data )
    return _createFile(route, filename, content)

  if 'file' in request.files:
    fileData = request.files['file'].read()
    content = base64.b64encode( fileData )
    return _createFile(route, filename, content)

  logging.error('file data missing')
  response = jsonify ( {'error': 'file data missing'} )
  response.status_code = 400
  return response

@app.route('/<route>/files/<filename>', methods=['PUT'])
def updateFile(route, filename):

  if request.data:
    if request.json:
      jsonData = request.get_json(silent=True)
      content = base64.b64encode(json.dumps(jsonData, indent=2))
      return _updateFile(route, filename, content)

    # request has data but not json, so it must be file upload
    content = base64.b64encode( request.data )
    return _updateFile(route, filename, content)

  if 'file' in request.files:
    fileData = request.files['file'].read()
    content = base64.b64encode( fileData )
    return _updateFile(route, filename, content)

  logging.error('json input missing')
  response = jsonify ( {'error': 'file data missing'} )
  response.status_code = 400
  return response

@app.route('/<route>/files/<filename>', methods=['DELETE'])
def deleteFile(route, filename):
  return _deleteFile(route, filename)

@app.errorhandler(404)
def not_found(error):
  return make_response(jsonify({'error': 'Not found'}), 404)
    

if __name__ == '__main__':
    app.run(debug = True, host = '0.0.0.0')
