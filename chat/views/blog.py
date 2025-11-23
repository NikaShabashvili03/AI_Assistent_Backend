from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from ..serializers import BlogSerializer
from accounts.permissions import IsAuthenticated
from ..models import Blog

DEFAULT_LIMIT = 10
MAX_LIMIT = 50 

class BlogFeedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            limit = int(request.query_params.get('limit', DEFAULT_LIMIT))
            offset = int(request.query_params.get('offset', 0))
            search = request.query_params.get('search', '').strip()
            
            if limit > MAX_LIMIT:
                limit = MAX_LIMIT
                
            start = offset
            end = offset + limit
            
            if search:
                queryset = Blog.objects.filter(
                    Q(blog_title__icontains=search) | Q(summary__icontains=search)
                ).order_by('-created_at')
            else:
                queryset = Blog.objects.all().order_by('-created_at')
                
            blogs = queryset[start:end + 1]
            
            has_more = len(blogs) > limit
            
            data_to_serialize = blogs[:limit]
            
            serializer = BlogSerializer(data_to_serialize, many=True)
            
            return Response({
                'blogs': serializer.data,
                'next_offset': end if has_more else None,
                'has_more': has_more,
                'count': len(data_to_serialize),
                'total_results_fetched': end - (limit + 1) + len(blogs)
            }, status=status.HTTP_200_OK)

        except ValueError:
            return Response({'detail': 'Invalid limit or offset parameter.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': f'An internal error occurred: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# geo_terms = [
#     '"plate tectonics" OR "lithosphere" OR "subduction"',
#     '"sedimentary" OR "stratigraphy" OR "sandstone" OR "shale"',
#     '"igneous" OR "volcanology" OR "magma" OR "basalt"',
#     '"metamorphic" OR "petrology" OR "gneiss" OR "schist"',
#     '"geomorphology" OR "erosion" OR "glaciation"',
#     '"mineralogy" OR "geochemistry" OR "hydrothermal"'
# ]

# class BlogFeedView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         url = "https://serpapi.com/search"
#         params = {
#             "engine": "google_scholar",
#             "q": '''
#                 "geology" OR "geoscience" OR "earth science" OR "lithosphere" OR "earth crust" OR 
#                 "geophysics" OR "geochemistry" OR "geomorphology" OR "mineralogy" OR "petrology" OR 
#                 "sedimentology" OR "stratigraphy" OR "structural geology" OR "tectonics" OR "plate tectonics" OR
#                 "paleontology" OR "seismology" OR "volcanology" OR "geochronology" OR "fossil" OR
#                 "igneous rock" OR "sedimentary rock" OR "metamorphic rock" OR "rock formation" OR 
#                 "granite" OR "basalt" OR "limestone" OR "sandstone" OR "shale" OR "gneiss" OR "schist" OR "quartz" OR
#                 "subduction zone" OR "fault line" OR "rift valley" OR "magma chamber" OR "orogeny" OR
#                 "erosion" OR "weathering" OR "deposition" OR "glaciation" OR "sediment transport" OR
#                 "radiometric dating" OR "carbon dating" OR "uranium lead dating" OR "isotope analysis"
#                 -medicine -biology -psychology -economics -machine -ai -computer -education -social -law -business
#             ''',
#             "api_key": settings.SERPAPI_KEY
#         }

#         try:
#             response = requests.get(url, params=params)
#             return JsonResponse(response.json(), safe=False)
#         except Exception as e:
#             return JsonResponse({"error": str(e)}, status=500)
