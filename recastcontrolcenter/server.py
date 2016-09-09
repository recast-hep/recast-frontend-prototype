#must be loaded first so that env vars get set
import recastconfig

import recastapi

import gevent
from gevent import monkey; monkey.patch_all()
import json
import os
import importlib
import pkg_resources
import flask
import recastcontrolcenter.backendtasks as asynctasks

from flask import Flask, render_template, request, jsonify, send_from_directory,redirect, session, url_for, abort
from socketio import socketio_manage
from socketapp import MonitoringNamespace
from recast_interface_blueprint import recast

import recastbackend.resultaccess
from recastdb.database import db

celery_app  = importlib.import_module(recastconfig.config['RECAST_CELERYAPP']).app

def get_blueprint(name):
    module,attr = name.split(':')
    blueprintmodule = importlib.import_module(module)
    return getattr(blueprintmodule,attr)

def create_app(config = None):
    templates_path = pkg_resources.resource_filename('recastcontrolcenter','templates')
    static_path    = pkg_resources.resource_filename('recastcontrolcenter','static')
    app = Flask('RECAST-demo',template_folder = templates_path, static_folder = static_path)
    app.config.from_object('recastcontrolcenter.admin.default_config')
    if config:
        app.config.from_object(config)
    app.register_blueprint(recast, url_prefix='/recast')
    db.init_app(app)
    return app

flask_app = create_app()


from flask_oauth import OAuth
oauth = OAuth()
oauth_app = oauth.remote_app('oauth_app',
    base_url=None,
    request_token_url=None,
    access_token_url=recastconfig.config['RECAST_OAUTH_TOKENURL'],
    authorize_url=recastconfig.config['RECAST_OAUTUH_AUTHORIZEURL'],
    consumer_key = recastconfig.config['RECAST_OAUTH_APPID'],
    consumer_secret = recastconfig.config['RECAST_OAUTH_SECRET'],
    request_token_params= {'response_type':'code','scope':'bio'},
    access_token_params = {'grant_type':'authorization_code'},
    access_token_method = 'POST'
)


def user_data(access_token):
    r = requests.get('https://oauthresource.web.cern.ch/api/Me',
        headers = {'Authorization':'Bearer {}'.format(session['access_token'])})
    return r.json()

@flask_app.route(recastconfig.config['RECAST_OAUTH_REDIRECT_ROUTE'])
@oauth_app.authorized_handler
def oauth_redirect(resp):
    session['access_token'] = resp['access_token']
    data = user_data(session['access_token'])
    print 'this is the login!'
    print data
    return jsonify(data)

@flask_app.route('/login')
def login():
    redirect_uri = config['RECAST_BASEURL']+config['RECAST_OAUTH_REDIRECT_ROUTE']
    return oauth_app.authorize(callback=redirect_uri)

@flask_app.route('/logout')
def logout():
  session.pop('user')
  return redirect('/')

#
# these are the views
#
@flask_app.route("/")
def home():
    if config['RECAST_OAUTH_DUMMYLOGIN']:
        if(session.has_key('user')): session.pop('user')
        session['user'] =  {'username':'lheinric'}
    userinfo = session.get('user',{})
    return render_template('home.html', userinfo = userinfo)

@flask_app.route('/status/<basicreqid>')
def request_point_status(basicreqid):
  resultdir = recastbackend.resultaccess.basicreqpath(basicreqid)
  available = os.path.exists(resultdir)
  print resultdir
  response = {'available':available, 'ready_backends':[]}
  if available:
      response['ready_backends'] = os.listdir(recastbackend.resultaccess.basicreqpath(basicreqid))
  return jsonify(**response)

@flask_app.route('/resultfile/<basicreqid>/<backend>/<path:filepath>')
def resultfile(basicreqid,backend,filepath):
  fullpath = recastbackend.resultaccess.resultfilepath(basicreqid,backend,filepath)
  return send_from_directory(os.path.dirname(fullpath),os.path.basename(fullpath))

import yaml
backendconfig = yaml.load(pkg_resources.resource_stream('recastcontrolcenter','resources/backendconfig.yml'))

resultviewconfig = {}
for resultview in backendconfig['resultviewconfig']:
    blueprint = get_blueprint(resultview['blueprint'])
    flask_app.register_blueprint(blueprint, url_prefix='/{}/{}'.format(
        resultview['analysis'],
        resultview['backend']
    ))
    analysis_backend = resultviewconfig.setdefault(resultview['analysis'],{}).setdefault(resultview['backend'],{})
    analysis_backend['blueprint'] = resultview['blueprint']

@flask_app.route('/resultview/<basicreqid>/<backend>')
def resultview(basicreqid,backend):
    point_id     = recastapi.request.read.basic_request(basicreqid)['point_request_id']
    scan_id      = recastapi.request.read.point_request(point_id)['scan_request_id']
    request_info = recastapi.request.read.scan_request(scan_id)
    analysis_id  = request_info['analysis_id']
    blueprintname = get_blueprint(resultviewconfig[analysis_id][backend]['blueprint']).name
    return redirect(url_for('{}.result_view'.format(blueprintname), basicreqid = basicreqid))

@flask_app.route('/monitor/<jobguid>')
def monitorview(jobguid):
  return render_template('monitor.html', jobguid = jobguid)

@flask_app.route('/socket.io/<path:remaining>')
def socketio(remaining):
    print "socket io route called"
    socketio_manage(request.environ, {
        '/monitor': MonitoringNamespace
    })
    return flask_app.response_class()
