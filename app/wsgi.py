from urlparse import parse_qs
import math
import logging

logging.basicConfig(level=logging.DEBUG)
__author__ = 'josh'
import mapnik
import StringIO
from PIL import Image
try:
    import pylibmc
    cache = pylibmc.Client(['memcached'], binary=True, 
        behaviors={"tcp_nodelay": True,
        "ketama": True})
except ImportError, e:
    logging.warning( "No memcache! {}".format(e.msg))
    cache = False


wms_keys = ('SRS','BBOX','SERVICE','LAYERS','STYLES','FORMAT','VERSION','REQUEST','WIDTH','HEIGHT')
wms_keys_lower = [k.lower() for k in wms_keys]
SRS = '+init=epsg:3857'
# from globalmaptiles import GlobalMercator

def DEFAULT_MAP_SETTINGS():
	return {
		'dbname': 'gis',
		'table': 'geo_adminarea',
		'host':' gis',
		'password':None,
		'user':'josh',
		'srs':'+init=epsg:3857'
	}



class Request(object):

    GET = {}

    def __init__(self,
        service = 'WMS',
        request = 'GetMap',
        version = '1.1.1',
        layers = '',
        format='image/jpeg',
        transparent='false',
        width=256,
        height=256,
        srs='EPSG:3857',
        bbox='13808586.9638051,-1062939.16132777,14175659.6553706,-907727.899370726'):

        self.GET = {}
        self.GET['service'] = service
        self.GET['request'] = request
        self.GET['version'] = version
        self.GET['layers'] = layers
        self.GET['format'] = format
        self.GET['transparent'] = transparent
        self.GET['width'] = width
        self.GET['height'] = height
        self.GET['srs'] = srs
        self.GET['bbox'] = bbox


class TileRequest(Request):

    def __init__(self, x=108,y=67,z=7):
        super(TileRequest, self).__init__()
        self.GET['bbox']= tile_to_box(x,y,z)


def tile_to_box(x,y,z):
    
    def tile_bounds(tx, ty, zoom):
        "Returns bounds of the given tile"
        res = 180 / 256.0 / 2**zoom
        return (
            tx*256*res - 180,
            ty*256*res - 90,
            (tx+1)*256*res - 180,
            (ty+1)*256*res - 90
        )
    
    bounds= [i for i in tile_bounds(x,y,z)]
    bounds[1] *= -1
    bounds[3] *= -1
    return ','.join([str(i) for i in bounds])


def application(env, start_response):
    qs = env['QUERY_STRING']

    d = parse_qs(qs)
    if qs == '':
        qs = 'default'
    logging.info('Query is {}'.format(qs))
    if 'x' in d and 'y' in d and 'z' in d:
        request = TileRequest()

    else:
        request = Request()

    for key, value in d.items():
        if key in wms_keys or key in wms_keys_lower:
            request.GET[key.lower()] = value[0]
        if key == 'pcode':
            request.GET['pcode'] = value[0]

    if cache:
        try:
            image = cache.get(qs)
            logging.info('Cache retrieved for map {}'.format(qs))
        except:
            raise
    
    if not image:
        image = wms(request).getvalue()
        if cache:
            try:
                cache.set(qs,image)
                logging.info('Cache set for map {}'.format(qs))
                
            except:
                raise
        
    start_response('200 OK', [('Content-Type','image/jpeg'), ('Access-Control-Allow-Origin', '*')])
    return [image]


class WGS84Tile():

    def __init__(self, xyz=(0, 0, 0)):
        self.x, self.y, self.level = xyz
        # Unprojected coordinates

    @property
    def world_tiles(self):
        """Determine how many tiles it takes to show the entire world @ this zoom level
        """
        return math.pow(2, self.level)

    def world_file(self):
        """Return contents of the World File appropriate for this tile"""

        # Google Maps ranges longitude from -180 to +180 and lat from -85.05112878 to 85.05112878
        # Get lat/lon of the tile

        # Convert lat/long to Google coordinate system
        world_max = 20037508
        res_tile = world_max*2 /self.world_tiles
        res_px = res_tile/256

        lon = -(world_max - res_tile * int(self.x))
        lat = world_max - res_tile * int(self.y)
        return """
{}
0.0
0.0
-{}
{}
{}
""".format(res_px, res_px, lon, lat)

