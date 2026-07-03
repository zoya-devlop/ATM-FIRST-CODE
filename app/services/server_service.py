servers = []

def create_server(name):
    server = {"name": name}
    servers.append(server)
    return server

def get_servers():
    return servers

def delete_server(name):
    global servers
    servers = [s for s in servers if s["name"] != name]
    return {"message": "Server deleted"}