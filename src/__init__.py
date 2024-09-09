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
configs = jdtk.load_directory("./configs")

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
    for config in configs:
        has_chapters = "chapter" in config.params("images")
        auto_chapters = config.has("series.chapters")
        
        data[config.meta.key] = {
            "chapters": {
                "supported": has_chapters,
                "auto": auto_chapters
            }
        }     
    return jsonify({"result": data})

@app.route('/match', methods=['GET'])
def match():
    result = None
    url = request.args.get("url")
    if url:
        for w in configs:
            match = w.match(url)
            if match:
                result = {
                    "key": w.meta.key,
                    "params": match
                }
                break
    return jsonify({"result": result})


@app.route('/website/<config_key>/series', methods=['GET'])
@config_from_key(configs)
def series(config: jidouteki.Config, data = ""):
    kdata = request.args.to_dict()
    
    result = {}

    if config.has("series.cover"): 
        result["cover"] = config.series.cover(**kdata)
    
    if config.has("series.title"): 
        result["title"] = config.series.title(**kdata)
        
    if config.has("series.chapters"): 
        result["chapters"] = config.series.chapters(**kdata)
                
    return jsonify({"result": result if result else None})

@app.route('/website/<config_key>/images', methods=['GET'])
@config_from_key(configs)
def pages(config: jidouteki.Config, data = ""):
    kdata = request.args.to_dict()
    result = None
    
    pages = config.images(**kdata)
    if pages:
        base = base_substr(pages)
        pages = [page.removeprefix(base) for page in pages]
        
        result = [{
            "name":  config.meta.display_name,
            "base": base,
            "pages": pages
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