from rest_framework.views import APIView
from rest_framework.response import Response
from accounts.permissions import IsAuthenticated
import requests
from django.http import JsonResponse
from django.conf import settings

geo_terms = [
    '"plate tectonics" OR "lithosphere" OR "subduction"',
    '"sedimentary" OR "stratigraphy" OR "sandstone" OR "shale"',
    '"igneous" OR "volcanology" OR "magma" OR "basalt"',
    '"metamorphic" OR "petrology" OR "gneiss" OR "schist"',
    '"geomorphology" OR "erosion" OR "glaciation"',
    '"mineralogy" OR "geochemistry" OR "hydrothermal"'
]

class FeedListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.GET.get('query', '')

        url = "https://serpapi.com/search"
        params = {
            "engine": "google_scholar",
            "q": '''
                "geology" OR "geoscience" OR "earth science" OR "lithosphere" OR "earth crust" OR 
                "geophysics" OR "geochemistry" OR "geomorphology" OR "mineralogy" OR "petrology" OR 
                "sedimentology" OR "stratigraphy" OR "structural geology" OR "tectonics" OR "plate tectonics" OR
                "paleontology" OR "seismology" OR "volcanology" OR "geochronology" OR "fossil" OR
                "igneous rock" OR "sedimentary rock" OR "metamorphic rock" OR "rock formation" OR 
                "granite" OR "basalt" OR "limestone" OR "sandstone" OR "shale" OR "gneiss" OR "schist" OR "quartz" OR
                "subduction zone" OR "fault line" OR "rift valley" OR "magma chamber" OR "orogeny" OR
                "erosion" OR "weathering" OR "deposition" OR "glaciation" OR "sediment transport" OR
                "radiometric dating" OR "carbon dating" OR "uranium lead dating" OR "isotope analysis"
                -medicine -biology -psychology -economics -machine -ai -computer -education -social -law -business
            ''',
            "api_key": settings.SERPAPI_KEY
        }

        try:
            response = requests.get(url, params=params)
            return JsonResponse(response.json(), safe=False)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
