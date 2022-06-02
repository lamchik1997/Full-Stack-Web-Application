import socketserver
import string
import random


def build_OK_response(mineType, content):
    return buildResponseFromByte("200 OK", mineType, content)


def build_404_response(mineType, content):
    return buildResponseFromByte("404 Not Found", mineType, content)


def build_301_response(newPath):
    response = "HTTP/1.1 301 Moved Permanently\r\n"
    response += "Location: " + newPath
    return response


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
    <h1 id="welcome">Welcome to my page,\t""" + name_value + """</h1>
    <p>Here is the images that you requested: </p>
    """
    for v in query_map["images"]:
        message += "<img src=/images/" + v + ".jpg>\n"
    message += "</body> \n </html>"
    content = open("template.html", "w")
    content.write(message)
    content.close()
    file = open("template.html", "r")
    content = file.read()
    return content


def parseQuery(path):
    dictionary = {}
    if not path.startswith('?'):
        build_404_response(
            'text/plain', "The query is not with '?' keyword....")
    path = path[1:]
    query = path.split('&')
    for q in query:
        sub_q = q.split('=')
        if sub_q[1].find('+') == -1:
            dictionary[sub_q[0]] = [sub_q[1]]
        else:
            values = sub_q[1].split('+')
            dictionary[sub_q[0]] = [values[0]]
            for v in range(1, len(values)):
                dictionary[sub_q[0]].append(values[v])
    return dictionary


def checkImgFile(v):
    check = False
    if v == 'cat.jpg' or v == 'dog.jpg' or v == 'eagle.jpg' or v == 'elephant.jpg' or v == 'flamingo.jpg' or v == \
            'kitten.jpg' or v == 'parrot.jpg' or v == 'rabbit.jpg':
        check = True
    return check


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
    if path == '/comment' or path == '/image-upload':
        return build_301_response('index.html')
    if path == '/' or path == '/index.html':
        requestFile = "index.html"
        content_type = "text/html"
    elif path.startswith('/images'):
        if not path[8:].startswith('cat') and not path[8:].startswith('dog') and not path[8:].startswith('eagle') and \
                not path[8:].startswith('elephant') and not path[8:].startswith('flamingo') and \
                not path[8:].startswith('kitten') and not path[8:].startswith('parrot') and \
                not path[8:].startswith('rabbit'):
            message = "Invalid file accessed. Your submission was rejected."
            return buildResponseFromByte("403 Forbidden", 'text/plain; charset=UTF-8', message)
        content = buildTemplate(parseQuery(path[7:]))
        content_type = 'text/html'
        return build_OK_response(content_type, content)
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


"""
This function will parse the header element and return a dictionary with all the key-value pairs for header.
"""


def parser(data):
    #   print(data)
    part = data.strip().split("\r\n")  # Getting each line of the header.
    headerEle = {}  # this store the return header dictionary
    for p in part:
        if ';' in p:
            lines = p.strip().split(';')
            line1 = lines[0].strip().split(':')
            key = line1[0]
            value = line1[1].strip()
            headerEle[key] = value
            line2 = lines[1].strip().split('=')
            boundary = line2[0]
            if len(line2) >= 2:
                value = line2[1].strip("\"")
                headerEle[boundary] = value
        else:
            line = p.strip().split(':', 1)
            key = line[0]
            key = key.strip("\"")
            if len(line) >= 2:
                value = line[1].strip()
                headerEle[key] = value
    return headerEle


def parserBody_header(header):
    res = {}
    lines = header.strip().split('\r\n')
    for i in range(len(lines)):
        if i == 0:
            l0 = lines[i].split(';')
            for p in l0:
                if ':' in p:
                    key = p.split(':')[0]
                    key = key.strip()
                    value = p.split(':')[1]
                    value = value.strip()
                    res[key] = value
                if '=' in p:
                    key = p.split('=')[0]
                    key = key.strip()
                    value = p.split('=')[1]
                    value = value.strip("\"")
                    res[key] = value
        elif i == 1:
            key = lines[i].split(':')[0]
            key = key.strip()
            value = lines[i].split(':')[1]
            value = value.strip("\"").strip()
            res[key] = value

    return res


def parseBody(boundary, encode_data, randStr):  # type 1 : processing image. type 0 : process text
    status = 200
    finalDic = {}
    encode = boundary.encode()
    split_boundary = encode_data.strip().split(encode)
    rn = '\r\n\r\n'.encode()

    r = '\r\n'.encode()
    for i in range(1, len(split_boundary) - 1):
        lines = split_boundary[i].strip(r).split(rn)
        for j in range(0, len(lines), 2):
            header = lines[j].strip(r)  # lstrip
            if j+1 > len(lines)-1:
                message = 'missing'.encode()
                data = message
            else:
                data = lines[j + 1].strip(r)  # r strip
            header = header.decode().strip()
            finalEle = parserBody_header(header)
            key = finalEle['name']
            check = True
            remove = '\r\n'.encode()
            data = data.strip(remove)
            value = data
            if key == 'upload':
                if not finalEle['filename'].endswith('.jpg'):
                    check = False
                    status = 404
            elif key == 'xsrf_token':
                if not value.decode() == randStr:
                    check = False
                    status = 403
            if check:
                finalDic[key] = value
    return finalDic, status


# This function will replace the HTML tags '<' , '>' '&' to &lt, &gt and &amp
def checkForAttack(userInput):
    for c in userInput:
        if c == '<':
            userInput = userInput.replace(c, '&lt')
            # print("replaced")
        elif c == '>':
            userInput = userInput.replace(c, '&gt')
            # print("replaced")
        elif c == '&':
            userInput = userInput.replace(c, '&amp')

    return userInput


def editHTML(response, randStr):
    requestFile = "index.html"
    message = """
    <html>
    <head>
    <title>CSE312 Sample Front End</title>
    <link rel="stylesheet" type="text/css" href="style.css" />
    </head>
    <body onload="welcomeAlert();">
    <h1>CSE312 Sample Page</h1>
    <p>
        Look at this wonderful page! If you want a better page, check out the bonus objective.
    </p>
    <p>
        Here's a flamingo:
    </p>
    <img src="image/flamingo.jpg" alt="It's a flamingo" class="my_image" />

        <p> This is form 1: For Objective 1 and 2 </p>
        <form action="/comment" id="comment-form" method="post" enctype="multipart/form-data">
        <label for="text-form-name">Name: </label>"""
    message += '\n<input value="' + randStr + '" name="xsrf_token" hidden>'
    message += """\n
        <input id="text-form-name" type="text" name="name"><br/>
        <label for="form-comment">Comment: </label>
        <input id="form-comment" type="text" name="comment">
        <input type="submit" value="Submit">
        </form>
        <p> This is form 2: for file upload.</p>
        <form action="/image-upload" id="image-form" method="post" enctype="multipart/form-data">
        <label for="form-file">Image: </label>
        <input id="form-file" type="file" name="upload">"""
    message += '\n<input value="' + randStr + '" name="xsrf_token" hidden>'
    message += """\n
        <br/>
        <label for="image-form-name">Caption: </label>
        <input id="image-form-name" type="text" name="caption">
        <input type="submit" value="Submit">
        </form>
        <h3> The following is the user input: </h3>
    """
    for li in response:
        message += "<p>" + li + "</p>"

    message += """
    <script src="functions.js"></script>
    </body>
    </html>"""
    content = open(requestFile, "w")
    content.write(message)
    content.close()
    return build_301_response("/" + requestFile)


def parse_header(head):
    header_dict = parser(head.decode())
    return header_dict


counter = 1
respondList = []


# This is for Objective 1 and Objective 3 HW3
def writeFile(path, message):
    requestFile = path[1:] + '.html'
    message = '<p>' + message + '</p>'
    f = open(requestFile, "w")
    f.write(message)
    f.close()


letter = string.ascii_letters  # Generate a random character.
randomStr = ''.join(random.choice(letter) for i in range(20))  # generate a random string


class MYTCPHandler(socketserver.BaseRequestHandler):

    def handle(self):
        received_data = self.request.recv(2048).strip()  # get the header ,first 2048 bytes of info
        editHTML(respondList, randomStr)  # add the XSRF to our html template.
        rn = '\r\n'.encode()
        request_line = received_data.strip(rn)  # This will get only the request line.
        request_line = request_line.decode()  # convert it from byte array to string.
        parts = request_line.split()
        request_type = parts[0]  # THIS is the type : GET /POST
        request_path: str = parts[1]  # This is the path.
        if request_type == 'GET':
            if request_path.endswith('.jpg') or request_path.endswith('.txt') \
                    or request_path.endswith('.ico'):
                header, content = decode_content_byte(request_path)
                self.request.sendall(header.encode() + content)
            else:
                header, content = decode_content(request_path)
                self.request.sendall(header.encode() + content.encode())

        elif request_type == 'POST':
            if request_path == '/comment':
                rn = "\r\n\r\n".encode()  # 1. Separate header and Body by \r\n\r\n
                parts = received_data.split(rn, 1)
                header = parts[0]
                body = parts[1]
                header_elem = parse_header(header)  # 2. Parse the header.  part[0]
                boundary = '--' + header_elem['boundary']  # 3. split by boundary ....
                finalDic, status = parseBody(boundary, body, randomStr)
                finalDic['name'] = finalDic['name'].decode()  # since it is text data, we need to convert to string.
                finalDic['comment'] = finalDic['comment'].decode()
                for key in finalDic:
                    finalDic[key] = checkForAttack(finalDic[key])
                if status == 404:
                    message = "Invalid file upload. Only jpg file is accepted. "
                    header404, content404 = build_404_response('text/plain; charset=UTF-8', message)
                    self.request.sendall(header404.encode() + content404.encode())
                elif status == 403:
                    message = "Invalid token.Your submission was rejected. "
                    header403, content403 = buildResponseFromByte("403 Forbidden", 'text/plain; charset=UTF-8', message)
                    self.request.sendall(header403.encode() + content403.encode())
                else:
                    message = "Thank you " + finalDic['name'] + " for your comment of " + finalDic['comment'] + "\n"
                    writeFile(request_path, message)
                    respondList.append(message)
                    response = editHTML(respondList, randomStr)
                    self.request.sendall(response.encode())

            elif request_path == '/image-upload':
                header_dict = parse_header(received_data)
                content_length = int(header_dict['Content-Length'])
                boundary = '--' + header_dict['boundary']
                read = 0
                data = b''
                while read < content_length:
                    received_data = self.request.recv(2048)
                    data += received_data
                    read += 2048
                finalDic, status = parseBody(boundary, data, randomStr)
                finalDic['caption'] = finalDic['caption'].decode()
                finalDic['caption'] = checkForAttack(finalDic['caption'])
                global counter  # This is use for user img naming conversion.
                if 'upload' in finalDic and status == 200:
                    img = './userPic/img' + str(counter) + '.jpg'
                    f = open(img, 'wb')
                    f.write(finalDic['upload'])
                    f.close()
                    message = '<img src =" ' + img + '"alt="User images" class="my_image">\n caption: ' \
                              + finalDic['caption']
                    respondList.append(message)
                    writeFile(request_path, message)
                    counter += 1
                    writeFile(request_path, message)
                    response = editHTML(respondList, randomStr)
                    self.request.sendall(response.encode())
                else:  # there is no "upload" key in dict ,which means that the user submitted a non-jpg file.
                    if status == 404:
                        message = "Invalid file upload. Only jpg file is accepted. "
                        header404, content404 = build_404_response('text/plain; charset=UTF-8', message)
                        self.request.sendall(header404.encode() + content404.encode())
                    elif status == 403:
                        message = "Invalid token.Your submission was rejected. "
                        header403, content403 = buildResponseFromByte("403 Forbidden", 'text/plain; charset=UTF-8',
                                                                      message)
                        self.request.sendall(header403.encode() + content403.encode())


if __name__ == "__main__":
    host = "0.0.0.0"
    # host = "localhost"
    port = 8000

    server = socketserver.ThreadingTCPServer((host, port), MYTCPHandler)
    server.serve_forever()
