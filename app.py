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
        try:
            # import the module
            mod = __import__(className)

            # find the symbol for the class
            cls = getattr(mod, className)

            # instantiate
            instance = cls()

            # determine plugin key name safely
            name = getattr(instance, 'pluginName', None) or getattr(cls, 'pluginName', None) or className

            # add the plugin to the list
            pluginList[name] = instance
        except Exception:
            print(f"Failed to load plugin '{className}':\n{traceback.format_exc()}")

def is_plugin_enabled(config_obj, plugin_obj):
    try:
        section = config_obj.get(getattr(plugin_obj, 'configSection', ''), {})
        return bool(section.get('enabled', True))
    except Exception:
        return True

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
        override_subject = data.get('overrideSubject')

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

        # Apply manual overrides if provided
        use_manual = str(data.get('useManualHTML', '')).lower() in ('1', 'true', 'yes', 'on')
        override_html = data.get('overrideHTML')
        if use_manual and override_html:
            nl.override_html = override_html
        if use_manual and override_subject is not None:
            nl.override_subject = override_subject

        html = nl.generate_HTML()
        subject = nl.generate_subject()
        return jsonify({ 'html': html, 'subject': subject, 'error': None })
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

        hostIndex = 0
        locationIndex = 0
        
        use_manual = str(form.get('useManualHTML', '')).lower() in ('1', 'true', 'yes', 'on')

        # Resolve host/location safely; if manual mode, allow empty/missing
        host_name = form.get("hostSelect", "")
        location_name = form.get("locationSelect", "")

        if not use_manual:
            for x in config['hosts']:
                if x['name'] == host_name:
                    break
                hostIndex += 1

            for x in config['locations']:
                if x['name'] == location_name:
                    break
                locationIndex += 1

        # Server-side minimal validation when not in manual mode
        if not use_manual:
            if not form.get('film'):
                return jsonify({'error': 'Film title is required'}), 400
            film_url_val = form.get('filmURL', '')
            if not film_url_val or not (film_url_val.startswith('http://') or film_url_val.startswith('https://')):
                return jsonify({'error': 'Valid Film URL is required'}), 400

        nl = Newsletter(config['clubCity'],
                        config['clubURL'],
                        form.get("film", ""),
                        form.get("filmURL", ""),
                        host_name,
                        (config["hosts"][hostIndex]['image'] if (not use_manual and config['hosts']) else ''),
                        location_name,
                        (config["locations"][locationIndex]['link'] if (not use_manual and config['locations']) else ''),
                        form.get("wearing", ""),
                        form.get("showTime", ""),
                        form.get("plotSynopsis", ""))

        # If manual HTML override was provided, use it
        override_html = form.get('overrideHTML')
        override_subject = form.get('overrideSubject')
        if use_manual and override_html:
            nl.override_html = override_html
        if use_manual and override_subject is not None:
            nl.override_subject = override_subject

        load_plugins()

        selected_plugins = [p for p in form.getlist("plugins") if is_plugin_enabled(config, pluginList.get(p))]
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
        # Only show enabled plugins in the UI
        plugNames = [name for name, pobj in pluginList.items() if is_plugin_enabled(config, pobj)]
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