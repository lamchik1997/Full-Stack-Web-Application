import socketserver


def decode_content(path):
    version = 'HTTP/1.1 '
    if path == '/hello':
        content = 'Hello World!'
        status = "200 OK"
        content_type = 'text/plain'
        content_length = str(len(content))
        response = version + status + "\r\nContent-Type: " + content_type + "\r\nContent-Length: " + content_length + \
                   "\r\n\r\n" + content

    elif path == '/hi':
        status = "301 Moved Permanently"
        new_path = '/hello'
        response = version + status + "\r\nLocation: " + new_path
    else:
        content = "The content was not found"
        status = '404 Not Found'
        content_type = 'text/plain'
        content_length = str(len(content))
        response = version + status + "\r\nContent-Type: " + content_type + "\r\nContent-Length: " + content_length + \
                   "\r\n\r\n" + content
    return response


class MYTCPHandler(socketserver.BaseRequestHandler):

    def handle(self):
        received_data = self.request.recv(1024).strip()
        # print(self.client_address[0] + " is sending data:")
        decode_data = received_data.decode()  # convert it from byte array to string.
        # print(decode_data)
        # print("\n\n")

        request_line = decode_data.strip("\r\n")
        # print("----------This is the request line --------", request_line)
        request_type = decode_data.split()[0]
        if request_type == 'GET':
            path = decode_data.split()[1]
            # print("------------path--------------", path)
            response = decode_content(path)
            self.request.sendall(response.encode())
        else:
            print("This is not a get request.")
            content = "This is not a get request!"
            self.request.sendall(
                "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: " + len(content) + "\r\n\r\n" + content)


if __name__ == "__main__":
    host = "0.0.0.0"
    port = 8000

    server = socketserver.ThreadingTCPServer((host, port), MYTCPHandler)
    server.serve_forever()