def wms(request, return_format='raw'):



    map_settings = DEFAULT_MAP_SETTINGS()
    map_settings.update({'table': 'geo_adminarea'})
    world_settings = DEFAULT_MAP_SETTINGS()
    world_settings.update({'table': 'geo_world'})
    base_settings = DEFAULT_MAP_SETTINGS()
    base_settings.update({'table': 'geo_timor'})

    params = {
        'service':'WMS',
        'request':'GetMap',
        'version':'1.1.1',
        'layers': '',
        'format':'image/jpeg',
        'transparent':'false',
        'width':256,
        'height':256,
        'srs':'EPSG:3857',
        'bbox':'13808586.9638051,-1062939.16132777,14175659.6553706,-907727.899370726'
    }
    case_insensitive_get = {}
    for i, j in request.GET.items():
        i = i.lower()

        if i in params.keys() and params[i] != j:
            logging.info( '{}: {}'.format(i,j) )
            params[i] = j
        if i in ['width','height']:
            params[i] = int(j)


    m = mapnik.Map(params['width'], params['height'], srs=SRS)
    im = mapnik.Image(params['width'], params['height'])
    m.background = mapnik.Color('#C4DFFF')
    layer_s = mapnik.Style() # style object to hold rules
    layer_r = mapnik.Rule()

    if request.GET.get('pcode'):
        pcodes = request.GET.get('pcode').split(',')
        if len(pcodes) >= 1:
            expression = ' or '.join(["[pcode] = %s"%p for p in pcodes])
            layer_r.filter = mapnik.Expression(expression)

            layer_polygon_symbolizer = mapnik.PolygonSymbolizer()
            layer_polygon_symbolizer.fill = mapnik.Color('#008000')

            layer_line_symbolizer = mapnik.LineSymbolizer()
            layer_line_symbolizer.stroke = mapnik.Color('#074507')
            layer_line_symbolizer.stroke_width = 0.1

            layer_r.symbols.append(layer_polygon_symbolizer)
            layer_r.symbols.append(layer_line_symbolizer)

            layer_s.rules.append(layer_r)

            m.append_style('My Style',layer_s) # Styles are given names only as they are applied to the map
    layer_ds = mapnik.PostGIS(**map_settings)

    layer = mapnik.Layer('places')
    layer.srs=SRS
    layer.datasource = layer_ds
    layer.styles.append('My Style')

    base_s = mapnik.Style() # style object to hold rules
     # style object to hold rules
    base_r = mapnik.Rule()

    base_polygon_symbolizer = mapnik.PolygonSymbolizer()
    base_polygon_symbolizer.fill = mapnik.Color('#F2EFF9')
    base_line_symbolizer = mapnik.LineSymbolizer()
    base_line_symbolizer.stroke = mapnik.Color('#94BEC4')
    base_line_symbolizer.width = 0.1

    base_r.symbols.append(base_polygon_symbolizer)
    base_r.symbols.append(base_line_symbolizer)
    base_s.rules.append(base_r)
    m.append_style('Base Style',base_s) # Styles are given names only as they are applied to the map
    base_ds = mapnik.PostGIS(**base_settings)


    base = mapnik.Layer('places')
    base.srs=SRS
    base.datasource = base_ds
    base.styles.append('Base Style')

    world_s = mapnik.Style()
    world_r = mapnik.Rule()
    world_polygon_symbolizer = mapnik.PolygonSymbolizer()
    world_polygon_symbolizer.fill = mapnik.Color('#FBFFE3')
    world_line_symbolizer = mapnik.LineSymbolizer()
    world_line_symbolizer.stroke = mapnik.Color('#74B3FF')
    world_line_symbolizer.width = 0.3

    world_r.symbols.append(world_polygon_symbolizer)
    world_r.symbols.append(world_line_symbolizer)
    world_s.rules.append(world_r)
    m.append_style('world',world_s)

    world_ds = mapnik.PostGIS(**world_settings)
    world = mapnik.Layer('world')
    world.srs=SRS
    world.datasource = world_ds
    world.styles.append('world')

    
    m.layers.append(world)
    m.layers.append(base)
    m.layers.append(layer)
    

    m.zoom_to_box(mapnik.Box2d(*([float(i) for i in params['bbox'].split(',')])))
    mapnik.render(m, im)
    pil_image = Image.frombytes('RGBA', [params['width'], params['height']], im.tostring())
    output = StringIO.StringIO()
    pil_image.save(output, format='jpeg')

    if return_format == 'image':
        return pil_image
    return output

if __name__ == '__main__':
    # im = wms(Request(), return_format='image')

    im = wms(TileRequest(x=108,y=67,z=7), return_format='image')
    im.save('./test.png')
