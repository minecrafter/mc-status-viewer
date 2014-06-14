from collections import OrderedDict
import mcstatus, yaml, threading, sys
from bottle import route, run, template, static_file, error

data = {}
json_response = None

with open('config.yml', 'r') as cfg_file:
    servers_config = yaml.load(cfg_file)

for category in servers_config:
    print category
    data[category] = {}
    for server in servers_config[category]:
        print "- " + server + ": " + servers_config[category][server]
        ip = servers_config[category][server]
        if "/" not in ip:
            ip += "/25565"
        status = mcstatus.McServer(ip.split("/")[0], ip.split("/")[1])
        data[category][server] = status

def update_all():
    for category in data:
        for server in data[category]:
            status = data[category][server]
            threading.Thread(target=lambda: status.update()).start()
            
def sort_dict_by_key(to_sort):
    return OrderedDict(sorted(to_sort.items(), key=lambda t: t[0]))

def generate_json():
    response = {"alive": {}, "dead": {}}

    for category in data:
        alive = {}
        dead = []
        for server in data[category]:
            status = data[category][server]
            if status.available:
                alive[server] = str(status.num_players_online) + "/" + str(status.max_players_online)
            else:
                dead.append(server)

        if len(alive) > 0:
            response["alive"][category] = sort_dict_by_key(alive)
        if len(dead) > 0:
            dead.sort()
            response["dead"][category] = dead

    response["alive"] = sort_dict_by_key(response["alive"])
    response["dead"] = sort_dict_by_key(response["dead"])
    return response

def schedule_update():
    threading.Timer(5, schedule_update).start()
    update_all()
    global json_response
    json_response = generate_json()

@route('/status')
def index():
    return json_response

@route('/')
def server_static():
    return static_file('index.html', '..')

@error(404)
def error404(error):
    return static_file('404.html', '..')

@route('/<filename>')
def server_static(filename):
    return static_file(filename, root = '..')

schedule_update()

try:
    run(host='localhost', port=8080)
except KeyboardInterrupt:
    sys.exit(0)
