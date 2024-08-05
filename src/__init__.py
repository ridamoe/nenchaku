import json
import requests
from jidouteki import Jidouteki
import re
from flask import Flask, jsonify, request, Response
from .utils import *

app = Flask(__name__)
app.json.sort_keys = False
app.url_map.strict_slashes = False

jdtk = Jidouteki(
    proxy="http://localhost/api/proxy?url="
)
websites = jdtk.load_all("./configs")

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
    return jsonify({
        "available_proxies": [website.metadata.key for website in websites]
        })

@app.route('/match', methods=['GET'])
def match():
    result = None
    url = request.args.get("url")
    if url:
        for w in websites:
            match = w.match.parse(url)
            if match:
                result = {
                    "website": w.metadata.key,
                    "params": match
                }
                break
    return jsonify({"result": result})


@app.route('/website/<website_key>/series', methods=['GET'])
@app.route('/website/<website_key>/series/<path:data>', methods=['GET'])
@website_from_key(websites)
def series(website: jidouteki.Website, data = ""):
    data = data.split("/")
    kdata = request.args.to_dict()
    result = {}

    if website.series:
        if website.series.cover:
            result["cover"] = website.series.cover.parse(*data, **kdata)
            
        if website.series.title:
            result["title"] = website.series.title.parse(*data, **kdata)
        
        if website.series.chapters:
            result["chapters"] = website.series.chapters.parse(*data, **kdata)
    
    return jsonify({"result": result if result else None})

@app.route('/website/<website_key>/chapter/pages', methods=['GET'])
@app.route('/website/<website_key>/chapter/pages/<path:data>', methods=['GET'])
@website_from_key(websites)
def pages(website: jidouteki.Website, data):
    data = data.split("/")
    kdata = request.args.to_dict()
    result = None
    
    pages = website.chapter.pages.parse(*data, **kdata)
    if pages:
        base = base_substr(pages)
        pages = [page.removeprefix(base) for page in pages]
        
        result = {
            "name":  website.metadata.display_name,
            "base": base,
            "pages": pages
        }
    return jsonify({"result": result})


@app.errorhandler(404)
def page_not_found(e):
    return jsonify(error="Not Found"), 404

@app.after_request
def after_request(response: Response):
    response.headers.set('Access-Control-Allow-Origin', '*')
    response.headers.set('Access-Control-Allow-Methods', 'GET,OPTIONS')
    return response