import requests
from jidouteki import Jidouteki
import re
import os
from flask import Flask, jsonify, request, Response
from .utils import *

app = Flask(__name__)
app.json.sort_keys = False
app.url_map.strict_slashes = False

jdtk = Jidouteki(
    proxy = os.environ.get("PUBLIC_API_ENDPOINT", "http://localhost/api") + "/proxy"
)

providers_dir = os.environ.get("PROVIDERS_DIR", "./providers")
providers = jdtk.load_directory(providers_dir)

@app.route('/proxy/', methods=['GET', 'OPTIONS'])
def proxy():
    url = request.args.get("url")
    if not url:
        return Response(status=400)

    headers = {}
    for key, value in request.headers:
        if any(key.startswith(el) for el in ["User-Agent", "Sec-Ch-Ua"]):
            headers[key] = value
    urlheaders = request.args.getlist("header")
    for h in urlheaders:
        match = re.fullmatch(r"(?P<key>.*?):\s?(?P<value>.*)", h).groupdict()
        if (match):
            headers[match["key"]] = match["value"]
    
    session = requests.session()
    fetched = session.get(url, headers=headers, allow_redirects=True)
    resp = Response(status=fetched.status_code)
    resp.headers.set('Access-Control-Allow-Origin', '*')
    resp.headers.set('Access-Control-Allow-Methods', 'GET,OPTIONS')
    
    for key, value in fetched.headers.items():
        if key not in ["Date", "Server", "Connection", "Content-Encoding", "Transfer-Encoding"]:
            resp.headers.set(key, value)
    if request.method == 'GET': resp.set_data(fetched.content)
    
    return resp

@app.route('/info', methods=['GET'])
def info():
    data = {}
    for provider in providers:
        data[provider.meta.key] = {
            "chapters": {
                "supported": "chapter" in provider.params.images,
                "auto": provider.has.series.chapters
            }
        }     
    return jsonify({"result": data})

@app.route('/match', methods=['GET'])
def match():
    result = None
    url = request.args.get("url")
    if url:
        for w in providers:
            match = w.get.match(url)
            if match:
                result = {
                    "key": w.meta.key,
                    "params": match
                }
                break
    return jsonify({"result": result})


@app.route('/website/<provider_key>/series', methods=['GET'])
@provider_from_key(providers)
def series(provider: jidouteki.Provider, data = ""):
    kdata = request.args.to_dict()
    
    result = {}

    if provider.has.series.cover: 
        result["cover"] = provider.get.series.cover(**kdata)
    
    if provider.has.series.title: 
        result["title"] = provider.get.series.title(**kdata)
        
    if provider.has.series.chapters: 
        result["chapters"] = provider.get.series.chapters(**kdata)
                
    return jsonify({"result": result if result else None})

@app.route('/website/<provider_key>/images', methods=['GET'])
@provider_from_key(providers)
def images(provider: jidouteki.Provider, data = ""): # TODO: rename to "galleries"
    kdata = request.args.to_dict()
    result = None
    
    images = provider.get.images(**kdata)
    if images:
        base = base_substr(images)
        images = [page.removeprefix(base) for page in images]
        
        result = [{
            "name":  provider.meta.display_name,
            "base": base,
            "images": images
        }]
    return jsonify({"result": result})


@app.errorhandler(404)
def page_not_found(e):
    return jsonify(error="Not Found"), 404

@app.after_request
def after_request(response: Response):
    response.headers.set('Access-Control-Allow-Origin', '*')
    response.headers.set('Access-Control-Allow-Methods', 'GET,OPTIONS')
    return response