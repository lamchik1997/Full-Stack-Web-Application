import socketserver


def build_OK_response(mineType, content):
    return buildResponseFromByte("200 OK", mineType, content)


def build_404_response(mineType, content):
    return buildResponseFromByte("404 Not Found", mineType, content)


def buildResponseFromByte(response_code, mineType, content):
    response = "HTTP/1.1 " + response_code + "\r\n"
    response += "Content-Type: " + mineType + "\r\n"
    response += "Content-length: " + str(len(content)) + "\r\n"
    response += "X-Content-Type-Options: nosniff" + "\r\n"
    response += "\r\n"
    return response, content


def buildTemplate(query_map):
    name_value = query_map.get('name')[0]
    message = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HTML Template</title>
    </head>
    <body>
    <h1 id="welcome">Welcome to my page,\t""" + name_value +"""</h1>
    <p>Here is the images that you requested: </p>
    """
    for v in query_map["images"]:
        message += "<img src=/images/" + v + ".jpg>\n"
    message += "</body> \n </html>"
    content = open("template.html", "w")
    content.write(message)
    content.close()
    file = open("template.html","r")
    content = file.read()
    return content


def parseQuery(path):
    dictionary = {}
    if not path.startswith('?'):
        build_404_response(
            'text/plain', "The query is not with '?' keyword....")
        print("This is not start with ?....")
    path = path[1:]
    # print("The path is " + path)
    query = path.split('&')
    # print("The set of query [1] is : " + query[0],
    #       "The second query is [2]: ", query[1])
    for q in query:
        sub_q = q.split('=')
        if sub_q[1].find('+') == -1:
            # there is no + images or it is a name.
            dictionary[sub_q[0]] = [sub_q[1]]
        else:
            values = sub_q[1].split('+')
            dictionary[sub_q[0]] = [values[0]]
            for v in range(1, len(values)):
                dictionary[sub_q[0]].append(values[v])
    return dictionary


def decode_content_byte(path):
    if path.endswith('.jpg'):
        content_type = 'image/jpeg'
        if path.startswith("/image/"):
            path = path.replace('/image/', '/images/', 1)
    elif path.endswith('.ico'):
        content_type = 'image/x-icon'
    else:
        content_type = 'text/plain; charset=UTF-8'
    file = open(path[1:], "rb")
    content = file.read()
    header, content = buildResponseFromByte('200 OK', content_type, content)
    file.close()
    return header, content


def decode_content(path):
    requestFile = path[1:]
    if path == '/' or path == '/index.html':
        requestFile = "index.html"
        content_type = "text/html"
    elif path.startswith('/images'):
        content = buildTemplate(parseQuery(path[7:]))
        # This is the objective 4 content with query language.
        content_type = 'text/html'
        return build_OK_response(content_type, content)
        # requestFile = 'template.html'
    elif path.endswith('.css'):
        content_type = 'text/css'
    elif path.endswith('.js'):
        content_type = 'text/javascript'
    else:
        content_type = "text/plain"
        return build_404_response(content_type, "404 Page Not Found.\nThe path = " + requestFile)

    file = open(requestFile, "r")
    content = file.read()
    header, content = build_OK_response(content_type, content)
    file.close()
    return header, content


class MYTCPHandler(socketserver.BaseRequestHandler):

    def handle(self):
        received_data = self.request.recv(1024).strip()
        # print(self.client_address[0] + " is sending data:")
        # convert it from byte array to string.
        decode_data = received_data.decode()
        request_line = decode_data.strip("\r\n")
        parts = request_line.split()
        request_type = parts[0]
        request_path = parts[1]
        if request_type == 'GET':
            if str(request_path).endswith('.jpg') or str(request_path).endswith('.txt') \
                    or str(request_path).endswith('.ico'):
                header, content = decode_content_byte(str(request_path))
                self.request.sendall(header.encode() + content)

            else:
                header, content = decode_content(str(request_path))
                self.request.sendall(header.encode() + content.encode())
        else:
            # post or request. We wil do it later...
            print("This is not a get request.")
            content = "This is not a get request!"
            self.request.sendall(
                "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: " + str(
                    len(content)) + "\r\n\r\n" + content)


if __name__ == "__main__":
    host = "0.0.0.0"
    # host = "localhost"
    port = 8000

    server = socketserver.ThreadingTCPServer((host, port), MYTCPHandler)
    server.serve_forever()
