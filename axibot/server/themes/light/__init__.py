from aiohttp_themes.theme import Theme
from aiohttp_themes.asset import SASSAsset, RequireJSAsset


class LightTheme(Theme):
    key = 'light'
    assets = {
        'main.css': SASSAsset('css/main.scss'),
        'main.js': RequireJSAsset(
            'js/main.js',
            requirejs_config_path='js/require_config.js'),
    }
