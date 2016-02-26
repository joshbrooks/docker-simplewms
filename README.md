# docker-simplewms

This is a very simple implementation of a WSGI server to return a WMS (Web Map Service) image.

DOcker container listens on port 80 for a request. Standard WMS parameters are supported:

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

Not all are used in this example. 
In addition a GET string 'pcode' can be used to specify an administration area to highlight eg

    ?pcode=6
    ?pcode=6,101,5
    
Default settings for Mapnik are as follows:
    'dbname': 'gis',
	  'table': 'geo_adminarea',
		'host':' gis',
		'password':None,
		'user':'josh',
		'srs':'+init=epsg:3857'
		
Table names are geo\_adminarea, geo\_world, geo\_timor.

Usage: 

    docker run --rm -p 8085:80 --li leaflet_gis_1:gis digitaltl/simplewms
    
To provide images on port 8085 of docker host, and PostGIS database connection to leaflet\_gis\_1.
