class FlaskRequest():

    def __init__(self, request):
        self.args = request.args
        self.data = request.data
        self.method = request.method
        self.headers = request.headers
        self.cookies = request.cookies
        self.content_type = request.content_type
        self.files = request.files
        self.environ = request.environ
        self.remote_addr = request.remote_addr
        self.url = request.url
        self.base_url = request.base_url
        self.url_root = request.url_root
        self.host_url = request.host_url
        self.host = request.host
        self.script_root = request.script_root
        self.path = request.path
        self.full_path = request.full_path

        if self.content_type == 'application/json':
            self.json = request.json
        else:
            self.json = {}

        if 'multipart/form-data' in self.content_type or 'application/x-www-form-urlencoded' in self.content_type:
            self.form = request.form
        else:
            self.form = {}
