from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .tasks import perform_cognitive_analysis_task, analysis_cache # Import the task and mock cache

class CognitiveRadarAPI(APIView):
    """
    Handles requests for AI-powered Cognitive Risk Analysis.
    Triggers an asynchronous GNN/LLM analysis task.
    """
    def post(self, request, *args, **kwargs):
        analysis_type = request.data.get('analysis_type')
        # Frontend code sends the analysis type: [cite: oladimeji-kazeem/grc/grc-2073184ca16c347acfc0a5199cff417b8a37885b/src/pages/CognitiveRiskRadar.tsx]
        if analysis_type not in ["comprehensive", "patterns", "emerging"]:
            return Response({"error": "Invalid analysis type"}, status=status.HTTP_400_BAD_REQUEST)
        
        # In a real app, you would pass the current user's ID/context
        
        # 1. Trigger the asynchronous GNN/LLM task
        task = perform_cognitive_analysis_task.delay(analysis_type)
        
        # 2. Store the task ID so the frontend can poll for the result
        # We use a unique ID for the analysis request.
        request_id = f"analysis_{task.id}" 
        analysis_cache[request_id] = {"status": "pending", "task_id": task.id}
        
        return Response({
            "status": "Analysis started", 
            "request_id": request_id,
            "task_id": task.id
        }, status=status.HTTP_202_ACCEPTED)

    def get(self, request, *args, **kwargs):
        """Polls for the result of a long-running analysis task."""
        request_id = request.query_params.get('request_id')
        
        if not request_id or request_id not in analysis_cache:
            return Response({"error": "Analysis not found or expired"}, status=status.HTTP_404_NOT_FOUND)
        
        task_info = analysis_cache[request_id]
        
        if task_info.get("status") == "completed":
            # The result is stored in the task's cache.
            # In a real system, you might fetch the result from a distributed cache (Redis/Memcached)
            # For this mock, we assume the task returns the data directly on completion.
            return Response(task_info, status=status.HTTP_200_OK)
        
        return Response(task_info, status=status.HTTP_202_ACCEPTED) # Still pending
