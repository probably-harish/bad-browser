import socket
import curses
import threading
from bs4 import BeautifulSoup
from art import text2art

SERVER_PORT = 8080
BUFFER_SIZE = 4096

class SimpleTerminalBrowser:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.header_window = None
        self.main_window = None
        self.tls_window = None
        self.status_line = None
        self.init_ui()
        self.host = ''
        self.client_socket = None

    def init_ui(self):
        max_height, max_width = self.stdscr.getmaxyx()
        self.header_window = curses.newwin(3, max_width, 0, 0)
        self.main_window = curses.newwin(max_height - 7, max_width, 3, 0)
        self.tls_window = curses.newwin(3, max_width, max_height - 4, 0)
        self.status_line = curses.newwin(1, max_width, max_height - 1, 0)

        self.header_window.box()
        self.tls_window.box()
        self.main_window.scrollok(True)
        self.stdscr.refresh()

        self.tls_window.addstr(1, 2, "TLS Status")
        self.header_window.addstr(1, 2, "Enter the URL: ")
        self.header_window.refresh()
        self.tls_window.refresh()

    def connect(self, host):
        self.host = host
        if not self.client_socket:
            try:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.connect((self.host, SERVER_PORT))
                # Handle successful connection
            except Exception as e:
                self.status_line.addstr(0, 0, f"Connection failed: {e}", curses.A_BOLD)
                self.status_line.refresh()
                return None


    def send_http_request(self, method, path, data=''):
        if method in ['GET', 'DELETE']:
            request = f"{method} {path} HTTP/1.1\r\nHost: {self.host}:{SERVER_PORT}\r\n\r\n"
        else:
            request = f"{method} {path} HTTP/1.1\r\nHost: {self.host}:{SERVER_PORT}\r\nContent-Length: {len(data)}\r\n\r\n{data}"

        # Connect to the server
        self.connect(self.host)

        # Send request to the server
        if self.client_socket:
            try:
                self.client_socket.sendall(request.encode())
            except BrokenPipeError as e:
                self.status_line.addstr(0, 0, f"Error: {e}", curses.A_BOLD)
                self.status_line.refresh()

    def receive_http_response(self):
        if self.client_socket:
            try:
                response = self.client_socket.recv(BUFFER_SIZE).decode()
                if response.startswith('<!DOCTYPE html>') or response.startswith('<html>'):
                    self.render_html_to_window(response)
                else:
                    self.main_window.addstr(response)
            except socket.error as e:
                self.main_window.addstr(f"Failed to receive data: {e}")
            finally:
                self.main_window.refresh()
        else:
            self.main_window.addstr("No active connection.")
            self.main_window.refresh()

    def run(self):
        try:
            while True:
                self.header_window.addstr(1, 2, "Enter the URL: ")
                self.header_window.clrtoeol()
                self.header_window.refresh()
                curses.echo()
                url = self.header_window.getstr(1, 16).decode().strip()
                curses.noecho()

                if url == 'exit':
                    return

                method = 'GET'  # Simplified: Always use GET for this example
                path = f"/{url}" if not url.startswith('/') else url

                self.main_window.clear()
                self.send_http_request(method, path)
                self.receive_http_response()

                self.status_line.addstr(0, 0, "Press any key to continue or type 'q' to quit...")
                self.status_line.refresh()
                key = self.stdscr.getch()
                if key == ord('q') or key == ord('Q'):
                    break
                self.status_line.clear()
                self.status_line.refresh()

        except KeyboardInterrupt:
            pass

        finally:
            if self.client_socket:
                #self.client_socket.close()
                #self.client_socket = None
                pass


    def render_html_to_window(self, html_content):
        soup = BeautifulSoup(html_content, 'html5lib')
        self.main_window.clear()

        # Function to recursively render HTML elements
        def render_element(element, indent=0):
            if element.name in ['style', 'script']:
                # Remove style and script elements
                return
            elif element.name == 'br':
                self.main_window.addstr('\n')
            elif hasattr(element, 'get_text'):
                text = element.get_text(separator='\n', strip=True)
                if text:
                    self.main_window.addstr('\n' + ' ' * indent + text)

            for child in element.children:
                render_element(child, indent + 2)

        # Start rendering from the top-level HTML element
        for element in soup.descendants:
            render_element(element)

        self.main_window.refresh()



    def receive_http_response(self):
        try:
            response = self.client_socket.recv(BUFFER_SIZE).decode()
            if response.startswith('<!DOCTYPE html>') or response.startswith('<html>'):
                self.render_html_to_window(response)
            else:
                # Handle non-HTML (plain text) content
                self.main_window.addstr(response)
        except socket.error as e:
            self.main_window.addstr(f"Failed to receive data: {e}")
        finally:
            self.main_window.refresh()

    def display_bad_browser_text(self):
        self.main_window.clear()
        bad_browser_text = text2art("Bad \nBrowser")
        self.main_window.addstr(bad_browser_text)
        self.main_window.refresh()

def main(stdscr):
    curses.curs_set(1)  # Show the cursor for input
    stdscr.clear()
    stdscr.addstr(0, 0, "Enter the IP address of the server (e.g., 127.0.0.1): ")
    stdscr.refresh()
    curses.echo()
    host = stdscr.getstr().decode().strip()
    curses.noecho()
    curses.curs_set(0)
    stdscr.clear()
    stdscr.refresh()

    browser = SimpleTerminalBrowser(stdscr)

    # Connect to the server immediately after receiving the IP address
    browser.connect(host)

    browser.display_bad_browser_text()  # Display "bad browser" initially
    browser.run()
    curses.endwin()

if __name__ == "__main__":
    curses.wrapper(main)

