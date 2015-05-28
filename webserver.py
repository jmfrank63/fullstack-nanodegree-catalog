from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem

import cgi

HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
    <title>Restaurants and Menus</title>
    <meta charset="utf-8">
    <style>
        ul {{
            list-style-type: none;
        }}
        .restaurant-name {{
            font-weight: bold;
        }}
        .restaurant-entry {{
            margin-bottom: 1em;
        }}
    </style>
</head>
<body>
{0}
</body>
</html>
"""

class WebServerHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # establish a database connection
        engine = create_engine('sqlite:///restaurantmenu.db')
        Base.metadata.bind = engine
        DBSession = sessionmaker(bind = engine)
        self.session = DBSession()
        BaseHTTPRequestHandler.__init__(self, *args, **kwargs)

    def make_list_entry(self, restaurant):
        '''
        Creates a HTML list element with the restaurant name
        '''
        entry = '''<li class="restaurant-entry">
                    <ul>
                        <li class="restaurant-name">{0}</li>
                        <li><a href="/{1}/edit">Edit</a></li>
                        <li><a href="{1}/delete">Delete</a></li>
                    </ul>
                  </li>'''.format(restaurant.name, restaurant.id)
        return entry

    def do_GET(self):
        try:
            if self.path.endswith("/restaurants"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                restaurants = self.session.query(Restaurant).all()
                restaurant_list = ['<ul>'] + \
                    [self.make_list_entry(restaurant)
                        for restaurant in restaurants] + \
                    ['</ul>'] + \
                    ['<a href="/new">Make a New Restaurant Here</a>']
                output = HTML_TEMPLATE.format('\n'.join(restaurant_list))
                self.wfile.write(output)
                return

            if self.path.endswith("/new"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                output = HTML_TEMPLATE
                output = output.format('''<form method='POST' enctype='multipart/form-data' action='/hello'><h2>Make a New Restaurant</h2><input name="create" type="text" ><input type="submit" value="Create"> </form>''')
                self.wfile.write(output)
                return

            if self.path.endswith("/hello"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                output = ""
                output += "<html><body>"
                output += "<h1>Hello!</h1>"
                output += '''<form method='POST' enctype='multipart/form-data' action='/hello'><h2>What would you like me to say?</h2><input name="message" type="text" ><input type="submit" value="Submit"> </form>'''
                output += "</body></html>"
                self.wfile.write(output)
                return

            if self.path.endswith("/hola"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                output = ""
                output += "<html><body>"
                output += "<h1>&#161Hola!</h1>"
                output += '''<form method='POST' enctype='multipart/form-data' action='/hello'><h2>What would you like me to say?</h2><input name="message" type="text" ><input type="submit" value="Submit"> </form>'''
                output += "</body></html>"
                self.wfile.write(output)
                return

            if self.path.endswith('/edit'):
                id = self.path.split('/')[-2]
                if id.isdigit():
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    restaurant = self.session.query(Restaurant).filter_by(id = id).first()
                    output = HTML_TEMPLATE.format('<h2>' + restaurant.name + '</h2>' + '''<form method="POST" enctype="multipart/form-data" action="/''' + id + '''/edit"><h2>Enter a New Name:</h2><input name="edit" type="text" ><input type="submit" value="Edit"> </form>''')
                    self.wfile.write(output)
                else:
                    self.send_error(404, 'File Not Found: %s' % self.path)
                return

            if self.path.endswith('/delete'):
                id = self.path.split('/')[-2]
                if id.isdigit():
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    restaurant = self.session.query(Restaurant).filter_by(id = id).first()
                    output = HTML_TEMPLATE.format('<h2>' + restaurant.name + '</h2>' + '''<form method="POST" enctype="multipart/form-data" action="/''' + id + '''/delete"><h2>Type Restaurant Name to confirm deletion:</h2><input name="delete" type="text" ><input type="submit" value="Delete"> </form>''')
                    self.wfile.write(output)
                else:
                    self.send_error(404, 'File Not Found: %s' % self.path)
                return

            self.send_error(404, 'File Not Found: %s' % self.path)
        except:
            self.send_error(404, 'File Not Found: %s' % self.path)

    def do_POST(self):
        try:
            self.send_response(301)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)
                field_keys = fields.keys()
                if 'message' in field_keys:
                    messagecontent = fields.get('message')
                    output = ""
                    output += "<html><body>"
                    output += " <h2>Ok, how about this:</h2>"
                    output += "<h1> %s </h1>" % messagecontent[0]
                    output += '''<form method='POST' enctype='multipart/form-data' action='/hello'><h2>What would you like me to say?</h2><input name="message" type="text" ><input type="submit" value="Submit"> </form>'''
                    output += "</body></html>"
                    self.wfile.write(output)
                    return

                if 'create' in field_keys:
                    self.session.add(Restaurant(name = fields.get('create')[0]))
                    self.session.commit()
                    output = HTML_TEMPLATE.format(fields.get('create')[0] + \
                            ''' successfully created <a href="/restaurants">Back to Restaurants</a> ''')
                    self.wfile.write(output)
                    return

                if 'edit' in field_keys:
                    id = self.path.split('/')[-2]
                    new_name = fields.get('edit')[0]
                    restaurant = self.session.query(Restaurant).filter_by(id = id).first()
                    old_name = restaurant.name
                    restaurant.name = new_name
                    self.session.add(restaurant)
                    self.session.commit()
                    output = HTML_TEMPLATE.format(old_name + \
                            ''' successfully edited to ''' + new_name + ''' <a href="/restaurants">Back to Restaurants</a> ''')
                    self.wfile.write(output)
                    return
                
                if 'delete' in field_keys:
                    id = self.path.split('/')[-2]
                    delete_name = fields.get('delete')[0]
                    restaurant = self.session.query(Restaurant).filter_by(id = id).first()
                    if delete_name == restaurant.name:
                        self.session.delete(restaurant)
                        self.session.commit()
                    output = HTML_TEMPLATE.format(delete_name + \
                            ''' successfully deleted <a href="/restaurants">Back to Restaurants</a> ''')
                    self.wfile.write(output)
                    return

        except:
            pass


def main():
    try:
        port = 8080
        server = HTTPServer(('', port), WebServerHandler)
        print "Web Server running on port %s" % port
        server.serve_forever()
    except KeyboardInterrupt:
        print " ^C entered, stopping web server...."
        server.socket.close()

if __name__ == '__main__':
    main()