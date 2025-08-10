from flask import Flask, request, render_template, redirect, url_for, jsonify
from Newsletter import Newsletter
import requests
import glob
import os
import traceback
import sys
import json

app = Flask(__name__)
scriptPath = os.path.dirname(os.path.abspath(__file__))

# Initialize config at module level
with open(os.path.join(scriptPath, "config.json"), "r") as f:
    config = json.load(f)

pluginList = {}

def load_plugins():
    global scriptPath

    pluginPath = os.path.join(scriptPath, "plugins")

    sys.path.append(scriptPath)
    sys.path.append(pluginPath)

    pluginNames = glob.glob(os.path.join(pluginPath, "*.py"))
    
    for x in pluginNames: 
        pathName = x.replace(".py","")
        className = os.path.basename(pathName)

        # import the module
        mod = __import__(className)

        # find the symbol for the class
        cls  = getattr(mod, className)

        # add the plugin to the list
        pluginList[ cls().pluginName ] = cls()

@app.route('/api/preview', methods=['POST'])
def preview_newsletter():
    """Return rendered newsletter HTML for the current form state."""
    try:
        data = request.get_json(silent=True) or request.form

        host_name = data.get('hostSelect', '')
        location_name = data.get('locationSelect', '')
        film = data.get('film', '')
        filmURL = data.get('filmURL', '')
        wearing = data.get('wearing', '')
        showTime = data.get('showTime', '')
        synopsis = data.get('plotSynopsis', '')

        # Resolve host and location URLs from config
        host_url = ''
        for h in config.get('hosts', []):
            if h.get('name') == host_name:
                host_url = h.get('image', '')
                break

        location_url = ''
        for loc in config.get('locations', []):
            if loc.get('name') == location_name:
                location_url = loc.get('link', '')
                break

        nl = Newsletter(
            config.get('clubCity', ''),
            config.get('clubURL', ''),
            film,
            filmURL,
            host_name,
            host_url,
            location_name,
            location_url,
            wearing,
            showTime,
            synopsis,
        )

        # Apply manual override if provided
        use_manual = str(data.get('useManualHTML', '')).lower() in ('1', 'true', 'yes', 'on')
        override_html = data.get('overrideHTML')
        if use_manual and override_html:
            nl.override_html = override_html

        html = nl.generate_HTML()
        return jsonify({ 'html': html, 'error': None })
    except Exception as e:
        # Return error but 200 so the client can display it inline
        return jsonify({ 'html': '', 'error': str(e) })

@app.route('/api/omdb/search')
def omdb_search():
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Search query is required'}), 400
    
    api_key = config['omdb']['apiKey']
    response = requests.get(f'http://www.omdbapi.com/?apikey={api_key}&s={query}&type=movie')
    return jsonify(response.json())

@app.route('/api/omdb/movie')
def omdb_movie():
    imdb_id = request.args.get('id', '')
    if not imdb_id:
        return jsonify({'error': 'IMDB ID is required'}), 400
    
    api_key = config['omdb']['apiKey']
    response = requests.get(f'http://www.omdbapi.com/?apikey={api_key}&i={imdb_id}&plot=full')
    return jsonify(response.json())

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        form = request.form

        hostIndex = 0;
        locationIndex = 0
        
        for x in config['hosts']:
            if x['name'] == form["hostSelect"]:
                break
            hostIndex += 1

        for x in config['locations']:
            if x['name'] == form["locationSelect"]:
                break
            locationIndex += 1

        nl = Newsletter(config['clubCity'],
                        config['clubURL'],
                        form["film"],
                        form["filmURL"],
                        form["hostSelect"],
                        config["hosts"][hostIndex]['image'],
                        form["locationSelect"],
                        config["locations"][locationIndex]['link'],
                        form["wearing"],
                        form["showTime"],
                        form["plotSynopsis"])

        # If manual HTML override was provided, use it
        use_manual = str(form.get('useManualHTML', '')).lower() in ('1', 'true', 'yes', 'on')
        override_html = form.get('overrideHTML')
        if use_manual and override_html:
            nl.override_html = override_html

        load_plugins()

        selected_plugins = form.getlist("plugins")
        results = []

        for plugin_name in selected_plugins:
            plugin = pluginList[plugin_name]
    
            try:
                response = plugin.execute(config, nl)
                results.append({
                    'plugin': plugin_name,
                    'success': True,
                    'message': response,
                    'url': extract_url(response) if response else None
                })
            except Exception as e:
                results.append({
                    'plugin': plugin_name,
                    'success': False,
                    'message': str(e),
                    'url': None
                })

        return jsonify(results)

    else:
        load_plugins()
        plugNames = [item for item in pluginList]
        return render_template('form.html', pluginList=plugNames, hostsDict=config['hosts'], locationDict=config['locations'])

def extract_url(text):
    # Extract URL from HTML response
    import re
    match = re.search(r'href=[\'"]?([^\'" >]+)', text)
    if match:
        return match.group(1)
    return None

if __name__ == '__main__':
    app.run(debug=True)