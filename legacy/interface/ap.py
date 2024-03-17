from quart import Quart, send_from_directory

class AdminProcessor:

    def __init__(self, app: Quart, base_dir: str):
        self.app = app
        self.base_dir = base_dir

    def setup_routes(self):

        @self.app.route('/index.html', methods=['GET'])
        async def index_html():
            return await send_from_directory(self.base_dir, 'index.html')

        # @self.app.route('/style.css', methods=['GET'])
        # async def style_css():
        #     return await send_from_directory(self.base_dir, 'style.css')
